# TopGift Telegram Mini App

This is a Django-based Telegram Mini App featuring a gift roulette, lottery system, and TON cryptocurrency deposits, entirely manageable via an in-app Telegram admin panel.

## Features
- 🎁 **Roulette**: Spin to win gifts with customizable chances.
- 🎟️ **Lottery**: Buy tickets; automatically draws winners when sold out.
- 💎 **TON Deposits**: Connect your TON wallet (via TON Connect UI) and deposit TON to receive "Stars".
- 🎒 **Inventory**: View won gifts, sell them instantly for Stars, or request a withdrawal to your real wallet.
- 👑 **Admin Panel**: Accessible directly in the TWA for authorized users. Allows full CRUD management of Users (including bans), Gifts, Roulettes, Lotteries, Settings, and processing Withdrawals.

## Setup Instructions (Local / Windows / Mac)

1. **Clone/Download the repository**.
2. **Create a virtual environment (optional but recommended)**.
3. **Install dependencies**:
   `pip install -r requirements.txt`
4. **Configure Environment Variables**:
   Create a `.env` file in the root directory (where `manage.py` is):
   ```env
   BOT_TOKEN=your_bot_token_here
   WEB_APP_URL=https://your-cloudpub-url.com
   ADMIN_IDS=123456789 # Your Telegram ID
   SECRET_KEY=any_random_string
   DEBUG=True # Set to False in production
   ```
5. **Run Migrations (if DB is empty)**:
   `python manage.py migrate`
6. **Start the Django Server**:
   `python manage.py runserver`
7. **Start the Telegram Bot** (in a separate terminal window):
   `python bot.py`
