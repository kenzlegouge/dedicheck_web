# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 14:24:38 2025

@author: Hola
"""

import streamlit as st
import pandas as pd
from renders import render_html_table
from app import load_data
from score import assign_team_from_nickname, assign_points

st.set_page_config(page_title="Team Rankings", layout="wide")
st.title("👥 Team Rankings")


# Load player and team data
uploaded = True


if uploaded:
    df = load_data("./resources/dedimania_all_records.csv")

teams_df = pd.read_csv("./resources/teams.csv", sep = "\t", engine="python")
teams_df.columns = teams_df.columns.str.strip().str.lower()

# Merge
df["Login"] = df["Login"].str.lower()
teams_df["login"] = teams_df["login"].str.lower()
teams_df = teams_df.drop_duplicates(subset="login")

df["Score"] = df['Rank'].apply(assign_points)

merged = pd.merge(df, teams_df, how="left", left_on="Login", right_on = "login")

print(merged.head(10))

# Example scoring: 1st place = 10 pts, 2nd = 8, 3rd = 6, 4th = 5, 5th = 4...

# Compute total team score
team_scores = (
    merged.groupby("team", dropna=True)["Score"]
    .sum()
    .reset_index()
    .sort_values("Score", ascending=False)
)
team_scores.Score = team_scores.Score.astype(int)

# Render Team Score Table
st.markdown(render_html_table("🏆 Team Total Scores",team_scores, ["team", "Score"]), unsafe_allow_html=True)

# Render Top 5 Players from Top 4 Teams
st.markdown("### 👥 Top Players from Top 4 Teams")

top_4_teams = team_scores.head(4)["team"].dropna().tolist()
cols = st.columns(len(top_4_teams))

for i, team in enumerate(top_4_teams):
    team_data = merged[merged["team"] == team]
    top_players = (
        team_data.groupby("NickName")["Score"]
        .sum()
        .reset_index()
        .sort_values("Score", ascending=False)
        .head(5)
    )
    top_players.Score = top_players.Score.astype(int)
    
    # Show inside the column
    with cols[i]:
       st.markdown(render_html_table(f"{i+1} : {team}",top_players, ["NickName", "Score"]), unsafe_allow_html=True)
