"""Main Streamlit file.
"""

import os

import requests
import streamlit as st

from src.api_client import api_get_records, fetch_dataframe_from_api
from src.data_utils import records_to_dataframe
from src.ui_sections import (
    build_api_filter_params,
    render_api_manual,
    render_basic_visualizations,
    render_data_tab,
    render_detailed_overview,
    render_hypotheses,
    render_maps,
    render_overview,
    render_sidebar_summary,
    render_statistics,
)


st.set_page_config(
    page_title="ANES 2024 Election Analysis",
    page_icon="🗳️",
    layout="wide",
)

API_DEFAULT_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.title("ANES 2024 Election Analysis")

api_base_url = st.sidebar.text_input("API base URL", value=API_DEFAULT_URL)

# 1. Load reference data from FastAPI.
try:
    reference_payload = api_get_records(
        api_base_url,
        tuple(sorted({"limit": 10000, "offset": 0}.items())),
    )
    reference_df = records_to_dataframe(reference_payload)
except requests.RequestException as error:
    st.error("Could not connect to FastAPI. Start it first, then reload this page.")
    st.code("python -m uvicorn api.main:app --reload")
    st.exception(error)
    st.stop()

if reference_df.empty:
    st.error("The API returned no records. Check that the cleaned CSV exists.")
    st.stop()

# 2. Build sidebar filters and ask FastAPI for filtered data.
api_params = build_api_filter_params(reference_df)
try:
    df_analysis, filtered_payload = fetch_dataframe_from_api(api_base_url, api_params)
except requests.RequestException as error:
    st.error("The filtered API request failed. Check the FastAPI terminal for details.")
    st.exception(error)
    st.stop()

if df_analysis.empty:
    st.warning("No rows match the selected API filters. Clear some filters to see the analysis.")
    st.stop()

render_sidebar_summary(filtered_payload, df_analysis)

# 3. Render the app sections.
tabs = st.tabs([
    "Overview",
    "Statistics",
    "Basic visualizations",
    "Detailed overview",
    "Maps",
    "Hypotheses",
    "API manual interface",
    "Data",
])

with tabs[0]:
    render_overview(df_analysis)
with tabs[1]:
    render_statistics(df_analysis)
with tabs[2]:
    render_basic_visualizations(df_analysis)
with tabs[3]:
    render_detailed_overview(df_analysis)
with tabs[4]:
    render_maps(df_analysis)
with tabs[5]:
    render_hypotheses(df_analysis)
with tabs[6]:
    render_api_manual(api_base_url)
with tabs[7]:
    render_data_tab(df_analysis)
