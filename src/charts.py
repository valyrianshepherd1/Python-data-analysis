"""Plotly chart functions."""

from typing import List, Optional

import pandas as pd
import plotly.express as px

from src.data_utils import make_count_df


def plot_count_bar(df: pd.DataFrame, column: str, title: str, x_label: str, top_n: Optional[int] = None):
    count_df = make_count_df(df, column, top_n=top_n)
    count_df[column] = count_df[column].astype(str)
    fig = px.bar(
        count_df,
        x=column,
        y="count",
        title=title,
        labels={column: x_label, "count": "Number of respondents"},
    )
    fig.update_layout(xaxis_tickangle=-30)
    fig.update_traces(marker_line_width=0.8, marker_line_color="white")
    return fig


def plot_percentage_comparison(percentages: pd.DataFrame, title: str, xlabel: str):
    x_col = percentages.index.name or "index"
    plot_df = percentages.reset_index().melt(
        id_vars=x_col,
        var_name="Category",
        value_name="Percentage",
    )
    fig = px.bar(
        plot_df,
        x=x_col,
        y="Percentage",
        color="Category",
        barmode="group",
        title=title,
        labels={x_col: xlabel, "Percentage": "Percentage within group"},
    )
    fig.update_layout(yaxis_range=[0, 100], xaxis_tickangle=-30)
    fig.update_traces(marker_line_width=0.8, marker_line_color="white")
    return fig


def plot_state_choropleth(
    state_summary: pd.DataFrame,
    color_column: str,
    title: str,
    color_label: str,
    color_scale: str = "Blues",
    extra_hover_columns: Optional[List[str]] = None,
    color_midpoint=None,
):
    if extra_hover_columns is None:
        extra_hover_columns = []

    hover_data = {"state_code": False, color_column: ":.2f"}
    for column in extra_hover_columns:
        hover_data[column] = True

    fig = px.choropleth(
        state_summary,
        locations="state_code",
        locationmode="USA-states",
        color=color_column,
        scope="usa",
        hover_name="state_name",
        hover_data=hover_data,
        color_continuous_scale=color_scale,
        color_continuous_midpoint=color_midpoint,
        labels={color_column: color_label},
        title=title,
    )
    fig.update_layout(
        title={"text": title, "x": 0.5, "xanchor": "center"},
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
    )
    return fig


def plot_age_histogram(df: pd.DataFrame):
    fig = px.histogram(
        df.dropna(subset=["age"]),
        x="age",
        nbins=16,
        title="Distribution of Respondent Age",
        labels={"age": "Age", "count": "Number of respondents"},
    )
    fig.update_traces(marker_line_width=1.2, marker_line_color="white", opacity=0.9)
    fig.add_vline(x=df["age"].mean(), line_dash="dash", annotation_text=f"Mean: {df['age'].mean():.1f}")
    fig.add_vline(x=df["age"].median(), line_dash="dot", annotation_text=f"Median: {df['age'].median():.1f}")
    fig.update_layout(bargap=0.05)
    return fig
