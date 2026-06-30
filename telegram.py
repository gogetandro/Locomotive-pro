import requests
from app.settings import settings

def send_telegram(text: str):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"sent": False, "reason": "Telegram not configured"}
    url=f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    r=requests.post(url, json={"chat_id":settings.telegram_chat_id,"text":text}, timeout=10)
    return {"sent": r.ok, "status": r.status_code, "body": r.text[:200]}
