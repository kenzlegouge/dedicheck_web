import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime
from daily_updater import start_daily_updater, CSV_PATH

st.set_page_config(page_title="Player Progress", layout="wide")

# --- Start daily updater once ---
if "daily_updater_started" not in st.session_state:
    start_daily_updater(interval_hours=24)
    st.session_state["daily_updater_started"] = True

st.title("📈 Player Point Progression Over Time")

# --- Load Data ---
@st.cache_data(ttl=3600 * 6)
def load_points():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, parse_dates=["recorded_at"])
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        return df
    else:
        st.warning("No data available yet. Please wait for first sync.")
        return pd.DataFrame()

@st.cache_data
def load_teams():
    path = "./resources/teams.csv"
    if os.path.exists(path):
        return pd.read_csv(path, sep = "\t", engine="python")
    else:
        st.warning("⚠️ No teams.csv found — teams will not be displayed.")
        return pd.DataFrame(columns=["Login", "Team"])

df = load_points()
teams_df = load_teams()

if df.empty:
    st.stop()

# --- Merge teams ---
df = df.merge(teams_df, how="left", left_on="login", right_on="Login")
df["Team"] = df["Team"].fillna("No team")
df = df.drop_duplicates()
# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Team selection
teams = sorted(df["Team"].unique())
selected_teams = st.sidebar.multiselect("Select teams", teams, default=teams[:3])

# Filter by team
df_team = df[df["Team"].isin(selected_teams)]

# Manual login addition
manual_login = st.sidebar.text_input("Add player by Login (case-sensitive)")
if manual_login:
    extra_player = df[df["login"].str.lower() == manual_login.lower()]
    if not extra_player.empty:
        st.sidebar.success(f"✅ Added {extra_player['nickname'].iloc[-1]}")
        df_team = pd.concat([df_team, extra_player])
    else:
        st.sidebar.error(f"❌ No player found with login '{manual_login}'")

# --- Date range filter ---
date_min, date_max = df["recorded_at"].min(), df["recorded_at"].max()
date_range = st.sidebar.slider(
    "Select date range",
    min_value=date_min.to_pydatetime(),
    max_value=date_max.to_pydatetime(),
    value=(date_min.to_pydatetime(), date_max.to_pydatetime()),
)

df_filtered = df_team[df_team["recorded_at"].between(*date_range)]

if df_filtered.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# --- Ensure unique color by login, display nickname ---
df_filtered["display_label"] = df_filtered.apply(
    lambda r: f"{r['nickname']} ({r['login']})", axis=1
)

# --- Chart 1: Total Score Over Time ---
chart1 = (
    alt.Chart(df_filtered)
    .mark_line(point=True)
    .encode(
        x=alt.X("recorded_at:T", title="Date"),
        y=alt.Y("score:Q", title="Total Points"),
        color=alt.Color("display_label:N", legend=alt.Legend(title="Player")),
        tooltip=[
            "nickname",
            "login",
            "Team",
            alt.Tooltip("score:Q", format=".2f"),
            alt.Tooltip("recorded_at:T", title="Date"),
        ],
    )
    .properties(height=450, title="Total Points Over Time")
)

st.altair_chart(chart1, use_container_width=True)

# --- Chart 2: Daily Differential (ΔPoints) ---
# Compute daily difference per player
# 1️⃣ Ensure recorded_at is datetime
df_filtered["recorded_at"] = pd.to_datetime(df_filtered["recorded_at"], errors="coerce")
print(f"df", {df_filtered.shape[0]})
print(df_filtered)
# 3️⃣ Compute day-by-day difference per player
df_diff = (
    df_filtered
    .sort_values(["login", "recorded_at"])
    .groupby("login", group_keys=False)
    .apply(lambda g: g.assign(diff=g["score"].diff()))
    .dropna(subset=["diff"])
)

print(df_diff.shape[0])

# 4️⃣ Clean up
df_diff["recorded_at"] = pd.to_datetime(df_diff["recorded_at"])

chart2 = (
    alt.Chart(df_diff.dropna(subset=["diff"]))
    .mark_line(point=True)
    .encode(
        x=alt.X("recorded_at:T", title="Date"),
        y=alt.Y("diff:Q", title="Δ Points (Daily Change)"),
        color=alt.Color("display_label:N", legend=alt.Legend(title="Player")),
        tooltip=[
            "nickname",
            "login",
            "Team",
            alt.Tooltip("diff:Q", format="+.2f", title="Δ Points"),
            alt.Tooltip("recorded_at:T", title="Date"),
        ],
    )
    .properties(height=350, title="Daily Point Differential (Δ)")
)

st.altair_chart(chart2, use_container_width=True)

# --- Footer Info ---
st.caption(
    f"💾 Data source: player_daily_scores (updated daily) • "
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
