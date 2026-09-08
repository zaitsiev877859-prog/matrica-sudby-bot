import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]
ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", "0"))
SUPPORT_URL = os.environ.get("SUPPORT_URL", "https://t.me/vladimirzaytzev")
