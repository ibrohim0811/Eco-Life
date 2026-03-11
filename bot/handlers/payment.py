import sys
import os
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from aiogram_i18n.context import I18nContext

from states.payment import Payment
from UI.default import payment_method
from UI.inline import payment_version

payment = Router()


@payment.message(lambda msg, i18n: msg.text == i18n("payment"))
async def payment_start(msg: types.Message, i18n: I18nContext, state: FSMContext):
    await msg.answer(i18n("att_pay"))
    await msg.answer(i18n("choose_version"), reply_markup=payment_version)
    await state.set_state(Payment.version)
    
@payment.callback_query(Payment.version, F.data.in_(["go", "pro", "ultima"]))
async def plan_select(callback: types.CallbackQuery, i18n: I18nContext, state: FSMContext):
    await callback.message.delete()
    
    version = callback.data
    await state.update_data(version=version)
    
    await callback.answer(i18n("selected"))
    await callback.message.answer(i18n("select_payment_method"), reply_markup=payment_method)
    await state.set_state(Payment.payment_method)
    
#ertaga davom ettirasan groq api keyni qoshib chekni tekshirasan groq bilan