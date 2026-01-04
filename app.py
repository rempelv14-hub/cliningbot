import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart
import urllib.parse

# ===== Настройки =====
TOKEN = "8449548749:AAEAQwo0JNuor1GuBS386ZxVSA1f4LbpsoY"
WHATSAPP_NUMBER = "77071700479"

PRICES = {
    "🧹 Генеральная уборка": 650,
    "🧼 Влажная уборка": 450,
    "🏗 После ремонта": 800,
}

# ===== FSM состояния =====
class Order(StatesGroup):
    service = State()
    area = State()
    full_name = State()
    date_time = State()
    address = State()

bot = Bot(TOKEN)
dp = Dispatcher()

# ===== Главное меню =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧹 Генеральная уборка"), KeyboardButton(text="🧼 Влажная уборка")],
        [KeyboardButton(text="🏗 После ремонта"), KeyboardButton(text="🪜 Мытьё потолка")],
        [KeyboardButton(text="🏢 Уборка подъезда"), KeyboardButton(text="🛋 Химчистка")],
        [KeyboardButton(text="❓ Чем отличается ген и влажная"), KeyboardButton(text="❓ Частые вопросы")]
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Главное меню")]],
    resize_keyboard=True
)

# ===== Старт =====
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте! 👋\nВы обратились в клининговую компанию 🧼\nВыберите услугу или вопрос:",
        reply_markup=main_kb
    )

# ===== Главное меню кнопка =====
@dp.message(lambda m: m.text == "⬅️ Главное меню")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вы вернулись в главное меню. Выберите услугу или вопрос:",
        reply_markup=main_kb
    )

# ===== Разница уборок =====
@dp.message(lambda m: m.text == "❓ Чем отличается ген и влажная")
async def diff(message: Message):
    await message.answer(
        "🧹 *Генеральная уборка:*\n"
        "• тщательная уборка всех комнат\n"
        "• удаление пыли со всех поверхностей\n"
        "• мытьё полов и плинтусов\n"
        "• уборка кухни с обезжириванием\n"
        "🧼 *Влажная уборка:*\n"
        "• протирание поверхностей\n"
        "• влажная уборка полов\n"
        "• уборка кухни без удаления жира",
        parse_mode="Markdown"
    )

# ===== FAQ =====
faq_texts = {
    "1": "Генеральная уборка стоит 650 тг за 1 м².",
    "2": "Генеральная уборка — полная, с удалением жира и мытьём окон. Влажная — поверхностная, без сильного обезжиривания.",
    "3": "Да, работаем в выходные, уточняйте дату при записи.",
    "4": "Средняя квартира 50-60 м²: 2-3 часа.",
    "5": "Химчистка рассчитывается индивидуально по фото мебели."
}

@dp.message(lambda m: m.text == "❓ Частые вопросы")
async def faq(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Сколько стоит генеральная уборка?", callback_data="faq_1")],
            [InlineKeyboardButton(text="2️⃣ Чем отличается генеральная и влажная?", callback_data="faq_2")],
            [InlineKeyboardButton(text="3️⃣ Можно ли вызвать уборку на выходные?", callback_data="faq_3")],
            [InlineKeyboardButton(text="4️⃣ Сколько времени занимает уборка?", callback_data="faq_4")],
            [InlineKeyboardButton(text="5️⃣ Как рассчитывается химчистка?", callback_data="faq_5")]
        ]
    )
    await message.answer("Выберите вопрос:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("faq_"))
async def answer_faq(call):
    key = call.data.split("_")[1]
    await call.message.answer(faq_texts.get(key, "Ответ не найден"))
    await call.answer()

# ===== Выбор услуги =====
@dp.message(lambda m: m.text in [
    "🧹 Генеральная уборка", "🧼 Влажная уборка", "🏗 После ремонта",
    "🪜 Мытьё потолка", "🏢 Уборка подъезда", "🛋 Химчистка"
])
async def choose_service(message: Message, state: FSMContext):
    service = message.text
    await state.update_data(service=service)

    # Химчистка сразу в WhatsApp
    if service == "🛋 Химчистка":
        wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text=Здравствуйте! Я хочу заказать химчистку."
        wa_button = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Написать менеджеру", url=wa_link)]]
        )
        await message.answer("🛋 Для химчистки свяжитесь с менеджером:", reply_markup=wa_button)
        return

    # Если услуга с квадратурой
    if service in PRICES:
        await state.set_state(Order.area)
        await message.answer(f"{service} стоит {PRICES[service]} тг за м².\nВведите площадь (только число):", reply_markup=back_kb)
    else:
        await state.set_state(Order.full_name)
        await message.answer(f"Вы выбрали {service}. Введите ФИО:", reply_markup=back_kb)

# ===== Ввод площади =====
@dp.message(Order.area, F.text)
async def get_area(message: Message, state: FSMContext):
    if message.text.startswith("❓") or message.text == "⬅️ Главное меню":
        # Если пользователь нажал FAQ или Главное меню — игнорируем этот шаг
        return
    if not message.text.isdigit():
        await message.answer("Неверный формат. Введите число, например: 42")
        return
    area = int(message.text)
    data = await state.get_data()
    price_per_m2 = PRICES[data["service"]]
    total = area * price_per_m2
    await state.update_data(area=area, total=total)
    await state.set_state(Order.full_name)
    await message.answer(f"💰 Стоимость: {total} тг\nВведите ФИО:", reply_markup=back_kb)

# ===== Ввод ФИО =====
@dp.message(Order.full_name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(Order.date_time)
    await message.answer("Введите дату и время уборки:", reply_markup=back_kb)

# ===== Ввод даты и времени =====
@dp.message(Order.date_time, F.text)
async def get_date(message: Message, state: FSMContext):
    await state.update_data(date_time=message.text)
    await state.set_state(Order.address)
    await message.answer("Введите адрес:", reply_markup=back_kb)

# ===== Ввод адреса и кнопка WhatsApp =====
@dp.message(Order.address, F.text)
async def get_address(message: Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")
    full_name = data.get("full_name")
    date_time = data.get("date_time")
    address = message.text
    total = data.get("total", "-")

    text = f"Услуга: {service}\nФИО: {full_name}\nДата и время: {date_time}\nАдрес: {address}"
    if total != "-":
        text += f"\nСтоимость: {total} тг"

    wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(text)}"
    wa_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать менеджеру", url=wa_link)]]
    )

    await message.answer("✅ Заявка заполнена! Нажмите кнопку ниже, чтобы отправить её менеджеру:", reply_markup=wa_button)
    await state.clear()

# ===== Запуск =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
