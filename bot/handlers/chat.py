import re
import os
from aiogram import Router, types, F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n.context import I18nContext
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv

from UI.default import main_menu
from bot.connections import get_user_language
from asgiref.sync import sync_to_async
from states.chat import SupportState

load_dotenv()

router = Router()
ADMIN_ID = int(os.getenv("SUPER_ADMIN"))

@router.message(Command("help"))
async def help_handler(msg: types.Message, state: FSMContext, i18n: I18nContext):
    lang = await sync_to_async(get_user_language)(tg_id=msg.from_user.id)
    await i18n.set_locale(lang)
    
    await state.set_state(SupportState.on_chat)
    await msg.answer(i18n("support_started"), reply_markup=ReplyKeyboardRemove()) 
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Chatni yopish ❌", 
        callback_data=f"close_chat_{msg.from_user.id}")
    )
    
    await msg.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆘 <b>Yangi yordam so'rovi!</b>\n"
             f"👤 Kimdan: {msg.from_user.full_name}\n"
             f"🆔 ID: <code>{msg.from_user.id}</code>\n\n"
             f"<i>Javob berish uchun xabarga 'Reply' qiling.</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.message(SupportState.on_chat)
async def user_to_admin(msg: types.Message, bot: Bot):
    """User xabarini adminga yuborish (Faqat state ochiq bo'lsa ishlaydi)"""
    if msg.text == "/start":
        return 

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Chatni yopish ❌", 
        callback_data=f"close_chat_{msg.from_user.id}")
    )
    
    await bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=msg.chat.id,
        message_id=msg.message_id,
        caption=f"📩 <b>Xabar keldi (ID: <code>{msg.from_user.id}</code>)</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("close_chat_"))
async def admin_close_chat_callback(callback: types.CallbackQuery, bot: Bot, i18n: I18nContext):
    user_id = int(callback.data.split("_")[2])
    
    from main import dp 
    
    user_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    await dp.storage.set_state(key=user_key, state=None)
    await dp.storage.set_data(key=user_key, data={})
    
    lang = await sync_to_async(get_user_language)(tg_id=user_id)
    try:
        await bot.send_message(
            chat_id=user_id, 
            text=i18n.get("chat_ended", locale=lang), 
            reply_markup=main_menu(i18n)
        )
    except:
        pass 

    await callback.message.edit_text(f"{callback.message.text}\n\n✅ <b>Chat yopildi!</b>", parse_mode="HTML")
    await callback.answer("Chat yopildi!")

@router.message(F.reply_to_message, F.chat.id == ADMIN_ID)
async def admin_reply_to_user(msg: types.Message, bot: Bot, i18n: I18nContext):
    reply_text = msg.reply_to_message.text or msg.reply_to_message.caption
    if not reply_text: return
    
    match = re.search(r"ID: (\d+)", reply_text)
    
    if match:
        user_id = int(match.group(1))
        
        if msg.text and msg.text.strip() == "/close":
            from main import dp
            user_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
            await dp.storage.set_state(key=user_key, state=None)
            await bot.send_message(user_id, i18n("chat_ended"), reply_markup=main_menu(i18n))
            await msg.answer(f"✅ User {user_id} bilan chat yopildi.")
        else:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=ADMIN_ID,
                    message_id=msg.message_id
                )
                await msg.answer("✅ Xabar yuborildi.")
            except:
                await msg.answer("❌ Foydalanuvchi botni bloklagan.")
    else:
        await msg.answer("⚠️ User ID topilmadi.")