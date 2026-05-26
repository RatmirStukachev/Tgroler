import os
import django
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

# Set up Django environment so we can use models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://example.com") # Replace with actual URL

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    name = first_name
    if last_name:
        name += f" {last_name}"

    # Get or create user
    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={'username': username, 'name': name}
    )

    if not created:
        # Update user details if they changed
        user.username = username
        user.name = name
        user.save()

    markup = InlineKeyboardMarkup()
    web_app_btn = InlineKeyboardButton(
        text="Open TopGift 🎁",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    markup.add(web_app_btn)

    bot.reply_to(
        message,
        f"Welcome to TopGift, {name}! 🎁\nClick the button below to start.",
        reply_markup=markup
    )

if __name__ == '__main__':
    print("Bot is running...")
    # bot.infinity_polling()
