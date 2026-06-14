from pathlib import Path
from typing import Any, Dict, List, Optional
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv("DATA_PATH", BASE_DIR / "data" / "processed" / "anes_2024_selected_clean.csv"))
ADDED_RECORDS_PATH = Path(
    os.getenv("ADDED_RECORDS_PATH", BASE_DIR / "data" / "processed" / "user_added_records.csv")
)
SUBSCRIBERS_PATH = Path(
    os.getenv("SUBSCRIBERS_PATH", BASE_DIR / "data" / "processed" / "telegram_subscribers.txt")
)

app = FastAPI(
    title="ANES 2024 Election Analysis API",
    description="Minimal REST API for the Streamlit election analysis project.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewRecord(BaseModel):
    state_name: str = Field(..., example="California")
    age: int = Field(..., ge=18, le=100, example=35)
    gender_label: Optional[str] = Field(None, example="Woman")
    sex_label: Optional[str] = Field(None, example="Female")
    race_ethnicity_label: Optional[str] = Field(None, example="White, non-Hispanic")
    education_group: Optional[str] = Field(None, example="Bachelor's degree")
    income_group: Optional[str] = Field(None, example="Middle income categories")
    ideology_label: Optional[str] = Field(None, example="Moderate")
    voter_turnout_label: Optional[str] = Field(None, example="Voted")
    presidential_vote_label: Optional[str] = Field(None, example="Kamala Harris")
    note: Optional[str] = Field(None, example="Demo record created through the Streamlit API form")


def load_original_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    df["source"] = "original_dataset"
    return df


def load_added_records() -> pd.DataFrame:
    if not ADDED_RECORDS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(ADDED_RECORDS_PATH)
    df["source"] = "user_added_record"
    return df


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    try:
        return model.model_dump()
    except AttributeError:
        return model.dict()


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    clean_df = df.where(pd.notna(df), None)
    return clean_df.to_dict(orient="records")


def filter_text_equals(df: pd.DataFrame, column: str, value: Optional[str]) -> pd.DataFrame:
    if value and column in df.columns:
        return df[df[column].astype(str).str.lower() == value.lower()]
    return df


def load_subscribers() -> List[str]:
    if not SUBSCRIBERS_PATH.exists():
        return []

    subscribers = []
    for line in SUBSCRIBERS_PATH.read_text(encoding="utf-8").splitlines():
        chat_id = line.strip()
        if chat_id and chat_id not in subscribers:
            subscribers.append(chat_id)

    return subscribers


def send_update_to_subscribers(text: str) -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return 0

    subscribers = load_subscribers()
    if not subscribers:
        return 0

    sent = 0
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in subscribers:
        try:
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            if response.ok:
                sent += 1
        except requests.RequestException:
            pass

    return sent


@app.get("/records")
def get_records(
    state: Optional[str] = Query(None, description="Filter by state name, for example California"),
    candidate: Optional[str] = Query(None, description="Filter by presidential vote label"),
    age_group: Optional[str] = Query(None, description="Filter by age group, for example 18-29"),
    education_group: Optional[str] = Query(None, description="Filter by education group"),
    gender: Optional[str] = Query(None, description="Filter by gender label"),
    race_ethnicity: Optional[str] = Query(None, description="Filter by race/ethnicity label"),
    income_group: Optional[str] = Query(None, description="Filter by income group"),
    ideology: Optional[str] = Query(None, description="Filter by ideology label"),
    turnout: Optional[str] = Query(None, description="Filter by voter turnout label"),
    min_age: Optional[int] = Query(None, ge=18, description="Minimum respondent age"),
    max_age: Optional[int] = Query(None, le=100, description="Maximum respondent age"),
    include_added: bool = Query(False, description="Include demo records created through POST /records"),
    only_added: bool = Query(False, description="Return only demo records created through POST /records"),
    limit: int = Query(100, ge=1, le=10000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> Dict[str, Any]:
    """Return records from the cleaned dataset, optionally filtered by several parameters."""
    if only_added:
        df = load_added_records()
    else:
        df = load_original_dataset()
        if include_added:
            added = load_added_records()
            if not added.empty:
                df = pd.concat([df, added], ignore_index=True, sort=False)

    if df.empty:
        return {"total_matches": 0, "limit": limit, "offset": offset, "records": []}

    df = filter_text_equals(df, "state_name", state)
    df = filter_text_equals(df, "presidential_vote_label", candidate)
    df = filter_text_equals(df, "age_group", age_group)
    df = filter_text_equals(df, "education_group", education_group)
    df = filter_text_equals(df, "gender_label", gender)
    df = filter_text_equals(df, "race_ethnicity_label", race_ethnicity)
    df = filter_text_equals(df, "income_group", income_group)
    df = filter_text_equals(df, "ideology_label", ideology)
    df = filter_text_equals(df, "voter_turnout_label", turnout)

    if min_age is not None and "age" in df.columns:
        df = df[pd.to_numeric(df["age"], errors="coerce") >= min_age]
    if max_age is not None and "age" in df.columns:
        df = df[pd.to_numeric(df["age"], errors="coerce") <= max_age]

    total_matches = len(df)
    page = df.iloc[offset : offset + limit]

    return {
        "total_matches": int(total_matches),
        "limit": int(limit),
        "offset": int(offset),
        "records": dataframe_to_records(page),
    }


@app.post("/records", status_code=201)
def create_record(record: NewRecord) -> Dict[str, Any]:
    """Create one demo record and save it separately from the original ANES dataset."""
    ADDED_RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing = load_added_records()
    if existing.empty or "added_record_id" not in existing.columns:
        next_id = 1
    else:
        next_id = int(pd.to_numeric(existing["added_record_id"], errors="coerce").max()) + 1

    new_row = {"added_record_id": next_id, **model_to_dict(record)}
    updated = pd.concat([existing.drop(columns=["source"], errors="ignore"), pd.DataFrame([new_row])], ignore_index=True)
    updated.to_csv(ADDED_RECORDS_PATH, index=False)

    notification_lines = ["Database update"]
    for key, value in new_row.items():
        notification_lines.append(f"{key}: {value if value is not None else 'Not specified'}")
    notification_text = "\n".join(notification_lines)
    telegram_notifications_sent = send_update_to_subscribers(notification_text)

    return {
        "message": "Demo record created successfully",
        "record": new_row,
        "saved_to": str(ADDED_RECORDS_PATH),
        "telegram_notifications_sent": telegram_notifications_sent,
    }
