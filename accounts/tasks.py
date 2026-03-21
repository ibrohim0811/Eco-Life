import asyncio
import psycopg2
from pathlib import Path
from celery import Celery, shared_task
from aiogram import Bot
import os
from dotenv import load_dotenv
from django.utils import timezone
from datetime import timedelta
from accounts.models import Subscription

BASE_DIR = Path(__file__).resolve().parent.parent 
env_path = BASE_DIR / '.env'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
print(f"redis debug {REDIS_URL}")

load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv('BOT_TOKEN').strip()
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


app = Celery('ecosys', broker=REDIS_URL)

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
    
    
@shared_task
def send_reminder_sbs():
    now = timezone.now()
    tomorrow = timezone.now() + timedelta(days=1)
    
    start = tomorrow - timedelta(hours=1)
    end = tomorrow + timedelta(hours=1)
    
    expiring_soon = Subscription.objects.filter(
        expires_at__range=(start, end),
        expires_at__gt=now,
        is_lifetime=False
    ).exclude(plan="Free")
    
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    async def notify_user():
        for sub in expiring_soon:
            try:
                msg = (
                    f"⚠️ <b>Hurmatli {sub.user.username}!</b>\n\n"
                    f"Sizning <b>{sub.plan}</b> tarifingiz ertaga tugaydi.\n"
                    f"Xizmatlardan uzluksiz foydalanish uchun hisobingizni to'ldirib qo'ying."
                )
                
                await bot.send_message(sub.user.tg_id, msg, parse_mode="HTML")
                
            except Exception as e:
                print(f"Xabar yuborishda xato (User: {sub.user.tg_id}): {e}")
        await bot.session.close()
        
    asyncio.run(notify_user())
    

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_task(subject, message, recipient_list):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        fail_silently=False,
    )
    return "Email muvaffaqiyatli yuborildi!"