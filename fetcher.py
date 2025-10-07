# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 18:58:54 2025

@author: Hola
"""

import threading
import time
import pandas as pd
from datetime import datetime
from dedi import fetch_dedi  
import psycopg2
from datetime import date


latest_df = None
last_updated = None

def background_fetch_loop(interval=3600):
    """Run fetch_dedi() every `interval` seconds (default = 1h)."""
    global latest_df, last_updated
    while True:
        print("⏳ Running scheduled Dedimania fetch...")
        try:
            df = fetch_dedi()
            latest_df = df
            last_updated = datetime.utcnow()
            df.to_csv("./resources/dedimania_all_records.csv", index=False, encoding="utf-8")
            print(f"✅ Data refreshed — {len(df)} records @ {last_updated}")
        except Exception as e:
            print(f"⚠️ Error during fetch: {e}")
        time.sleep(interval)  # wait for next refresh
        
    # if datetime.utcnow().hour == 0:
    #     store_daily_scores(latest_scores_df)

# Launch the background thread (only once)
def start_background_thread():
    if not any(t.name == "dedimania_fetcher" for t in threading.enumerate()):
        t = threading.Thread(target=background_fetch_loop, args=(3600,), daemon=True, name="dedimania_fetcher")
        t.start()
        print("🚀 Background fetch thread started.")

def store_daily_scores(df_scores):
    """
    Store the daily score snapshot of players into the DB.
    df_scores must contain: Login, NickName, Team, Score
    """
    conn = psycopg2.connect(
        host="your-neon-host",
        dbname="your_db",
        user="your_user",
        password="your_password",
        sslmode="require"
    )
    cur = conn.cursor()

    today = date.today()

    for row in df_scores.itertuples(index=False):
        cur.execute("""
            INSERT INTO player_daily_scores (login, nickname, team, score, recorded_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (login, recorded_at)
            DO UPDATE SET score = EXCLUDED.score, nickname = EXCLUDED.nickname, team = EXCLUDED.team;
        """, (row.Login, row.NickName, getattr(row, "Team", None), float(row.Score), today))

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Stored {len(df_scores)} player scores for {today}")