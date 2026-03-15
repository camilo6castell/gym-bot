import os
import requests
from dotenv import load_dotenv

load_dotenv()
base = f"https://api.telegram.org/bot{os.getenv('TOKEN')}"

def notify(msg):
    print("mensaje a notificar", msg)
    url = f"{base}/sendMessage"
    requests.post(url, json={
        "chat_id": os.getenv('CHAT_ID'),
        "text": msg
    })

def getUpdates():
    url = f"{base}/getUpdates"
    return requests.get(url).json()

