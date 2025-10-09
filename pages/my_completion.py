# -*- coding: utf-8 -*-
"""
Created on Thu Oct  9 09:56:04 2025

@author: Hola
"""
import streamlit as st
import pandas as pd
from renders import render_html_table,render_teams_table
from app import load_data
from score import assign_team_from_nickname, assign_points
import streamlit.components.v1 as components
import altair as alt

st.set_page_config(page_title="My achievements", layout="wide")
st.title("Dodo challenge completion")


# Load player and team data
df = load_data("./resources/dedimania_all_records.csv")

teams_df = pd.read_csv("./resources/teams.csv", sep = "\t", engine="python")

# Manual login addition
manual_login = st.sidebar.text_input("Add player by Login (case-sensitive)")
if manual_login:
    extra_player = df[df["Login"].str.lower() == manual_login.lower()]
    if not extra_player.empty:
        st.sidebar.success(f"✅ Added {extra_player['NickName'].iloc[-1]}")
        df_team = pd.concat([teams_df, extra_player])
    else:
        st.sidebar.error(f"❌ No player found with login '{manual_login}'")
        
# Step 1: Extract challenge ID and map to decades
df=df[df["Login"]==manual_login]
df['Challenge_ID'] = df['Challenge'].str.extract(r'\*(\d+)\*')
df = df.dropna(subset=['Challenge_ID'])
df["Challenge_ID"] = df["Challenge_ID"].astype(int)
df['Decade'] = (df['Challenge_ID'] // 10) * 10  # Grouping by decade (0-9 -> 0, 10-19 -> 10, etc.)
df['Challenge_Unit'] = df['Challenge_ID'] % 10

def rank_to_category(rank):
    if pd.isna(rank): return 'Not Completed'
    elif rank == 1: return 'Gold'
    elif rank == 2: return 'Silver'
    elif rank == 3: return 'Bronze'
    elif rank <= 10: return 'Top 10'
    elif rank <= 20: return 'Top 20'
    elif rank <= 30: return 'Top 30'
    else: return 'Other'
    
df['Rank_Category'] = df['Rank'].apply(rank_to_category)


# --- Step 4: Prepare grid of all possible (decade, unit) combinations ---
decades = sorted(df['Decade'].unique())
units = list(range(10))
grid = pd.DataFrame([(d, u) for d in decades for u in units], columns=['Decade', 'Challenge_Unit'])
plot_df = grid.merge(df[['Decade', 'Challenge_Unit', 'Rank_Category', 'Rank']], how='left')

# --- Step 6: Color mapping ---
color_domain = ['Gold', 'Silver', 'Bronze', 'Top 10', 'Top 20', 'Top 30', 'Not Completed']
color_range = [
    '#FFD700', '#C0C0C0', '#CD7F32',      # medals
    '#73C2FB', '#8BC34A', '#B0BEC5',      # faded tiers
    '#1e1e1e'                             # not completed = dark background
]

# --- Step 6: Create heatmap (with square tiles and dark theme) ---
tile_size = 40
width = tile_size * 14                      # 10 challenge units
height = tile_size * len(decades)          # dynamic based on # of decades
plot_df['Challenge_Unit'] = plot_df['Challenge_Unit'].astype(str)

print(plot_df)
heatmap = alt.Chart(plot_df).mark_rect(
    cornerRadius=8,
    stroke= '#1e1e1e',
    strokeWidth=3
).encode(
    x=alt.X('Challenge_Unit:O',
        sort=['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            title='Unit Digit',
            axis=alt.Axis(labelColor='white', titleColor='white'),
            scale=alt.Scale(padding=0, align=0.5)),
    y=alt.Y('Decade:O',
            title='Decade',
            axis=alt.Axis(labelColor='white', titleColor='white'),
            scale=alt.Scale(padding=0, align=0.5)),
    color=alt.Color('Rank_Category:N',
                    scale=alt.Scale(domain=color_domain, range=color_range),
                    legend=alt.Legend(title='Rank Category', labelColor='white', titleColor='white')),
    tooltip=['Decade', 'Challenge_Unit', 'Rank', 'Rank_Category']
).properties(
    width=width,
    height=height,
    background='#1e1e1e',
    title=alt.TitleParams(
        text="Hover to see ranks",
        color='white',
        anchor='start'
    )
)

# --- Step 8: Show in Streamlit ---
st.altair_chart(heatmap,use_container_width = False)  # Don't use use_container_width=True
