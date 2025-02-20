import os
import logging
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types

BOT_TOKEN = "8120956703:AAFgC0YCApZAR-149EXMEISq00ZNzvjAYRY" #  actual token: 8120956703:AAFgC0YCApZAR-149EXMEISq00ZNzvjAYRY
GROUP_CHAT_ID = "-1002274219234"

ADMIN_ID = [7077167971, 6327823559, 7583614105]

telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN)

uzbekistan_tz = pytz.timezone("Asia/Tashkent")

IMAGE_FOLDER = "photos"

SENDING_TIMES = [
    "06:00", "08:50", "11:40", "14:30", "17:20", "20:10", "23:00"
]

@bot.message_handler(commands=["send"])
def send_photos_command(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        pass
    else:
        send_photos()

def send_photos():
    try:
        images = [os.path.join(IMAGE_FOLDER, img) for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png"))]

        if not images:
            bot.send_message(ADMIN_ID, "rasmlar tugadi")
        elif images:
            images = images[:9]
            media_group = []

            for img in images:
                with open(img, "rb") as file:
                    media_group.append(telebot.types.InputMediaPhoto(file.read(), caption="Rasmlar"))

            bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media_group)

            for img in images:
                os.remove(img)
        else:
            bot.send_message(ADMIN_ID, "ERROR")

    except Exception as e:
        logging.error(f"❌ Error sending photos: {e}")

@bot.message_handler(commands=["start"])
def check_status(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📸 qolgan rasmlarni ko'rish", callback_data="photo_count"),
               InlineKeyboardButton("📤 Rasmlar qancha postga yetishini ko'rish", callback_data="post_count"))

        bot.send_message(message.chat.id, "📊 Bot Status:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["photo_count", "post_count"])
def refresh_status(call: types.CallbackQuery):
    os.path.join(IMAGE_FOLDER)

    photo_count = len([img for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png", "webp"))])
    if photo_count == 0:
        post_count = 0
    else:
        post_count = photo_count // 9

    if call.data == "photo_count":
        bot.answer_callback_query(call.id, f"📸 Qolgan rasmlar: {photo_count}", show_alert=True)
    elif call.data == "post_count":
        bot.answer_callback_query(call.id, f"📤 Post qilishga yetadi: {post_count} marta", show_alert=True)


@bot.message_handler(content_types=["photo"])
def handle_photo(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        pass
    else:
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)

        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(IMAGE_FOLDER, file_info.file_path.split("/")[-1])

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, "Rasm Saqlandi")

scheduler = BackgroundScheduler()

for time_str in SENDING_TIMES:
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(send_photos, "cron", hour=hour, minute=minute, timezone=uzbekistan_tz)


scheduler.start()
# bot.infinity_polling()
