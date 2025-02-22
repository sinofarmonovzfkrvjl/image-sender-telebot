import os
import logging
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot import types

BOT_TOKEN = "8120956703:AAFgC0YCApZAR-149EXMEISq00ZNzvjAYRY"
GROUP_CHAT_ID = "@Glavniga_suratlar_RASMIY"
ADMIN_ID = [5230484991, 7077167971, 6327823559, 7583614105]

telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="MARKDOWN")

uzbekistan_tz = pytz.timezone("Asia/Tashkent")

os.environ["TZ"] = "Asia/Tashkent"

IMAGE_FOLDER = "photos"

SENDING_TIMES = [
    "06:00", "08:50", "11:40", "14:30", "17:20", "20:10", "23:00"
]

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

@bot.message_handler(commands=["send"])
def send_photos_command(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
        return
    send_photos()

def send_photos():
    try:
        images = [os.path.join(IMAGE_FOLDER, img) for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png"))]

        if not images:
            for admin_id in ADMIN_ID:
                try:
                    bot.send_message(admin_id, "Rasmlar tugadi")
                except:
                    continue
        elif images:
            images = images[:9]
            media_group = []

            for img in images:
                with open(img, "rb") as file:
                    media_group.append(telebot.types.InputMediaPhoto(file.read()))

            if media_group:
                media_group[0].caption = "Link - [Reaksiya bosamiz](https://t.me/+Qn_TbuMIrPU0YjMy)"
                bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media_group)

                for img in images:
                    os.remove(img)

    except Exception as e:
        logging.error(f"Error sending photos: {e}")
        for admin_id in ADMIN_ID:
            try:
                bot.send_message(admin_id, f"Xatolik yuz berdi: {str(e)}")
            except:
                continue

@bot.message_handler(commands=["start"])
def check_status(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
        return
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("📸 qolgan rasmlarni ko'rish"),
        KeyboardButton("📤 Rasmlar qancha postga yetishini ko'rish")
    )

    bot.send_message(
        message.chat.id,
        f"Salom {message.from_user.full_name}\n\n📊 Bot Status:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in ["📸 qolgan rasmlarni ko'rish", "📤 Rasmlar qancha postga yetishini ko'rish"])
def see_bot_status(message: types.Message):
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    photo_count = len([img for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(("jpg", "jpeg", "png", "webp"))])
    
    if photo_count == 0:
        bot.send_message(message.chat.id, "Rasmlar mavjud emas")
    else:
        post_count = photo_count // 9
        
        if message.text == "📸 qolgan rasmlarni ko'rish":
            bot.send_message(message.chat.id, f"📸 Qolgan rasmlar: {photo_count}")
        elif message.text == "📤 Rasmlar qancha postga yetishini ko'rish":
            bot.send_message(message.chat.id, f"📤 Post qilishga yetadi: {post_count} marta")

@bot.message_handler(commands=['delete'])
def delete_all_photos(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
    else:
        photos = [os.path.join(IMAGE_FOLDER, img) for img in os.listdir(IMAGE_FOLDER)]
        for photo in photos:
            os.remove(photo)
    
    bot.reply_to(message, "Rasmlar o'chirildi")

@bot.message_handler(commands=['jadval'])
def jadvalni_jonatish(message: types.Message):
    bot.send_message(message.chat.id, "06:00, 08:50, 11:40, 14:30, 17:20, 20:10, 23:00")

@bot.message_handler(content_types=["photo", "document"])
def handle_photo(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        pass
    else:
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)

        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_path = os.path.join(IMAGE_FOLDER, f"{file_info.file_id}.jpg")

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, "Rasm Saqlandi")

scheduler = BackgroundScheduler()

for time_str in SENDING_TIMES:
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(send_photos, "cron", hour=hour, minute=minute, timezone=uzbekistan_tz)

scheduler.start()
# bot.infinity_polling(skip_pending=True)
