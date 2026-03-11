import asyncio
import logging
import os
import datetime
import sys
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from fpdf import FPDF # fpdf2 ishlatsangiz yaxshiroq

from aiogram import Router, Bot, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile

# admin.py ichida
from accounts.tasks import run_broadcast_task

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("SUPER_ADMIN", 0))]

DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

terminal_logs = []

class TerminalLogger:
    def __init__(self, original_stream):
        self.stream = original_stream

    def write(self, message):
        self.stream.write(message)
        if message.strip():
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            # Loglarni limitda ushlab turamiz (oxirgi 500 ta)
            if len(terminal_logs) > 500: terminal_logs.pop(0)
            terminal_logs.append(f"[{timestamp}] {message.strip()}")

    def flush(self):
        self.stream.flush()

sys.stdout = TerminalLogger(sys.stdout)
sys.stderr = TerminalLogger(sys.stderr)

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s:%(message)s")

# --- DATABASE ---
def get_all_tg_ids():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT tg_id FROM accounts_users IS NOT NULL")
        ids = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return ids
    except Exception as e:
        print(f"DB Error: {e}")
        return []

# --- STATES ---
dp_admin = Router()

class AdminStates(StatesGroup):
    waiting_broadcast_type = State()
    waiting_broadcast_content = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# --- HANDLERS ---
@dp_admin.message(Command("send_message"))
async def cmd_send_message(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.clear()
    await state.set_state(AdminStates.waiting_broadcast_type)

    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Matn", callback_data="broadcast:text")
    kb.button(text="🖼 Rasm", callback_data="broadcast:photo")
    kb.button(text="🎞 Video", callback_data="broadcast:video")
    kb.button(text="🎬 GIF", callback_data="broadcast:animation") 
    kb.adjust(1)
    await message.answer("Qaysi turdagi xabar yuborasiz?", reply_markup=kb.as_markup())

@dp_admin.callback_query(AdminStates.waiting_broadcast_type, F.data.startswith("broadcast:"))
async def cb_broadcast_type(callback: types.CallbackQuery, state: FSMContext):
    kind = callback.data.split(":")[1]
    await state.update_data(broadcast_kind=kind)
    await state.set_state(AdminStates.waiting_broadcast_content)
    await callback.message.edit_text(f"{kind.capitalize()} yuboring:")

@dp_admin.message(AdminStates.waiting_broadcast_content)
async def handle_broadcast_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kind = data.get("broadcast_kind")
    
    content = None
    caption = message.caption or ""

    if kind == "text":
        if message.text: content = message.text
        else: return await message.answer("❌ Matn yuboring!")

    elif kind == "photo":
        if message.photo: content = message.photo[-1].file_id
        else: return await message.answer("❌ Rasm yuboring!")

    elif kind == "video":
        if message.video: content = message.video.file_id
        # Ba'zan foydalanuvchilar videoni ham GIF deb o'ylashadi, shuni tekshiramiz
        elif message.animation: content = message.animation.file_id 
        else: return await message.answer("❌ Video yuboring!")

    # GIF (Animation) uchun maxsus qism
    elif kind == "animation" or (message.animation and not content):
        if message.animation:
            content = message.animation.file_id
            kind = "animation" # Kindni aniqlashtirib olamiz
        else:
            return await message.answer("❌ GIF (animatsiya) yuboring!")

    if content:
        run_broadcast_task.delay(kind, content, caption)
        await state.clear()
        await message.answer("🚀 GIF/Video tarqatish navbatga qo'shildi!")

# --- PDF LOGS (UTF-8 bilan) ---
def save_terminal_to_pdf():
    if not terminal_logs: return None
    pdf = FPDF()
    pdf.add_page()
    
    # AGAR O'ZBEKCHA HARFLAR KERAK BO'LSA:
    # pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    # pdf.set_font('DejaVu', size=8)
    
    pdf.set_font("Courier", size=8) # Standart ASCII uchun
    pdf.set_fill_color(30, 30, 30)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(255, 255, 255)
    
    for line in terminal_logs:
        pdf.multi_cell(0, 5, txt=f"> {line}")
    
    os.makedirs("logs", exist_ok=True)
    path = f"logs/log_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
    pdf.output(path)
    return path

@dp_admin.message(Command("log"))
async def cmd_get_log(message: types.Message):
    if not is_admin(message.from_user.id): return
    path = save_terminal_to_pdf()
    if path:
        await message.answer_document(FSInputFile(path))
    else:
        await message.answer("Loglar bo'sh.")

print(">>> Admin Module Ready.")