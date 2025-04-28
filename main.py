import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@ibratmasterclass"

dp = Dispatcher()

registered_users = {}

class Registration(StatesGroup):
    name = State()
    phone = State()
    age = State()
    event = State()
    follower_check = State()

async def check_channel_membership(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    if user_id == 6470963942:
        await message.answer("Admin cannot register. Please contact support if needed.")
        return

    if user_id in registered_users:
        await message.answer("You are already registered! ✅")
        return

    await message.answer(
        f"Welcome {html.bold(message.from_user.full_name)} to Ibrat master class! You can register for our events and stay informed about upcoming opportunities. Enter your name and surname:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="Share phone number 📱", request_contact=True)
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Please share your phone number:", reply_markup=keyboard)
    await state.set_state(Registration.phone)

@dp.message(Registration.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)

    await message.answer("Please enter your age:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Age must be a number. Please enter again:")
        return

    await state.update_data(age=message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Event A"), KeyboardButton(text="Event B"), KeyboardButton(text="Event C")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Please choose an event:", reply_markup=keyboard)
    await state.set_state(Registration.event)

@dp.message(Registration.event)
async def process_event(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id

    if message.text not in ["Event A", "Event B", "Event C"]:
        await message.answer("Please choose a valid event from the buttons!")
        return

    await state.update_data(event=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="I'm a follower", callback_data="check_follower")]
        ]
    )

    await message.answer(
        "Please join our channel and click the button below to confirm you're following it. " + CHANNEL_USERNAME,
        reply_markup=keyboard
    )
    await state.set_state(Registration.follower_check)

@dp.callback_query(F.data == "check_follower")
async def handle_follower_check(callback_query, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id

    is_member = await check_channel_membership(user_id, bot)

    if is_member:
        data = await state.get_data()

        info = f"""
        <b>Registration completed! 🎉</b>

        <b>Name:</b> {html.quote(data['name'])}
        <b>Phone:</b> +{html.quote(data['phone'])}
        <b>Age:</b> {html.quote(data['age'])}
        <b>Event:</b> {html.quote(data['event'])}
        """
        await callback_query.message.answer(info, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())

        ADMIN_ID = 6470963942
        await bot.send_message(chat_id=ADMIN_ID, text=info, parse_mode=ParseMode.HTML)

        await state.clear()
    else:
        await callback_query.message.answer(
            "You are not following the channel yet. Please join the channel and click the button below to confirm. " + CHANNEL_USERNAME,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="I'm a follower", callback_data="check_follower")]
                ]
            )
        )

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.FileHandler("bot.log"), logging.StreamHandler(sys.stdout)]
    )
    asyncio.run(main())
