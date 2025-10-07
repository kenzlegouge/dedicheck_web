# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 08:57:04 2025

@author: Hola
"""

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta, timezone

# Load teams safely
TEAMS_PATH = "./resources/teams.csv"
teams_df = pd.read_csv(TEAMS_PATH, sep = "\t", engine="python")
teams_map = dict(zip(teams_df["Login"], teams_df["Team"]))

# Define colors for known teams
TEAM_COLORS = {
    "ĊĦ »": "#1f77b4",   # Blue
    "ѕнιғт": "#ff7f0e",  # Orange
    "LeG": "#2ca02c",    # Green
    "нот": "#d62728",    # Red
    "Јғғ": "#9467bd",    # Purple
    "Сяс": "#8c564b",    # Brown
    "הѕс": "#e377c2",    # Pink
    "»тят": "#7f7f7f",   # Gray
    "νѕρ": "#bcbd22",    # Yellow-green
    "ғฟ๏": "#17becf",    # Teal
    "ѕωα": "#1a55FF",    # Strong Blue
    "Law": "#FF1493",    # Deep Pink
    "4W : : ": "#FFD700",# Gold
    "nsc": "#A52A2A",    # Dark Red
    "»ЯтА": "#228B22",   # Forest Green
    "ωаѕρ .": "#DAA520", # Goldenrod
    "ғаιהτ.": "#00CED1", # Dark Turquoise
    "sigN": "#DC143C",   # Crimson
    "GC l|": "#4682B4",  # Steel Blue
    "kings": "#800000",  # Maroon
}

def render_html_table(title: str, df, columns: list[str]):
    """
    Render a styled HTML table inside Streamlit, using the dark leaderboard theme.
    
    Args:
        title (str): Section title (e.g., "Top Players by #1 Ranks")
        df (pd.DataFrame): The dataframe to render.
        columns (list[str]): Column names (in the order they should appear).
    """

    st.markdown(f"### {title}")

    html = """
    <html>
    <head>
    <style>
    body {
        background-color: transparent;
        color: #e6edf3;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .table-box {
        background: linear-gradient(145deg, #1a1d25, #11141a);
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        padding: 1.2em;
        margin-top: 0.5em;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        border: none;
    }
    th {
        text-align: left;
        padding: 0.5em;
        color: #8b949e;
        font-weight: 700;
        border-bottom: 1px solid #2d313a;
        font-size: 0.9em;
    }
    td {
        padding: 0.6em;
        border-bottom: 1px solid #2d313a;
        font-size: 0.95em;
    }
    .nickname { color: #58a6ff; font-weight: 600; }
    tr:hover {
        background-color: rgba(88,166,255,0.08);
        transition: background 0.2s ease;
    }
    </style>
    </head>
    <body>
    <div class="table-box">
        <table>
            <thead>
                <tr>
    """
    # headers
    for col in columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # rows
    for _, row in df.iterrows():
        html += "<tr>"
        for col in columns:
            cell_value = row[col]
            cell_class = "nickname" if col.lower() == "nickname" else ""
            html += f'<td class="{cell_class}">{cell_value}</td>'
        html += "</tr>"
    
    html += "</tbody></table></div></body></html>"


    return(html)


def render_score_table(title: str, df, columns: list[str]):
    """
    Render a styled HTML table inside Streamlit, using the dark leaderboard theme.

    Args:
        title (str): Section title (e.g., "Top Players by #1 Ranks")
        df (pd.DataFrame): The dataframe to render.
        columns (list[str]): Column names (in the order they should appear). 
                             'Login' will be used only for tooltip if included.
    """
    import streamlit as st

    st.markdown(f"### {title}")

    # Sort by Points descending
    df_sorted = df.sort_values(by='Points', ascending=False).reset_index(drop=True)

    # Start HTML
    html = """
    <html>
    <head>
    <style>
    body {
        background-color: transparent;
        color: #e6edf3;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .table-box {
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
        font-weight: 700;
        border-bottom: 1px solid #2d313a;
        font-size: 0.9em;
    }
    td {
        padding: 0.6em;
        border-bottom: 1px solid #2d313a;
        font-size: 0.95em;
    }
 
    </style>
    </head>
    <body>
    <div class="table-box">
        <table>
            <thead>
                <tr>
    """
    # Only include visible columns (skip Login)
    all_columns = columns.copy()
    if "Team" not in all_columns:
        all_columns.insert(1, "Team")  # place after NickName
    
    html += """
    <style>
    .top-1 { background-color: rgba(255,215,0,0.08);font-weight: 900; }
    .top-2 { background-color: rgba(192,192,192,0.08); }
    .top-3 { background-color: rgba(205,127,50,0.08); }
    
    tr:hover {
        background-color: rgba(88,166,255,0.08);
        transition: background 0.2s ease;
    }
    
    .nickname {
    color: #58a6ff;
    font-weight: 600;
    position: relative;
    max-width: 120px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    }
    
    
    .nickname:hover::after {
        content: attr(data-login);
        position: absolute;
        left: 0;
        bottom: 100%;
        background: rgba(30, 34, 45, 0.95);
        color: #e6edf3;
        font-size: 0.75em;
        padding: 4px 8px;
        border-radius: 6px;
        white-space: nowrap;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    
    .team-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 0.8em;
        font-weight: 600;
        text-align: center;
        min-width: 70px;
    }
    </style>
    """
    
    # Table headers
    for col in all_columns:
        if col != "Login":
            html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Rows
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        # Top 1–3 highlighting
        top_class = ""
        if i == 0:
            top_class = "top-1"
        elif i == 1:
            top_class = "top-2"
        elif i == 2:
            top_class = "top-3"
    
        login = str(row.get("Login", "")).strip().lower()
        team = teams_map.get(login, "")
        if pd.isna(team):
            team = "soloplayer"
        team_color = ""
        for key, color in TEAM_COLORS.items():
            if key in team.lower():
                team_color = color
                break
    
        html += f'<tr class="{top_class}">'
    
        for col in all_columns:
            if col == "Login":
                continue  # Skip Login column entirely
            cell_value = row.get(col, "")
            
            if col == "Average_Rank":
                cell_value = f"{float(cell_value):.2f}"
                
            if col == "NickName":
                login_value = row["Login"]
                html += (
                    f'<td class="nickname {top_class}" '
                    f'data-login="Login: {login_value}">{cell_value}</td>'
                )
              
            elif col == "Team":
                if team:
                    badge_html = (
                        f'<span class="team-badge" '
                        f'style="color:{team_color}; '
                        f'border:1px solid {team_color}; '
                        f'background-color:rgba(255,255,255,0.00);">'
                        f'{team}</span>'
                    )
                    html += f"<td>{badge_html}</td>"
                else:
                    html += "<td></td>"
            else:
                html += f'<td class="{top_class}">{cell_value}</td>'
    
        html += "</tr>"

    return html

def top_border(df):
    # --- Compute metrics ---
    total_maps = df["MapUID"].nunique()
    unique_players = df["Login"].nunique()
    total_records = len(df)
    last_updated = pd.to_datetime(df["RecordDate"], errors="coerce").max().strftime("%Y-%m-%d %H:%M")
    
    # --- CSS Styling ---
    st.markdown("""
    <style>
    .stat-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        background: transparent;
        gap: 1em;
        margin-bottom: 1.5em;
    }
    .stat-box {
        flex: 1;
        min-width: 180px;
        background: linear-gradient(145deg, #1a1d25, #11141a);
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        text-align: center;
        padding: 1em 0.5em;
        color: #e6edf3;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.7);
    }
    .stat-value {
        font-size: 2em;
        font-weight: 700;
        margin-bottom: 0.2em;
    }
    .stat-label {
        color: #8b949e;
        font-size: 0.85em;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }
    @media (max-width: 800px) {
        .stat-container {
            flex-direction: column;
            align-items: center;
        }
        .stat-box {
            width: 100%;
            max-width: 400px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Display top info boxes ---
    st.markdown(f"""
    <div class="stat-container">
        <div class="stat-box">
            <div class="stat-value">🗺️ {total_maps:,}</div>
            <div class="stat-label">Maps Tracked</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">👤 {unique_players:,}</div>
            <div class="stat-label">Unique Players</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">🏁 {total_records:,}</div>
            <div class="stat-label">Records Tracked</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">🕒 {last_updated}</div>
            <div class="stat-label">Last Updated</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
# Helper: human-readable "x time ago"
def time_ago(dt):
    if pd.isna(dt):
        return "N/A"
    now = datetime.now(timezone.utc) if dt.tzinfo else datetime.utcnow()
    diff = now - dt
    s = diff.total_seconds()
    if s < 60:
        return f"{int(s)} s ago"
    elif s < 3600:
        return f"{int(s // 60)} min ago"
    elif s < 86400:
        return f"{int(s // 3600)} h ago"
    else:
        days = int(s // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
