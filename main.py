import os
import requests
from bs4 import BeautifulSoup
import time
from flask import Flask
from threading import Thread
from datetime import datetime
import json

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MOVINGSOON_URL = "https://movingsoon.co.uk/agent/clarionhg/"
SEEN_FILE = "seen.json"

# Load seen listings from file
def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

# Save seen listings to file
def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen = load_seen()

# Send Telegram message
def send_alert(title, url):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"\ud83c\udfe0 *New Clarion Listing!*\n\n*{title}*\n{url}\n\n\ud83d\udd52 Detected at: {timestamp}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )
    print("\ud83d\udce8 Sent alert:", title)

# Scrape listings
def get_listings():
    rsp = requests.get(MOVINGSOON_URL)
    soup = BeautifulSoup(rsp.text, "html.parser")
    items = soup.select(".property-content h2 a")
    new = []
    for itm in items:
        url = itm['href']
        title = itm.get_text(strip=True)
        if url not in seen:
            seen.add(url)
            new.append((title, url))
    return new

app = Flask('')

@app.route('/')
def home():
    listings = list(seen)[-5:]
    display = "<br>".join(f"<a href='{u}' target='_blank'>{u}</a>" for u in listings)
    return f"\u2705 Bot running. <br><br>Recent listings:<br>{display}"

# Start Flask app
def run():
    app.run(host='0.0.0.0', port=10000)

# Keep bot alive by pinging itself
def self_ping():
    while True:
        try:
            requests.get("https://clarion-alert-bot.onrender.com")
        except:
            pass
        time.sleep(60)

Thread(target=run).start()
Thread(target=self_ping).start()

print("\ud83e\udd16 Bot started...")

# Check for listings loop
while True:
    try:
        new_listings = get_listings()
        for t, u in new_listings:
            send_alert(t, u)
        if new_listings:
            save_seen(seen)
        print("\u2705 Checked for new listings.")
    except Exception as e:
        print("\u26a0\ufe0f Error:", e)
    time.sleep(30)
