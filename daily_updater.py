# daily_updater.py
import os
import pandas as pd
import psycopg2
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

CSV_PATH = "./resources/daily_player_points.csv"
_updater_thread = None  # internal guard variable


def fetch_daily_scores_from_db():
    """Fetch all player_daily_scores rows from Neon and write to CSV once per day."""
    load_dotenv()
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    query = """
        SELECT login, nickname, score, recorded_at
        FROM player_daily_scores
        ORDER BY recorded_at ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"💾 Updated {CSV_PATH} with {len(df)} rows at {datetime.now()}", flush=True)
    return df


def _loop(interval_hours: float):
    """Background loop that refreshes daily_player_points.csv every N hours."""
    while True:
        try:
            fetch_daily_scores_from_db()
        except Exception as e:
            print(f"⚠️ Error fetching daily scores: {e}", flush=True)
        time.sleep(interval_hours * 3600)


def start_daily_updater(interval_hours=24):
    """Start the daily updater thread (runs once a day)."""
    global _updater_thread

    if _updater_thread is not None and _updater_thread.is_alive():
        print("ℹ️ Daily updater already running, skipping new thread.", flush=True)
        return

    # Ensure the CSV exists on first boot
    if not os.path.exists(CSV_PATH):
        print("📄 No CSV found, creating initial daily_player_points.csv...", flush=True)
        try:
            fetch_daily_scores_from_db()
        except Exception as e:
            print(f"⚠️ Could not create initial CSV: {e}", flush=True)

    # Start background thread
    _updater_thread = threading.Thread(target=_loop, args=(interval_hours,), daemon=True)
    _updater_thread.start()
    print(f"🚀 Daily updater started (every {interval_hours}h)", flush=True)
