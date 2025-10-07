import asyncpg
import os
import pandas as pd
from datetime import datetime
from utils import load_uid_map


async def init_db(bot):
    bot.db = await asyncpg.connect(os.getenv("DATABASE_URL"))
    
    # Create table if it doesn't exist
    await bot.db.execute("""
    CREATE TABLE IF NOT EXISTS new_records (
        id SERIAL PRIMARY KEY,
        uid TEXT NOT NULL,
        map_name TEXT,
        login TEXT,
        nickname TEXT,
        time_s REAL,
        rank INTEGER,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Count existing records
    result = await bot.db.fetchrow("SELECT COUNT(*) AS total FROM new_records;")
    total_records = result["total"]

    # If empty, populate from records folder
    if total_records == 0:
        print("[DB] Populating initial records from CSVs...")
        uid_to_name, key_to_uid = load_uid_map("maps_dict.txt")

        folder = "records"
        for filename in os.listdir(folder):
            if filename.endswith(".csv"):
                uid = filename.replace(".csv","")
                path = os.path.join(folder, filename)
                df = pd.read_csv(path).head(30)
                df["Nickname"] = df["Nickname"].fillna("") # if empty pseudo, fills NA
                for _, row in df.iterrows():
                    
                    map_name = uid_to_name.get(uid, uid)  # fallback to uid if not found
                    
                    await bot.db.execute("""
                        INSERT INTO new_records(uid, map_name, login, nickname, time_s, rank, detected_at)
                        VALUES($1,$2,$3,$4,$5,$6,$7)
                    """,
                    uid,  # store UID or map_name mapping if needed
                    map_name,
                    row["Login"],
                    row["Nickname"],
                    row["Time_s"],
                    int(row["Rank"]),
                    datetime.utcnow()
                    )
        print("[DB] Initial records inserted.")
        
    print(f"✅ Connected to database. Total stored records: {total_records}")
    return total_records


async def ensure_db_connection(bot):
    """Reconnect to DB only if the connection was lost."""
    try:
        await bot.db.execute("SELECT 1;")
    except Exception:
        print("[DB] Lost connection, reconnecting...")
        bot.db = await asyncpg.connect(os.getenv("DATABASE_URL"))
        print("[DB] Reconnected successfully.")


async def save_new_record(bot, uid, map_name, login, nickname, time_s, rank):
    """Insert a single new record safely."""
    await ensure_db_connection(bot)
    await bot.db.execute(
        """
        INSERT INTO new_records (uid, map_name, login, nickname, time_s, rank, detected_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        uid,
        map_name,
        login,
        nickname,
        time_s,
        rank,
        datetime.utcnow(),
    )