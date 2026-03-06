import os
import requests
from dotenv import load_dotenv

load_dotenv()

def notify(msg):
    print("mensaje a notificar", msg)
    url = f"https://api.telegram.org/bot{os.getenv('TOKEN')}/sendMessage"
    requests.post(url, json={
        "chat_id": os.getenv('CHAT_ID'),
        "text": msg
    })
