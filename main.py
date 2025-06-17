import os
import time
import json
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# Environment variables
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("INTERVAL", 30))  # 30 seconds default
TARGET_URL = "https://movingsoon.co.uk/agent/clarionhg/"
DATA_FILE = "/mnt/data/listings_seen.json"  # Persisted on Render

bot = Bot(token=TELEGRAM_TOKEN)

def load_seen():
    try:
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen):
    with open(DATA_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_listings():
    try:
        response = requests.get(TARGET_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    property_cards = soup.select("article.property")
    listings = []

    for card in property_cards:
        a_tag = card.find("a", href=True)
        if a_tag:
            title = a_tag.get_text(strip=True)
            relative_url = a_tag["href"]
            full_url = "https://movingsoon.co.uk" + relative_url
            listings.append((full_url, title))
    return listings

def send_telegram_message(title, url):
    message = f"🏠 *New Clarion Listing!*\n\n*{title}*\n{url}"
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to send message: {e}")

def main():
    seen = load_seen()
    print("Clarion bot started. Checking for new listings...")

    while True:
        listings = fetch_listings()
        new = False

        for url, title in listings:
            if url not in seen:
                print(f"New listing: {title}")
                send_telegram_message(title, url)
                seen.add(url)
                new = True

        if new:
            save_seen(seen)
        else:
            print("No new listings.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
