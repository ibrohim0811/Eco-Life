# register.py (yoki handlers/register.py)

import sys
import os
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from aiogram_i18n.context import I18nContext
from django.contrib.auth.hashers import make_password
from django.db import transaction

from states.register import Register
from UI.inline import settings_lang
from UI.default import contact_button, main_menu # sorov — register tugmasi bo'lgan keyboard deb taxmin qilyapman
from accounts.models import Users
from validation.validate import validate_phone_number

register = Router(name="registration")


def get_user(tg_id: int):
    return Users.objects.filter(tg_id=tg_id).first()


@register.message(lambda msg, i18n: msg.text == i18n("register"))
async def cmd_register(msg: types.Message, state: FSMContext, i18n: I18nContext):
    tg_id = msg.from_user.id

    user = await sync_to_async(get_user)(tg_id)
    if user:
        await i18n.set_locale(user.language or "uz")
        await msg.answer(
            f"{i18n('already_registered')}\n{i18n('welcome_back')}",
            reply_markup=main_menu(i18n)
        )
        await state.clear()
        return

    await state.clear()

    await state.set_state(Register.set_lang)

    default_lang = msg.from_user.language_code or "uz"
    await i18n.set_locale(default_lang)

    await msg.answer(
        i18n("select_lang"),
        reply_markup=settings_lang(i18n)
    )


@register.callback_query(StateFilter(Register.set_lang), F.data.in_({"uz", "ru", "en"}))
async def process_language_selection(callback: types.CallbackQuery, state: FSMContext, i18n: I18nContext):
    """Til tanlash"""
    tg_id = callback.from_user.id

    if await sync_to_async(get_user)(tg_id):
        await callback.message.edit_text(i18n("already_registered"))
        await state.clear()
        await callback.answer()
        return

    selected_lang = callback.data   

    await i18n.set_locale(selected_lang)
    await state.update_data(user_lang=selected_lang)

    await state.set_state(Register.first_name)

    print(f"DEBUG: selected_lang = {selected_lang}, new state = {await state.get_state()}")

    try:
        await callback.message.edit_text(i18n("name"))
    except Exception as e:
        print(f"Edit text error: {e}")
        await callback.message.answer(i18n("name"))

    await callback.answer(i18n("sucsess_lang"))
    
    
@register.message(StateFilter(Register.first_name))
async def process_first_name(msg: types.Message, state: FSMContext, i18n: I18nContext):
    if any(c.isdigit() for c in msg.text):
        await msg.answer(i18n("invalid_name"))
        await msg.answer(i18n("name"))
        return

    await state.update_data(first_name=msg.text.strip())
    await state.set_state(Register.last_name)
    await msg.answer(i18n("last_name"))


@register.message(StateFilter(Register.last_name))
async def process_last_name(msg: types.Message, state: FSMContext, i18n: I18nContext):
    if any(c.isdigit() for c in msg.text):
        await msg.answer(i18n("invalid_last_name"))
        await msg.answer(i18n("last_name"))
        return

    await state.update_data(last_name=msg.text.strip())
    await state.set_state(Register.phone)
    await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))


@register.message(StateFilter(Register.phone))
async def process_phone(msg: types.Message, state: FSMContext, i18n: I18nContext):
    phone = None

    if msg.contact:
        phone = msg.contact.phone_number
    elif msg.text:
        phone = msg.text.strip()

    if phone and validate_phone_number(phone):
        await state.update_data(phone=phone)
        await state.set_state(Register.password)
        await msg.answer(i18n("password"), reply_markup=types.ReplyKeyboardRemove())
        return

    # Agar noto'g'ri bo'lsa
    await msg.answer(i18n("invalid_phone"), reply_markup=contact_button(i18n))



@register.message(Register.password)
async def password(msg: types.Message, state: FSMContext, i18n: I18nContext):
    password = msg.text
    
    if len(password) < 8:
        await msg.answer(i18n("invalid_password"))
        return
    
    await state.update_data(password=password)
    data = await state.get_data()
    
    user = await sync_to_async(Users.objects.create)(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        username=msg.from_user.username or f"user_{msg.from_user.id}",
        password=make_password(data.get("password")),
        tg_id=msg.from_user.id,
        language=data.get('user_lang')
    )
    
    await msg.answer(f"{i18n('start_text')} \n {i18n('web')} \n Username: <code>{user.username}</code> \n  {msg.from_user.first_name} \n{i18n('join')}\n https://eco-life.up.railway.app", parse_mode="HTML", reply_markup=main_menu(i18n))
    await state.clear()




# @register.message(StateFilter(Register.password))
# async def process_password_and_create_user(msg: types.Message, state: FSMContext, i18n: I18nContext):
#     password = msg.text.strip()

   
#     if len(password) < 8:
#         await msg.answer(i18n("password_too_short"))
#         return

#     data = await state.get_data()

#     try:
#         async with transaction.atomic(): 
#             user = await sync_to_async(Users.objects.create)(
#                 tg_id=msg.from_user.id,
#                 first_name=data.get("first_name"),
#                 last_name=data.get("last_name"),
#                 phone=data.get("phone"),
#                 username=msg.from_user.username or f"t_{msg.from_user.id}",
#                 password=make_password(password),
#                 language=data.get("user_lang", "uz"),
               
#             )

#         success_text = (
#             f"{i18n('registration_success')}\n\n"
#             f"{i18n('your_name')}: {user.first_name} {user.last_name or ''}\n"
#             f"{i18n('phone')}: {user.phone}\n\n"
#             f"{i18n('web')}: https://Eco-life.uz\n\n"
#             f"{i18n('login_with_phone_or_telegram')}"
#         )

#         await msg.answer(success_text, reply_markup=main_menu(i18n))
#         await state.clear()

#     except Exception as e:
#         print(f"Registration error for tg_id {msg.from_user.id}: {e}")
#         await msg.answer(i18n("error_try_again_later"))
#         await state.clear()
        
        



@register.message(
    StateFilter(
        Register.set_lang,
        Register.first_name,
        Register.last_name,
        Register.phone,
        Register.password
    )
)
async def unknown_message_in_registration(msg: types.Message, state: FSMContext, i18n: I18nContext):
    current_state = await state.get_state()

    if current_state == Register.set_lang.state:
        await msg.answer(i18n("please_select_language"), reply_markup=settings_lang(i18n))
    elif current_state == Register.first_name.state:
        await msg.answer(i18n("name"))
    elif current_state == Register.last_name.state:
        await msg.answer(i18n("last_name"))
    elif current_state == Register.phone.state:
        await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
    elif current_state == Register.password.state:
        await msg.answer(i18n("password"))
    else:
        await msg.answer(i18n("please_continue_registration"))