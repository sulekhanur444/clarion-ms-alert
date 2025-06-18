import os
import requests
from bs4 import BeautifulSoup
import time
from flask import Flask
from threading import Thread

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
RIGHTMOVE_URL = "https://www.rightmove.co.uk/estate-agents/profile/Clarion-Housing-Lettings/UK-58989.html"
seen = set()

def send_alert(title, url):
    message = f"🏠 *New Clarion Listing!*\n\n{title}\n{url}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    )
    print("📨 Sent alert:", title)

def get_listings():
    rsp = requests.get(RIGHTMOVE_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(rsp.text, "html.parser")
    items = soup.select("a.propertyCard-link")  # Rightmove class for listings
    new = []
    for itm in items:
        url = "https://www.rightmove.co.uk" + itm['href']
        title = itm.get_text(strip=True)
        if url not in seen:
            seen.add(url)
            new.append((title, url))
    return new

# Flask app for uptime
app = Flask('')
@app.route('/')
def home():
    return "✅ Clarion Rightmove bot is live!"

def run():
    app.run(host='0.0.0.0', port=10000)

def self_ping():
    while True:
        try:
            requests.get("https://clarion-alert-bot.onrender.com")  # Your Render URL
        except:
            pass
        time.sleep(60)

def start_bot():
    while True:
        try:
            for title, url in get_listings():
                send_alert(title, url)
            print("✅ Checked for new listings.")
        except Exception as e:
            print("⚠️ Error:", e)
        time.sleep(60)

# Start threads
Thread(target=run).start()
Thread(target=self_ping).start()
Thread(target=start_bot).start()
