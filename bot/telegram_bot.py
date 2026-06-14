"""Telegram bot for database update subscriptions."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_DIR = Path(__file__).resolve().parent.parent
SUBSCRIBERS_PATH = Path(
    os.getenv("TELEGRAM_SUBSCRIBERS_PATH", BASE_DIR / "data" / "processed" / "telegram_subscribers.txt")
)

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to your .env file.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Subscribe to database updates"}],
        [{"text": "Unsubscribe"}],
    ],
    "resize_keyboard": True,
}


def telegram_request(method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.post(f"{TELEGRAM_API_URL}/{method}", json=payload or {}, timeout=20)
    response.raise_for_status()
    return response.json()


def send_message(chat_id: int, text: str) -> None:
    telegram_request(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "reply_markup": MENU_KEYBOARD},
    )


def get_updates(offset: Optional[int]) -> List[Dict[str, Any]]:
    payload: Dict[str, Any] = {"timeout": 25}
    if offset is not None:
        payload["offset"] = offset
    data = telegram_request("getUpdates", payload)
    return data.get("result", [])


def load_subscribers() -> Set[int]:
    if not SUBSCRIBERS_PATH.exists():
        return set()
    subscribers: Set[int] = set()
    for line in SUBSCRIBERS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            subscribers.add(int(line))
    return subscribers


def save_subscribers(subscribers: Set[int]) -> None:
    SUBSCRIBERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(str(chat_id) for chat_id in sorted(subscribers))
    SUBSCRIBERS_PATH.write_text(text + ("\n" if text else ""), encoding="utf-8")


def subscribe(chat_id: int) -> None:
    subscribers = load_subscribers()
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    send_message(chat_id, "You are subscribed to database updates.")


def unsubscribe(chat_id: int) -> None:
    subscribers = load_subscribers()
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    send_message(chat_id, "You are unsubscribed from database updates.")


def handle_text(chat_id: int, text: str) -> None:
    normalized = text.strip().lower()

    if normalized in {"/start", "start"}:
        send_message(chat_id, "Choose an option:")
    elif normalized == "subscribe to database updates":
        subscribe(chat_id)
    elif normalized == "unsubscribe":
        unsubscribe(chat_id)
    else:
        send_message(chat_id, "Choose one of the buttons below.")


def main() -> None:
    print("Telegram bot is running. Press Ctrl+C to stop.")
    last_update_id: Optional[int] = None

    while True:
        try:
            updates = get_updates(None if last_update_id is None else last_update_id + 1)
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                chat_id = chat.get("id")
                text = message.get("text")
                if chat_id is not None and text:
                    handle_text(chat_id, text)
        except requests.RequestException as exc:
            print(f"Telegram request failed: {exc}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Bot stopped.")
            break


if __name__ == "__main__":
    main()
