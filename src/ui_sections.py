"""Streamlit interface sections.

Each function renders one part of the web app.
"""

from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from src.api_client import api_get_records, api_post_record
from src.charts import plot_age_histogram, plot_count_bar, plot_percentage_comparison, plot_state_choropleth
from src.data_utils import (
    add_state_codes,
    explain_stat_value,
    get_major_party_voters,
    interpret_average_ideology,
    make_count_df,
    make_percentage_table,
    records_to_dataframe,
    safe_options,
)
from src.labels import (
    AGE_GROUP_ORDER,
    EDUCATION_GROUP_ORDER,
    GENDER_LABELS,
    IDEOLOGY_LABELS,
    IDEOLOGY_ORDER,
    INCOME_GROUP_ORDER,
    MAJOR_CANDIDATE_ORDER,
    RACE_LABELS,
    SEX_LABELS,
    STATE_CODES,
    TURNOUT_LABELS,
    VOTE_LABELS,
)


def sidebar_select_filter(df: pd.DataFrame, column: str, label: str) -> Optional[str]:
    """Create one selectbox and return selected value or None."""
    options = safe_options(df, column)
    if not options:
        return None
    selected = st.sidebar.selectbox(label, ["All"] + options)
    return None if selected == "All" else selected


def build_api_filter_params(reference_df: pd.DataFrame) -> Dict:
    """Collect sidebar filters and convert them into GET /records parameters."""
    st.sidebar.header("Filters sent to GET /records")
    params = {"include_added": st.sidebar.checkbox("Include user-added demo records"), "limit": 10000, "offset": 0}

    filter_specs = [
        ("state", "state_name", "State"),
        ("candidate", "presidential_vote_label", "Presidential vote"),
        ("gender", "gender_label", "Gender"),
        ("race_ethnicity", "race_ethnicity_label", "Race/ethnicity"),
        ("education_group", "education_group", "Education group"),
        ("income_group", "income_group", "Income group"),
        ("ideology", "ideology_label", "Ideology"),
        ("turnout", "voter_turnout_label", "Turnout"),
    ]
    for api_name, column, label in filter_specs:
        value = sidebar_select_filter(reference_df, column, label)
        if value:
            params[api_name] = value

    if "age" in reference_df.columns and reference_df["age"].notna().any():
        min_age, max_age = int(reference_df["age"].min()), int(reference_df["age"].max())
        age_range = st.sidebar.slider("Age range", min_value=min_age, max_value=max_age, value=(min_age, max_age))
        if age_range[0] != min_age:
            params["min_age"] = age_range[0]
        if age_range[1] != max_age:
            params["max_age"] = age_range[1]

    return params


def render_sidebar_summary(payload: Dict, df: pd.DataFrame) -> None:
    st.sidebar.divider()
    st.sidebar.metric("API total matches", f"{payload.get('total_matches', 0):,}")
    st.sidebar.metric("Rows returned", f"{len(df):,}")


def show_map(fig) -> None:
    """Display all USA maps with the same size and alignment. """
    fig.update_layout(
        height=520,
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        geo=dict(
            scope="usa",
            projection_type="albers usa",
            domain=dict(x=[0.0, 0.82], y=[0.0, 1.0]),
            showland=True,
            landcolor="white",
            bgcolor="white",
        ),
        coloraxis_colorbar=dict(
            x=0.88,
            xanchor="left",
            y=0.5,
            yanchor="middle",
            len=0.78,
            thickness=14,
            tickfont=dict(size=10),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_overview(df: pd.DataFrame) -> None:
    st.header("Project overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{len(df):,}")
    col2.metric("States", f"{df['state_name'].nunique() if 'state_name' in df else 0:,}")
    col3.metric("Median age", f"{df['age'].median():.0f}" if "age" in df else "N/A")
    col4.metric("Turnout rate", f"{df['voter_turnout'].mean() * 100:.1f}%" if "voter_turnout" in df else "N/A")


def render_statistics(df: pd.DataFrame) -> None:
    st.header("Descriptive statistics")
    numeric_cols = [col for col in ["age", "education", "income", "ideology", "voter_turnout"] if col in df.columns]
    stats = df[numeric_cols].agg(["count", "mean", "median", "std", "min", "max"]).T

    for stat_name in ["mean", "median", "min", "max"]:
        stats[f"{stat_name}_interpretation"] = [
            explain_stat_value(variable, stats.loc[variable, stat_name], stat_name)
            for variable in stats.index
        ]
    st.dataframe(stats, use_container_width=True)

    categorical_cols = [
        "state_name", "presidential_vote_label", "voter_turnout_label", "race_ethnicity_label",
        "gender_label", "sex_label", "education_label", "income_group", "ideology_label",
        "pre_election_choice_label",
    ]
    available = [col for col in categorical_cols if col in df.columns]
    selected = st.selectbox("Choose a categorical variable", available)
    st.dataframe(make_count_df(df, selected), use_container_width=True)


def render_basic_visualizations(df: pd.DataFrame) -> None:
    st.header("Basic visualizations")
    if "age" in df.columns:
        st.plotly_chart(plot_age_histogram(df), use_container_width=True)

    plot_specs = [
        ("education_label", "Distribution of Education Levels", "Education level", None),
        ("income", "Distribution of Household Income Category Codes", "Income category code", None),
        ("ideology_label", "Distribution of Political Ideology", "Ideology", None),
        ("voter_turnout_label", "Distribution of Voter Turnout", "Turnout", None),
        ("race_ethnicity_label", "Distribution of Race/Ethnicity", "Race/ethnicity", None),
        ("gender_label", "Distribution of Gender", "Gender", None),
        ("sex_label", "Distribution of Sex", "Sex", None),
        ("pre_election_choice_label", "Distribution of Pre-Election Presidential Choice", "Pre-election choice", None),
        ("state_name", "Top 10 States by Number of Respondents", "State", 10),
    ]
    for column, title, label, top_n in plot_specs:
        if column in df.columns:
            st.plotly_chart(plot_count_bar(df, column, title, label, top_n), use_container_width=True)


def render_detailed_overview(df: pd.DataFrame) -> None:
    st.header("Detailed overview")
    df_voters, df_major = get_major_party_voters(df)
    st.metric("Rows with valid presidential vote", f"{len(df_voters):,}")
    st.metric("Rows with major-party presidential vote", f"{len(df_major):,}")

    comparisons = [
        ("race_ethnicity_label", "Major-Party Presidential Vote by Race/Ethnicity", "Race/ethnicity", list(RACE_LABELS.values())),
        ("gender_label", "Major-Party Presidential Vote by Gender", "Gender", list(GENDER_LABELS.values())),
        ("sex_label", "Major-Party Presidential Vote by Sex", "Sex", list(SEX_LABELS.values())),
        ("education_group", "Major-Party Presidential Vote by Education Group", "Education group", EDUCATION_GROUP_ORDER),
        ("ideology_label", "Major-Party Presidential Vote by Ideology", "Ideology", IDEOLOGY_ORDER),
    ]
    for group_col, title, xlabel, order in comparisons:
        if group_col in df_major.columns and not df_major.empty:
            st.subheader(title)
            _, pct = make_percentage_table(df_major, group_col, "presidential_vote_label", order, MAJOR_CANDIDATE_ORDER)
            st.dataframe(pct.round(2), use_container_width=True)
            st.plotly_chart(plot_percentage_comparison(pct, title, xlabel), use_container_width=True)

    for group_col, title, order in [
        ("age_group", "Voter Turnout by Age Group", AGE_GROUP_ORDER),
        ("income_group", "Voter Turnout by Income Group", INCOME_GROUP_ORDER),
    ]:
        if {group_col, "voter_turnout_label"}.issubset(df.columns):
            st.subheader(title)
            _, pct = make_percentage_table(df, group_col, "voter_turnout_label", order, ["Did not vote", "Voted"])
            st.dataframe(pct.round(2), use_container_width=True)
            st.plotly_chart(plot_percentage_comparison(pct, title, group_col.replace("_", " ")), use_container_width=True)

    if {"pre_election_choice_label", "presidential_vote_label"}.issubset(df.columns):
        st.subheader("Actual presidential vote by pre-election choice")
        table = pd.crosstab(df["pre_election_choice_label"], df["presidential_vote_label"], normalize="index") * 100
        st.dataframe(table.round(2), use_container_width=True)
        fig = px.imshow(table, text_auto=".1f", aspect="auto", title="Actual Presidential Vote by Pre-Election Choice")
        st.plotly_chart(fig, use_container_width=True)


def render_maps(df: pd.DataFrame) -> None:
    st.header("Choropleth maps")
    minimum = st.slider("Minimum respondents per state for rate maps", 10, 100, 30, 5)

    if "state_name" in df.columns:
        sample = df.groupby("state_name", observed=True).size().reset_index(name="respondent_count")
        sample["respondent_share_pct"] = sample["respondent_count"] / len(df) * 100
        sample = add_state_codes(sample)
        show_map(plot_state_choropleth(sample, "respondent_count", "Number of Respondents by State", "Respondents", "Blues", ["respondent_share_pct"]))

    if {"state_name", "voter_turnout"}.issubset(df.columns):
        turnout = df.dropna(subset=["state_name", "voter_turnout"]).groupby("state_name", observed=True).agg(
            respondent_count=("state_name", "size"), turnout_rate_pct=("voter_turnout", lambda x: x.mean() * 100)
        ).reset_index()
        turnout = add_state_codes(turnout[turnout["respondent_count"] >= minimum])
        show_map(plot_state_choropleth(turnout, "turnout_rate_pct", "Reported Voter Turnout Rate by State", "Turnout rate (%)", "Greens", ["respondent_count"]))

    _, df_major = get_major_party_voters(df)
    if {"state_name", "presidential_vote_label"}.issubset(df_major.columns) and not df_major.empty:
        vote = df_major.groupby(["state_name", "presidential_vote_label"], observed=True).size().unstack(fill_value=0)
        for candidate in MAJOR_CANDIDATE_ORDER:
            if candidate not in vote.columns:
                vote[candidate] = 0
        vote["major_party_respondents"] = vote["Kamala Harris"] + vote["Donald Trump"]
        vote["harris_share_pct"] = vote["Kamala Harris"] / vote["major_party_respondents"] * 100
        vote["trump_share_pct"] = vote["Donald Trump"] / vote["major_party_respondents"] * 100
        vote["harris_minus_trump_pct"] = vote["harris_share_pct"] - vote["trump_share_pct"]
        vote = add_state_codes(vote.reset_index())
        vote = vote[vote["major_party_respondents"] >= 20]
        show_map(plot_state_choropleth(vote, "harris_minus_trump_pct", "Major-Party Vote Balance by State", "Harris minus Trump", "RdBu", ["major_party_respondents", "harris_share_pct", "trump_share_pct"], 0))

    if {"state_name", "ideology"}.issubset(df.columns):
        ideology = df.dropna(subset=["state_name", "ideology"]).groupby("state_name", observed=True).agg(
            respondent_count=("state_name", "size"), average_ideology=("ideology", "mean")
        ).reset_index()
        ideology = ideology[ideology["respondent_count"] >= minimum]
        ideology["average_ideology_text"] = ideology["average_ideology"].apply(interpret_average_ideology)
        ideology = add_state_codes(ideology)
        fig = px.choropleth(
            ideology,
            locations="state_code",
            locationmode="USA-states",
            color="average_ideology",
            scope="usa",
            hover_name="state_name",
            color_continuous_scale="RdBu_r",
            range_color=(1, 7),
            title="Average Ideology by State",
        )
        fig.update_traces(customdata=ideology[["average_ideology_text", "respondent_count", "average_ideology"]], hovertemplate="<b>%{hovertext}</b><br>Average ideology: %{customdata[0]}<br>Average ideology code: %{customdata[2]:.2f}<br>Respondents: %{customdata[1]}<extra></extra>")
        fig.update_layout(coloraxis_colorbar=dict(title="Average ideology", tickmode="array", tickvals=list(IDEOLOGY_LABELS.keys()), ticktext=list(IDEOLOGY_LABELS.values())))
        show_map(fig)

    if {"state_name", "age"}.issubset(df.columns):
        age = df.dropna(subset=["state_name", "age"]).groupby("state_name", observed=True).agg(
            respondent_count=("state_name", "size"), average_age=("age", "mean")
        ).reset_index()
        age = add_state_codes(age[age["respondent_count"] >= minimum])
        show_map(plot_state_choropleth(age, "average_age", "Average Respondent Age by State", "Average age", "Viridis", ["respondent_count"]))


def render_hypotheses(df: pd.DataFrame) -> None:
    st.header("Hypothesis checking")
    st.subheader("Hypothesis 1: age, income, and turnout")
    st.write("Reported voter turnout is higher among older respondents, especially in higher income groups.")
    if {"age_group", "income_group", "voter_turnout"}.issubset(df.columns):
        table = df.dropna(subset=["age_group", "income_group", "voter_turnout"]).groupby(
            ["age_group", "income_group"], observed=True
        )["voter_turnout"].mean().mul(100).unstack().reindex(index=AGE_GROUP_ORDER, columns=INCOME_GROUP_ORDER)
        st.dataframe(table.round(2), use_container_width=True)
        st.plotly_chart(px.imshow(table, text_auto=".1f", aspect="auto", title="Reported Voter Turnout by Age Group and Income Group", zmin=0, zmax=100), use_container_width=True)

    st.subheader("Hypothesis 2: education, ideology, and presidential vote")
    _, df_major = get_major_party_voters(df)
    if not df_major.empty and {"education_group", "ideology_label", "presidential_vote_label"}.issubset(df_major.columns):
        data = df_major.dropna(subset=["education_group", "ideology_label", "presidential_vote_label"])
        for candidate in MAJOR_CANDIDATE_ORDER:
            share = data.assign(voted_candidate=(data["presidential_vote_label"] == candidate).astype(int)).groupby(
                ["ideology_label", "education_group"], observed=True
            )["voted_candidate"].mean().mul(100).unstack().reindex(index=IDEOLOGY_ORDER, columns=EDUCATION_GROUP_ORDER)
            st.write(f"{candidate} vote share by ideology and education group")
            st.dataframe(share.round(2), use_container_width=True)
            long = share.reset_index().melt(id_vars="ideology_label", var_name="Education group", value_name="Vote share")
            fig = px.line(long, x="ideology_label", y="Vote share", color="Education group", markers=True, title=f"{candidate} Vote Share by Ideology and Education Group")
            fig.update_layout(yaxis_range=[0, 100], xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)


def render_api_manual(api_url: str) -> None:
    st.header("Manual FastAPI interface")

    st.subheader("GET /records")
    with st.form("manual_get_records"):
        col1, col2, col3 = st.columns(3)
        get_state = col1.selectbox("state", [""] + sorted(STATE_CODES.values()))
        get_candidate = col2.selectbox("candidate", [""] + list(VOTE_LABELS.values()))
        get_age_group = col3.selectbox("age_group", [""] + AGE_GROUP_ORDER)

        col4, col5, col6 = st.columns(3)
        get_education = col4.selectbox("education_group", [""] + EDUCATION_GROUP_ORDER)
        get_gender = col5.selectbox("gender", [""] + list(GENDER_LABELS.values()))
        get_race = col6.selectbox("race_ethnicity", [""] + list(RACE_LABELS.values()))

        col7, col8, col9 = st.columns(3)
        get_income = col7.selectbox("income_group", [""] + INCOME_GROUP_ORDER)
        get_ideology = col8.selectbox("ideology", [""] + IDEOLOGY_ORDER)
        get_turnout = col9.selectbox("turnout", [""] + list(TURNOUT_LABELS.values()))

        col10, col11, col12, col13 = st.columns(4)
        get_min_age = col10.number_input("min_age", min_value=18, max_value=100, value=18)
        get_max_age = col11.number_input("max_age", min_value=18, max_value=100, value=100)
        get_limit = col12.number_input("limit", min_value=1, max_value=10000, value=10)
        get_offset = col13.number_input("offset", min_value=0, value=0)

        col14, col15 = st.columns(2)
        get_include_added = col14.checkbox("include_added", value=False)
        get_only_added = col15.checkbox("only_added", value=False)

        submitted_get = st.form_submit_button("Send GET request")

    if submitted_get:
        manual_params = {
            "state": get_state,
            "candidate": get_candidate,
            "age_group": get_age_group,
            "education_group": get_education,
            "gender": get_gender,
            "race_ethnicity": get_race,
            "income_group": get_income,
            "ideology": get_ideology,
            "turnout": get_turnout,
            "min_age": get_min_age if get_min_age != 18 else None,
            "max_age": get_max_age if get_max_age != 100 else None,
            "include_added": get_include_added,
            "only_added": get_only_added,
            "limit": int(get_limit),
            "offset": int(get_offset),
        }
        manual_params = {key: value for key, value in manual_params.items() if value not in [None, ""]}
        try:
            result = api_get_records(api_url, tuple(sorted(manual_params.items())))
            st.success("GET request succeeded")
            st.json(result)
            st.dataframe(records_to_dataframe(result), use_container_width=True)
        except requests.RequestException as error:
            st.error("GET request failed")
            st.exception(error)

    st.subheader("POST /records")
    st.write("This creates a demo record and saves it separately from the original ANES dataset.")
    with st.form("manual_post_record"):
        col1, col2 = st.columns(2)
        post_state = col1.selectbox("State name", sorted(STATE_CODES.values()), index=sorted(STATE_CODES.values()).index("California"))
        post_age = col2.number_input("Age", min_value=18, max_value=100, value=35)

        col3, col4, col5 = st.columns(3)
        post_gender = col3.selectbox("Gender", ["", "Man", "Woman", "Non-binary", "Another gender"])
        post_sex = col4.selectbox("Sex", ["", "Male", "Female"])
        post_turnout = col5.selectbox("Turnout", ["", "Voted", "Did not vote"])

        col6, col7 = st.columns(2)
        post_race = col6.selectbox("Race/ethnicity", [""] + list(RACE_LABELS.values()))
        post_education = col7.selectbox("Education group", [""] + EDUCATION_GROUP_ORDER)

        col8, col9 = st.columns(2)
        post_income = col8.selectbox("Income group", [""] + INCOME_GROUP_ORDER)
        post_ideology = col9.selectbox("Ideology", [""] + IDEOLOGY_ORDER)

        post_vote = st.selectbox("Presidential vote", [""] + list(VOTE_LABELS.values()))
        post_note = st.text_area("Note", value="Demo record created from the Streamlit API tab")
        submitted_post = st.form_submit_button("Send POST request")

    if submitted_post:
        new_record = {
            "state_name": post_state,
            "age": int(post_age),
            "gender_label": post_gender or None,
            "sex_label": post_sex or None,
            "race_ethnicity_label": post_race or None,
            "education_group": post_education or None,
            "income_group": post_income or None,
            "ideology_label": post_ideology or None,
            "voter_turnout_label": post_turnout or None,
            "presidential_vote_label": post_vote or None,
            "note": post_note or None,
        }
        try:
            result = api_post_record(api_url, new_record)
            st.success("POST request succeeded. The new demo record was saved by FastAPI.")
            st.json(result)
            st.info("To see this row in GET results, use include_added=True or only_added=True.")
        except requests.RequestException as error:
            st.error("POST request failed")
            st.exception(error)

def render_data_tab(df: pd.DataFrame) -> None:
    st.header("Data preview")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data as CSV", data=csv, file_name="filtered_anes_2024_data.csv", mime="text/csv")
