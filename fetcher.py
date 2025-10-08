# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 18:58:54 2025

@author: Hola
"""
import os
import threading
import time
import sys
from dotenv import load_dotenv
load_dotenv()  # must come first
import pandas as pd
from datetime import datetime
from dedi import fetch_dedi  
import psycopg2
from datetime import date


from score import assign_points
from psycopg2.extras import execute_values
    

latest_df = None
last_updated = None


def background_fetch_loop(interval=3600):
    """Run fetch_dedi() every `interval` seconds (default = 1h)."""
    global latest_df, last_updated
    print("test")
    while True:
        print("⏳ Running scheduled Dedimania fetch...")
        try:
            df = fetch_dedi()

            latest_df = df

            last_updated = datetime.utcnow()

            df.to_csv("./resources/dedimania_all_records.csv", index=False, encoding="utf-8")
            print(f"✅ Data refreshed — {len(df)} records @ {last_updated}")
            print("⚠️ Storing to remote Neon db")
            store_daily_scores(df)

        except Exception as e:
            print(f"⚠️ Error during fetch: {e}")
        
        # if datetime.utcnow().hour == 0:
        #     print("Storing all data")
        
        
        time.sleep(interval)  # wait for next refresh
        


# Launch the background thread (only once)
def start_background_thread():
    if not any(t.name == "dedimania_fetcher" for t in threading.enumerate()):
        t = threading.Thread(target=background_fetch_loop, args=(3600,), daemon=True, name="dedimania_fetcher")
        t.start()
        print("🚀 Background fetch thread started.")

def store_daily_scores(df):
    """
    Efficiently store daily player scores into the DB.
    df must contain: Login, NickName, Rank, optional Team.
    """
    print("⚙️ Starting fast bulk upload...")

    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found!")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    # Compute score
    df["Score"] = df["Rank"].apply(assign_points)
    
    df = (
    df.sort_values("RecordDate")
      .groupby("Login", as_index=False)
      .agg({
          "NickName": "last",
          "Score": "sum"  # or 'sum', depending on your scoring model
      })
)

    today = date.today()

    # Ensure table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_daily_scores (
            id SERIAL PRIMARY KEY,
            login TEXT NOT NULL,
            nickname TEXT,
            score FLOAT NOT NULL,
            recorded_at DATE NOT NULL DEFAULT CURRENT_DATE,
            UNIQUE (login, recorded_at)
        );
    """)
    conn.commit()

    # Build list of tuples
    records = [
        (
            str(row.Login),
            str(row.NickName),
            float(row.Score),
            today,
        )
        for row in df.itertuples(index=False)
    ]
    
    

    print(f"🚀 Inserting {len(records)} records in bulk...")

    # Faster ON CONFLICT bulk upsert
    query = """
        INSERT INTO player_daily_scores (login, nickname, score, recorded_at)
        VALUES %s
        ON CONFLICT (login, recorded_at)
        DO UPDATE SET
            score = EXCLUDED.score,
            nickname = EXCLUDED.nickname;
    """

    execute_values(cur, query, records, page_size=500)
    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Bulk insert complete — {len(records)} rows uploaded for {today}")
