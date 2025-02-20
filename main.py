import os
import logging
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from telebot import logger, types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message, InputMediaPhoto
from datetime import datetime

BOT_TOKEN = "7534683635:AAFkejwXgRovlVTCdkeHBBwDbOBA3AKA5P0"
GROUP_CHAT_ID = "-1002274219234"
ADMIN_ID = [7077167971, 6327823559, 7583614105]
IMAGE_FOLDER = "photos"
SENDING_TIMES = ["06:00", "08:50", "11:40", "14:30", "17:20", "20:10", "23:00"]

bot = telebot.TeleBot(BOT_TOKEN)

logger.setLevel(logging.INFO)

uzbekistan_tz = pytz.timezone("Asia/Tashkent")

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def send_photos():
    """Send photos to the group chat"""
    try:
        # Get list of image files
        images = [
            os.path.join(IMAGE_FOLDER, img) 
            for img in os.listdir(IMAGE_FOLDER) 
            if img.lower().endswith(("jpg", "jpeg", "png"))
        ]

        if not images:
            # Notify all admins
            for admin_id in ADMIN_ID:
                try:
                    bot.send_message(admin_id, "❌ Rasmlar tugadi!")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            return

        # Take first 9 images
        batch_images = images[:9]
        media_group = []

        # Prepare media group
        for img in batch_images:
            try:
                with open(img, "rb") as file:
                    media_group.append(InputMediaPhoto(file.read()))
            except Exception as e:
                logger.error(f"Error processing image {img}: {e}")
                continue

        if media_group:
            # Set caption only for the first image
            media_group[0].caption = f"📸 Post vaqti: {datetime.now(uzbekistan_tz).strftime('%H:%M')}"
            
            # Send media group
            bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media_group)

            # Delete sent images
            for img in batch_images:
                try:
                    os.remove(img)
                except Exception as e:
                    logger.error(f"Error deleting image {img}: {e}")

    except Exception as e:
        logger.error(f"Error in send_photos: {e}")
        # Notify admins about error
        for admin_id in ADMIN_ID:
            try:
                bot.send_message(admin_id, f"❌ Xatolik yuz berdi: {str(e)}")
            except:
                pass

@bot.message_handler(commands=["send"])
def send_photos_command(message: Message):
    """Manual trigger for sending photos"""
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
        return
    send_photos()
    bot.reply_to(message, "✅ Rasmlar yuborildi")

@bot.message_handler(commands=["start"])
def check_status(message: Message):
    """Handle start command"""
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

@bot.message_handler(func=lambda message: message.text in [
    "📸 qolgan rasmlarni ko'rish",
    "📤 Rasmlar qancha postga yetishini ko'rish"
])
def see_bot_status(message: Message):
    """Handle status check buttons"""
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
        return

    photo_count = len([
        img for img in os.listdir(IMAGE_FOLDER)
        if img.lower().endswith(("jpg", "jpeg", "png", "webp"))
    ])
    
    if photo_count == 0:
        bot.send_message(message.chat.id, "Rasmlar mavjud emas")
        return
        
    post_count = photo_count // 9
    
    if message.text == "📸 qolgan rasmlarni ko'rish":
        bot.send_message(message.chat.id, f"📸 Qolgan rasmlar: {photo_count}")
    elif message.text == "📤 Rasmlar qancha postga yetishini ko'rish":
        bot.send_message(message.chat.id, f"📤 Post qilishga yetadi: {post_count} marta")

@bot.message_handler(commands=['delete'])
def delete_all_photos(message: Message):
    """Delete all photos in the folder"""
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Siz Admin emassiz")
        return

    try:
        photos = [os.path.join(IMAGE_FOLDER, img) for img in os.listdir(IMAGE_FOLDER)]
        for photo in photos:
            os.remove(photo)
        bot.reply_to(message, "✅ Barcha rasmlar o'chirildi")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")

@bot.message_handler(content_types=["photo"])
def handle_photo(message: Message):
    """Handle incoming photos"""
    if message.from_user.id not in ADMIN_ID:
        return

    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Generate unique filename using timestamp
        file_name = f"photo_{message.date}.jpg"
        file_path = os.path.join(IMAGE_FOLDER, file_name)

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, "✅ Rasm saqlandi")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")

def main():
    """Main function to start the bot"""
    try:
        # Setup scheduler
        scheduler = BackgroundScheduler()
        
        # Add jobs for each sending time
        for time_str in SENDING_TIMES:
            hour, minute = map(int, time_str.split(":"))
            scheduler.add_job(
                send_photos,
                "cron",
                hour=hour,
                minute=minute,
                timezone=uzbekistan_tz
            )
        
        # Start scheduler
        scheduler.start()
        
        logger.info("Bot started. Press Ctrl+C to exit.")
        
        # Start bot
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    main()