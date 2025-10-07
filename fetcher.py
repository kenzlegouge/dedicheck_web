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

# Launch the background thread (only once)
def start_background_thread():
    if not any(t.name == "dedimania_fetcher" for t in threading.enumerate()):
        t = threading.Thread(target=background_fetch_loop, args=(3600,), daemon=True, name="dedimania_fetcher")
        t.start()
        print("🚀 Background fetch thread started.")
