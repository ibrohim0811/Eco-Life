import asyncio
import psycopg2
from pathlib import Path
from celery import Celery
from aiogram import Bot
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent 
env_path = BASE_DIR / '.env'

load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv('BOT_TOKEN').strip()
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


app = Celery('ecosys', broker='redis://localhost:6379/0')

def get_all_tg_ids():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT tg_id FROM accounts_users WHERE tg_id IS NOT NULL")
        ids = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return ids
    except Exception as e:
        print(f"DB Error: {e}")
        return []


@app.task(name='run_broadcast_task')
def run_broadcast_task(kind, content, caption):
    bot = Bot(token=BOT_TOKEN)
    
    
    user_ids = get_all_tg_ids()

    async def main():
        ok, fail = 0, 0
        for uid in user_ids:
            try:
                if kind == "text":
                    await bot.send_message(uid, content)
                elif kind == "photo":
                    await bot.send_photo(uid, photo=content, caption=caption)
                elif kind == "video":
                    await bot.send_video(uid, video=content, caption=caption)
                elif kind == "animation":
                    await bot.send_animation(uid, animation=content, caption=caption)
                ok += 1
                await asyncio.sleep(0.05) 
            except Exception as e:
                print(f"Xato (User {uid}): {e}")
                fail += 1
        
        admin_id = os.getenv("SUPER_ADMIN")
        if admin_id:
            await bot.send_message(admin_id, f"✅ Tarqatish tugadi!\nOK: {ok}\nFAIL: {fail}")
        
        await bot.session.close()

    asyncio.run(main())

import requests
BASE_URL = os.getenv("SMS_URL")    
TOKEN = os.getenv("SMS_API") 
    
@app.task(name='send_sms_task')
def send_sms_task(phone: str, message: str):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/send_sms.php",
            headers=headers,
            json={"phone": phone, "message": message},
            timeout=10 
        )
        result = response.json()
        print(f"SMS yuborildi: {phone} - Status: {result.get('status')}")
        return result
    except Exception as e:
        print(f"SMS yuborishda xato: {e}")
        return {"status": "error", "message": str(e)}