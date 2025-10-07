# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 23:00:18 2025

@author: Hola
"""

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from renders import render_html_table, render_score_table,top_border, time_ago
from score import scoring_function
from fetcher import start_background_thread, latest_df, last_updated

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    page_title="Dodo challenge Viewer",
    page_icon="🏁",
    layout="wide",
)

# Dark theme styling
st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stDataFrame {background-color: #0e1117 !important;}
    table, th, td {
        color: #fafafa !important;
        border-color: #444 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# LOAD DATA
# ---------------------------


start_background_thread()



@st.cache_data(ttl=3600)
def load_data(path):
    # If available, use latest data; otherwise load cached CSV
    if latest_df is not None:
        df = latest_df.copy()
    else:
        df = pd.read_csv("./resources/dedimania_all_records.csv")
    
    df["Record"] = pd.to_numeric(df["Record"], errors="coerce")
    # Try to parse date
    df["RecordDate"] = pd.to_datetime(df["RecordDate"], errors="coerce", dayfirst=True)
    df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')

    df = df.dropna(subset=["RecordDate"])
    return df

uploaded = True


if uploaded:
    df = load_data("./resources/dedimania_all_records.csv")
    
    # --- Data preparation ---
    df["RecordDate"] = pd.to_datetime(df["RecordDate"], format="%d/%m/%Y %H:%M")
    df["Record"] = pd.to_numeric(df["Record"], errors="coerce")

    # --- Top 5 recent records ---
    recent_records = df.sort_values("RecordDate", ascending=False).head(100)[
        ["Challenge", "NickName", "Record", "Rank", "RecordDate"]
    ]
    recent_records = recent_records.copy()
    recent_records["RecordDate"] = recent_records["RecordDate"].apply(time_ago)

    # --- Most disputed maps ---
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_df = df[df["RecordDate"] >= seven_days_ago]
    recent_df = recent_df.copy()
    recent_df["RecordDate"] = recent_df["RecordDate"].apply(time_ago)
    active_maps = (
    recent_df.groupby(["Challenge"])
    .size()
    .reset_index(name="NewRecords")
    .sort_values("NewRecords", ascending=False)
    .head(10)
    )

    # --- Player most records ---
       
    player_most_records = (
    df.groupby(["NickName", "Login"])
    .size()
    .reset_index(name="MostRecords")
    .sort_values("MostRecords", ascending=False)
    .head(10)
    )
    
    # --- Top players (best record overall) ---
    top_players = (
        df[df["Rank"].astype(float) == 1]
        .groupby(["Login", "NickName"])
        .size()
        .reset_index(name="Top1_Count")
        .sort_values("Top1_Count", ascending=False)
        .head(10)
    )

    # --- Page Title ---
    st.markdown("## 🏁 Dodo challenge leaderboard")
    # Little gadget at the top
    top_border(df) 
    
    
    col1, col2 = st.columns([2, 1], gap="large")


    
    # === LEFT: Top 5 Recent Records ===
    with col1:
        st.markdown("### 🕒 Latest records")

        # ✅ Combine CSS + HTML inside components.html
        html = """
        <html>
        <head>
        <style>
        body {
            background-color: transparent;
            color: #e6edf3;
            font-family: 'Segoe UI', Roboto, sans-serif;
        }
        .records-box {
            background: linear-gradient(145deg, #1a1d25, #11141a);
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            padding: 1.2em;
            margin-top: 0.5em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            text-align: left;
            padding: 0.5em;
            color: #8b949e;
            border-bottom: 1px solid #2d313a;
            font-size: 0.9em;
        }
        td {
            padding: 0.6em;
            border-bottom: 1px solid #2d313a;
            font-size: 0.95em;
        }
        tr:hover {
            background-color: rgba(88,166,255,0.08);
            transition: background 0.2s ease;
        }
        .nickname { color: #58a6ff; font-weight: 600; }
        .record { color: #3fb950; font-weight: 600; }
        .rank { color: #f1c40f; font-weight: 600; }
        </style>
        </head>
        <body>
        <div class="records-box">
            <table>
                <thead>
                    <tr>
                        <th>Challenge</th>
                        <th>Nickname</th>
                        <th>Record</th>
                        <th>Rank</th>
                        <th>Set on</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add rows dynamically
        for _, row in recent_records.iterrows():
            html += f"""
                <tr>
                    <td>{row['Challenge']}</td>
                    <td class="nickname">{row['NickName']}</td>
                    <td class="record">{row['Record']:.2f}</td>
                    <td class="rank">{int(row['Rank'])}</td>
                    <td>{row['RecordDate']}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        </body></html>
        """

        # ✅ Render styled HTML table
        components.html(html, height=400, scrolling=True)

    ## === RIGHT: Top Players by Top-1 Finishes ===
    with col2:
        components.html(render_html_table("🥇 Top Players by #1 Ranks", top_players, columns=["NickName", "Top1_Count"]), height=400, scrolling=True)

        
    col3, col4 = st.columns([1, 1], gap="medium")

    # === LEFT: Top 5 Recent Records ===
    with col3:
        components.html(render_html_table("🔥 Most Active Maps (Last 7 Days)", active_maps, columns=["Challenge", "NewRecords"]), height=400, scrolling=True)
    
    with col4:
        components.html(render_html_table("🔥 Top dedi presence", player_most_records, columns=["NickName", "Login", "MostRecords"]), height=400, scrolling=True)
        
    components.html(render_score_table("🔥 Solo Leaderboards", scoring_function(df), columns=['NickName', 'Points', 'Maps_Played', 'Average_Rank', 'Login']), height=800, scrolling=True)
