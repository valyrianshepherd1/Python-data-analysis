"""Small dataframe helper functions used by the web app."""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.labels import (
    AGE_GROUP_ORDER,
    EDUCATION_GROUP_ORDER,
    EDUCATION_LABELS,
    GENDER_LABELS,
    IDEOLOGY_LABELS,
    INCOME_GROUP_ORDER,
    INCOME_LABELS,
    MAJOR_CANDIDATE_ORDER,
    PRE_CHOICE_PARTY_LABELS,
    RACE_LABELS,
    SEX_LABELS,
    STATE_ABBREVIATIONS,
    STATE_CODES,
    TURNOUT_LABELS,
    VOTE_LABELS,
)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add labels and derived columns if they are not already present."""
    df = df.copy()

    numeric_columns = [
        "state", "presidential_vote", "voter_turnout", "pre_election_presidential_choice",
        "age", "education", "race_ethnicity", "sex", "gender", "income", "ideology",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    label_rules = [
        ("state_name", "state", STATE_CODES),
        ("presidential_vote_label", "presidential_vote", VOTE_LABELS),
        ("voter_turnout_label", "voter_turnout", TURNOUT_LABELS),
        ("education_label", "education", EDUCATION_LABELS),
        ("race_ethnicity_label", "race_ethnicity", RACE_LABELS),
        ("sex_label", "sex", SEX_LABELS),
        ("gender_label", "gender", GENDER_LABELS),
        ("income_label", "income", INCOME_LABELS),
        ("ideology_label", "ideology", IDEOLOGY_LABELS),
        ("pre_election_choice_label", "pre_election_presidential_choice", PRE_CHOICE_PARTY_LABELS),
    ]
    for new_column, source_column, labels in label_rules:
        if new_column not in df.columns and source_column in df.columns:
            df[new_column] = df[source_column].map(labels)

    if "age_group" not in df.columns and "age" in df.columns:
        df["age_group"] = pd.cut(
            df["age"],
            bins=[17, 29, 44, 64, np.inf],
            labels=AGE_GROUP_ORDER,
        ).astype("object")

    if "education_group" not in df.columns and "education" in df.columns:
        df["education_group"] = np.select(
            [df["education"].isin([1, 2, 3]), df["education"].eq(4), df["education"].eq(5)],
            EDUCATION_GROUP_ORDER,
            default=np.nan,
        )

    if "income_group" not in df.columns and "income" in df.columns:
        df["income_group"] = pd.cut(
            df["income"],
            bins=[0, 14, 22, 28],
            labels=INCOME_GROUP_ORDER,
            include_lowest=True,
        ).astype("object")

    if "major_party_vote" not in df.columns and "presidential_vote_label" in df.columns:
        df["major_party_vote"] = np.select(
            [
                df["presidential_vote_label"].eq("Kamala Harris"),
                df["presidential_vote_label"].eq("Donald Trump"),
            ],
            ["Democratic", "Republican"],
            default=np.nan,
        )

    return df


def records_to_dataframe(payload: Dict) -> pd.DataFrame:
    """Convert API JSON response into a prepared dataframe."""
    records = payload.get("records", [])
    if not records:
        return pd.DataFrame()
    return prepare_dataframe(pd.DataFrame(records))


def safe_options(df: pd.DataFrame, column: str) -> List[str]:
    """Return sorted values for a Streamlit selectbox."""
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().astype(str).unique().tolist())


def make_count_df(df: pd.DataFrame, column: str, top_n: Optional[int] = None) -> pd.DataFrame:
    counts = df[column].value_counts(dropna=False)
    if top_n is not None:
        counts = counts.head(top_n)
    return counts.rename_axis(column).reset_index(name="count")


def make_percentage_table(
    data: pd.DataFrame,
    group_col: str,
    outcome_col: str,
    group_order: Optional[List[str]] = None,
    outcome_order: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create count and row-percentage crosstabs."""
    subset = data.dropna(subset=[group_col, outcome_col]).copy()
    counts = pd.crosstab(subset[group_col], subset[outcome_col])
    percentages = pd.crosstab(subset[group_col], subset[outcome_col], normalize="index") * 100

    if group_order is not None:
        existing_groups = [group for group in group_order if group in percentages.index]
        counts = counts.reindex(existing_groups)
        percentages = percentages.reindex(existing_groups)

    if outcome_order is not None:
        existing_outcomes = [outcome for outcome in outcome_order if outcome in percentages.columns]
        counts = counts[existing_outcomes]
        percentages = percentages[existing_outcomes]

    return counts, percentages


def add_state_codes(state_summary: pd.DataFrame) -> pd.DataFrame:
    state_summary = state_summary.copy()
    state_summary["state_code"] = state_summary["state_name"].map(STATE_ABBREVIATIONS)
    return state_summary.dropna(subset=["state_code"])


def get_major_party_voters(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_voters = df.dropna(subset=["presidential_vote_label"]).copy()
    df_major = df_voters[df_voters["presidential_vote_label"].isin(MAJOR_CANDIDATE_ORDER)].copy()
    return df_voters, df_major


def interpret_average_ideology(value: float) -> str:
    if pd.isna(value):
        return "Missing"
    if value <= 1.5:
        return "Extremely liberal / liberal"
    if value <= 2.5:
        return "Liberal"
    if value <= 3.5:
        return "Slightly liberal"
    if value <= 4.5:
        return "Moderate"
    if value <= 5.5:
        return "Slightly conservative"
    if value <= 6.5:
        return "Conservative"
    return "Extremely conservative"


def explain_stat_value(variable: str, value: float, stat_name: str) -> str:
    label_maps = {
        "education": EDUCATION_LABELS,
        "income": INCOME_LABELS,
        "ideology": IDEOLOGY_LABELS,
        "voter_turnout": TURNOUT_LABELS,
    }

    if pd.isna(value):
        return "Missing"
    if variable == "age":
        return f"{value:.1f} years old" if stat_name in ["mean", "median"] else f"{value:.0f} years old"
    if variable == "voter_turnout" and stat_name == "mean":
        return f"{value:.1%} of respondents voted"

    labels = label_maps.get(variable)
    if labels is None:
        return "No label available"
    if value == int(value):
        return labels.get(int(value), "Unknown code")

    lower = int(np.floor(value))
    upper = int(np.ceil(value))
    return f"Average code {value:.2f}, between '{labels.get(lower, 'Unknown')}' and '{labels.get(upper, 'Unknown')}'"
