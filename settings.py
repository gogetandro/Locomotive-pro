import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./locomotive.db")

settings = Settings()
