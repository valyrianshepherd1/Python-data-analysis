"""Functions that communicate with FastAPI."""

from typing import Dict, Tuple

import requests
import streamlit as st

from src.data_utils import records_to_dataframe


@st.cache_data(ttl=30)
def api_get_records(api_url: str, params_tuple: Tuple[Tuple[str, object], ...]) -> Dict:
    """Call GET /records and return JSON response."""
    params = {key: value for key, value in params_tuple if value not in [None, "", "All"]}
    response = requests.get(f"{api_url.rstrip('/')}/records", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_dataframe_from_api(api_url: str, params: Dict):
    """Return both a dataframe and the original API payload."""
    payload = api_get_records(api_url, tuple(sorted(params.items())))
    df = records_to_dataframe(payload)
    return df, payload


def api_post_record(api_url: str, record: Dict) -> Dict:
    """Call POST /records and clear GET cache so new rows can appear."""
    response = requests.post(f"{api_url.rstrip('/')}/records", json=record, timeout=20)
    response.raise_for_status()
    api_get_records.clear()
    return response.json()
