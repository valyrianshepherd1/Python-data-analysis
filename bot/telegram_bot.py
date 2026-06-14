"""Telegram bot with project menu pages and update subscriptions."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = (os.getenv("API_BASE_URL") or "").rstrip("/")
STREAMLIT_APP_URL = os.getenv("STREAMLIT_APP_URL", "")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "")

BASE_DIR = Path(__file__).resolve().parent.parent
SUBSCRIBERS_PATH = Path(
    os.getenv("SUBSCRIBERS_PATH", BASE_DIR / "data" / "processed" / "telegram_subscribers.txt")
)

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to Railway variables or to your .env file.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

SUBSCRIBE_BUTTON = "Subscribe to database updates"
UNSUBSCRIBE_BUTTON = "Unsubscribe"

MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "Project overview"}, {"text": "Dataset"}],
        [{"text": "Statistics"}, {"text": "Visualizations"}],
        [{"text": "Maps"}, {"text": "Hypothesis 1"}],
        [{"text": "Hypothesis 2"}, {"text": "API"}],
        [{"text": "Sample records"}, {"text": "Links"}],
        [{"text": SUBSCRIBE_BUTTON}, {"text": UNSUBSCRIBE_BUTTON}],
        [{"text": "Help"}],
    ],
    "resize_keyboard": True,
}


def telegram_request(method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.post(f"{TELEGRAM_API_URL}/{method}", json=payload or {}, timeout=20)
    response.raise_for_status()
    return response.json()


def split_message(text: str, limit: int = 3900) -> List[str]:
    if len(text) <= limit:
        return [text]

    parts = []
    current = ""
    for line in text.splitlines():
        if len(current) + len(line) + 1 > limit:
            parts.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        parts.append(current)

    return parts


def send_message(chat_id: int, text: str) -> None:
    for part in split_message(text):
        telegram_request(
            "sendMessage",
            {"chat_id": chat_id, "text": part, "reply_markup": MENU_KEYBOARD},
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


def subscribe_to_updates(chat_id: int) -> str:
    subscribers = load_subscribers()
    subscribers.add(chat_id)
    save_subscribers(subscribers)

    return (
        "You are subscribed to database updates.\n\n"
        "When a new demo record is created through POST /records, "
        "this bot will send you the full record information."
    )


def unsubscribe_from_updates(chat_id: int) -> str:
    subscribers = load_subscribers()
    subscribers.discard(chat_id)
    save_subscribers(subscribers)

    return "You are unsubscribed from database updates."


def get_records_from_api(limit: int = 3) -> Dict[str, Any]:
    if not API_BASE_URL:
        return {"error": "API_BASE_URL is not configured."}

    response = requests.get(
        f"{API_BASE_URL}/records",
        params={"limit": limit, "offset": 0},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def page_start() -> str:
    return (
        "ANES 2024 Election Analysis Bot\n\n"
        "Choose any project section from the menu below:\n"
        "- Project overview\n"
        "- Dataset\n"
        "- Statistics\n"
        "- Visualizations\n"
        "- Maps\n"
        "- Hypotheses\n"
        "- API\n"
        "- Sample records\n"
        "- Links\n\n"
        "The menu also contains optional update subscription buttons."
    )


def page_overview() -> str:
    return (
        "Project overview\n\n"
        "This project analyzes the ANES 2024 Time Series dataset. "
        "The main goal is to study voter turnout, presidential vote choice, "
        "demographic groups, ideology, education, income, and differences between states.\n\n"
        "The project has three technical parts:\n"
        "1. Jupyter notebook with data cleaning and analysis.\n"
        "2. Streamlit web app for interactive exploration.\n"
        "3. FastAPI backend with GET and POST methods.\n\n"
        "The Telegram bot gives quick access to the main project sections."
    )


def page_dataset() -> str:
    return (
        "Dataset\n\n"
        "Dataset: ANES 2024 Time Series Study.\n\n"
        "Main variables used in the app:\n"
        "- state_name\n"
        "- age and age_group\n"
        "- gender_label and sex_label\n"
        "- race_ethnicity_label\n"
        "- education_group\n"
        "- income_group\n"
        "- ideology_label\n"
        "- voter_turnout_label\n"
        "- presidential_vote_label\n\n"
        "Important limitation: the project uses the survey sample as an analytical dataset. "
        "It is not the same as official election results."
    )


def page_statistics() -> str:
    return (
        "Statistics section\n\n"
        "The statistics part of the project shows descriptive statistics for numerical variables, "
        "including count, mean, median, standard deviation, minimum, and maximum.\n\n"
        "It also shows frequency tables for categorical variables, such as state, vote choice, "
        "turnout, race/ethnicity, gender, education, income group, and ideology."
    )


def page_visualizations() -> str:
    return (
        "Visualizations section\n\n"
        "The Streamlit app contains charts for:\n"
        "- age distribution\n"
        "- education distribution\n"
        "- income distribution\n"
        "- ideology distribution\n"
        "- voter turnout distribution\n"
        "- race/ethnicity distribution\n"
        "- gender and sex distribution\n"
        "- pre-election and final presidential vote choice\n"
        "- top states by number of respondents"
    )


def page_maps() -> str:
    return (
        "Maps section\n\n"
        "The project contains choropleth maps by US state:\n"
        "- number of respondents by state\n"
        "- reported voter turnout rate by state\n"
        "- major-party vote balance by state\n"
        "- average ideology by state\n"
        "- average respondent age by state\n\n"
        "For rate maps, a minimum respondent threshold is used to avoid showing unstable rates "
        "for states with very small sample sizes."
    )


def page_hypothesis_1() -> str:
    return (
        "Hypothesis 1\n\n"
        "Reported voter turnout is higher among older respondents, especially in higher income groups.\n\n"
        "Variables used:\n"
        "- age_group\n"
        "- income_group\n"
        "- voter_turnout\n\n"
        "The app checks this with a table and a heatmap of turnout percentages by age group and income group."
    )


def page_hypothesis_2() -> str:
    return (
        "Hypothesis 2\n\n"
        "Education is related to presidential vote choice within ideology groups.\n\n"
        "Variables used:\n"
        "- education_group\n"
        "- ideology_label\n"
        "- presidential_vote_label\n\n"
        "The app compares Harris and Trump vote shares across education groups inside ideology categories."
    )


def page_api() -> str:
    api_text = (
        "API section\n\n"
        "The project uses FastAPI as a backend for the Streamlit app.\n\n"
        "Main endpoints:\n"
        "GET /records\n"
        "Returns records from the cleaned dataset with optional filters.\n\n"
        "POST /records\n"
        "Creates one demo record and saves it separately from the original dataset.\n\n"
        "Telegram subscription logic:\n"
        "The bot saves subscribed chat IDs into telegram_subscribers.txt. "
        "The API reads the same file when it sends update notifications.\n\n"
    )

    if API_BASE_URL:
        api_text += (
            f"API base URL:\n{API_BASE_URL}\n\n"
            f"API documentation:\n{API_BASE_URL}/docs\n\n"
            f"Example GET request:\n{API_BASE_URL}/records?limit=5&offset=0"
        )
    else:
        api_text += "API_BASE_URL is not configured for this bot."

    return api_text


def page_sample_records() -> str:
    try:
        payload = get_records_from_api(limit=3)
    except requests.RequestException as error:
        return f"Could not load sample records from API.\n\nError:\n{error}"

    if "error" in payload:
        return payload["error"]

    records = payload.get("records", [])
    if not records:
        return "The API returned no records."

    lines = [
        "Sample records from GET /records",
        "",
        f"Total matches: {payload.get('total_matches')}",
        "",
    ]

    for index, record in enumerate(records, start=1):
        lines.append(f"Record {index}")
        lines.append(f"State: {record.get('state_name', 'N/A')}")
        lines.append(f"Age: {record.get('age', 'N/A')}")
        lines.append(f"Race/ethnicity: {record.get('race_ethnicity_label', 'N/A')}")
        lines.append(f"Education: {record.get('education_group', 'N/A')}")
        lines.append(f"Income: {record.get('income_group', 'N/A')}")
        lines.append(f"Ideology: {record.get('ideology_label', 'N/A')}")
        lines.append(f"Turnout: {record.get('voter_turnout_label', 'N/A')}")
        lines.append(f"Vote: {record.get('presidential_vote_label', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def page_links() -> str:
    lines = ["Project links", ""]

    if STREAMLIT_APP_URL:
        lines.append(f"Streamlit app:\n{STREAMLIT_APP_URL}")
        lines.append("")
    else:
        lines.append("STREAMLIT_APP_URL is not configured.")
        lines.append("")

    if API_BASE_URL:
        lines.append(f"FastAPI docs:\n{API_BASE_URL}/docs")
        lines.append("")
    else:
        lines.append("API_BASE_URL is not configured.")
        lines.append("")

    if GITHUB_REPO_URL:
        lines.append(f"GitHub repository:\n{GITHUB_REPO_URL}")
    else:
        lines.append("GITHUB_REPO_URL is not configured.")

    return "\n".join(lines)


def page_help() -> str:
    return (
        "Help\n\n"
        "Press one of the menu buttons:\n"
        "- Project overview: general project description\n"
        "- Dataset: dataset and variables\n"
        "- Statistics: descriptive statistics section\n"
        "- Visualizations: charts in the app\n"
        "- Maps: state maps\n"
        "- Hypothesis 1: turnout, age, and income\n"
        "- Hypothesis 2: education, ideology, and vote choice\n"
        "- API: FastAPI endpoints and documentation\n"
        "- Sample records: live records from the API\n"
        "- Links: Streamlit app, API docs, and GitHub link\n"
        "- Subscribe to database updates: receive new-record notifications\n"
        "- Unsubscribe: stop receiving new-record notifications"
    )


def page_unknown() -> str:
    return (
        "I did not recognize this message as a project menu option.\n\n"
        "Use the menu below or type Help."
    )


def handle_text(chat_id: int, text: str) -> None:
    normalized = text.strip().lower()

    pages = {
        "/start": page_start,
        "start": page_start,
        "/help": page_help,
        "help": page_help,
        "project overview": page_overview,
        "overview": page_overview,
        "dataset": page_dataset,
        "data": page_dataset,
        "statistics": page_statistics,
        "stats": page_statistics,
        "visualizations": page_visualizations,
        "visualization": page_visualizations,
        "charts": page_visualizations,
        "maps": page_maps,
        "map": page_maps,
        "hypothesis 1": page_hypothesis_1,
        "hypothesis one": page_hypothesis_1,
        "hypothesis 2": page_hypothesis_2,
        "hypothesis two": page_hypothesis_2,
        "api": page_api,
        "fastapi": page_api,
        "sample records": page_sample_records,
        "records": page_sample_records,
        "links": page_links,
        "subscribe to database updates": lambda: subscribe_to_updates(chat_id),
        "subscribe to updates": lambda: subscribe_to_updates(chat_id),
        "/subscribe": lambda: subscribe_to_updates(chat_id),
        "subscribe": lambda: subscribe_to_updates(chat_id),
        "unsubscribe": lambda: unsubscribe_from_updates(chat_id),
        "unsubscribe from updates": lambda: unsubscribe_from_updates(chat_id),
        "unsubscribe from database updates": lambda: unsubscribe_from_updates(chat_id),
        "/unsubscribe": lambda: unsubscribe_from_updates(chat_id),
    }

    page_function = pages.get(normalized)
    if page_function is None:
        send_message(chat_id, page_unknown())
    else:
        send_message(chat_id, page_function())


def main() -> None:
    print("Telegram project menu bot is running. Press Ctrl+C to stop.")
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
