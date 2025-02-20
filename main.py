import os
import logging
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8120956703:AAFgC0YCApZAR-149EXMEISq00ZNzvjAYRY" #  actual token: 8120956703:AAFgC0YCApZAR-149EXMEISq00ZNzvjAYRY
GROUP_CHAT_ID = "-1002296234497"

ADMIN_ID = [7077167971, 5230484991, 6327823559, 7583614105]

telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN)

uzbekistan_tz = pytz.timezone("Asia/Tashkent")

IMAGE_FOLDER = "photos"

SENDING_TIMES = [
    "06:00", "08:50", "11:40", "14:30", "17:20", "20:10", "23:00"
]

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Bot started!")

@bot.message_handler(commands=["send"])
def send_photos_command(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "You are not authorized to use this command!")
        return

    send_photos()

def send_photos():
    try:
        images = [os.path.join(IMAGE_FOLDER, img) for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png"))]

        if not images:
            bot.send_message(ADMIN_ID, "No photos available to send!")
            return

        images = images[:9]
        media_group = []

        for img in images:
            with open(img, "rb") as file:
                media_group.append(telebot.types.InputMediaPhoto(file.read(), caption="Rasmlar"))

        bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media_group)

        for img in images:
            os.remove(img)

        logging.info(f"✅ Sent {len(images)} photos to the group!")

    except Exception as e:
        logging.error(f"❌ Error sending photos: {e}")

@bot.message_handler(commands=["status"])
def check_status(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "You are not authorized to use this command!")
        return

    photo_count = len([img for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png"))])
    post_count = photo_count // 9  

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📸 Qancha rasm qoldi", callback_data="photo_count"),
               InlineKeyboardButton("📤 Rasm qancha postga yetadi", callback_data="post_count"))

    bot.send_message(message.chat.id, "📊 Bot Status:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["photo_count", "post_count"])
def refresh_status(call):
    photo_count = len([img for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png"))])
    post_count = photo_count // 9  

    if call.data == "photo_count":
        bot.answer_callback_query(call.id, f"📸 Qolgan rasmlar: {photo_count}")
    elif call.data == "post_count":
        bot.answer_callback_query(call.id, f"📤 Post qilishga yetadi: {post_count} marta")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "You are not authorized to send photos!")
        return

    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = os.path.join(IMAGE_FOLDER, file_info.file_path.split("/")[-1])

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    bot.reply_to(message, "Photo saved!")

scheduler = BackgroundScheduler()

for time_str in SENDING_TIMES:
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(send_photos, "cron", hour=hour, minute=minute, timezone=uzbekistan_tz)

scheduler.start()
bot.infinity_polling()
