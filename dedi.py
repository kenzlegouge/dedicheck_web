import requests
from bs4 import BeautifulSoup
import pandas as pd
from db import ensure_db_connection

UID_FILE = "all_maps.txt"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.1 Safari/537.36"
    )
}

def fetch_dedi():
    with open(UID_FILE, "r", encoding="utf-8") as f:
        uids = [u.strip() for u in f if u.strip()]

    all_records = []
    print(f"Found {len(uids)} UIDs in {UID_FILE}")

    for n, uid in enumerate(uids, start=1):
        url = f"http://dedimania.net/tmstats/?do=stat&Mode=M1&Uid={uid}&Show=RECORDS"
        print(f"[{n}/{len(uids)}] Fetching {url}")

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ Failed to fetch {uid}: {e}")
            continue

        # Extract clean text
        soup = BeautifulSoup(resp.text, "html.parser")
        lines = [line.strip() for line in soup.get_text("\n", strip=True).split("\n") if line.strip()]
        lines = cutlines(lines)
        # Each record starts with "TMU"
        records = []
        for i, line in enumerate(lines):
            if line == "TMU" and i + 11 < len(lines):
                block = lines[i : i + 12]  # TMU + next 11 lines
                record = {
                    "Game": block[0],
                    "Login": block[1],
                    "NickName": block[2],
                    "Rank": block[3],
                    "Max": block[4],
                    "Record": block[5],
                    "Mode": block[6],
                    "CPs": block[7],
                    "MapCPs": block[8],
                    "Challenge": block[9],
                    "Envir": block[10],
                    "RecordDate": block[11],
                    "MapUID": uid,
                }
                records.append(record)

        if not records:
            print(f"⚠️ No records found for {uid}")
        else:
            all_records.extend(records)
            print(f"✅ Parsed {len(records)} records for {uid}")

    # Combine everything into a DataFrame
    df = pd.DataFrame(all_records)
    
    df["Record"] = df["Record"].apply(parse_record_time)
    df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
    df["Max"] = pd.to_numeric(df["Max"], errors="coerce")
    df["CPs"] = pd.to_numeric(df["CPs"], errors="coerce")
    df["RecordDate"] = pd.to_datetime(df["RecordDate"], errors="coerce")


    return df

def cutlines(lines):
        # Define header block and length
    header_fields = [
        "Game", "Login", "NickName", "Rank", "Max",
        "Record", "Mode", "CPs", "MapCPs", "Challenge",
        "Envir", "RecordDate"
    ]
    
    # Find where the header starts
    start_idx = None
    for i in range(len(lines) - len(header_fields)):
        if lines[i:i+len(header_fields)] == header_fields:
            start_idx = i + len(header_fields)
            break
    
    # Find "Limit" at the end
    end_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("limit"):
            end_idx = i
            break
    
    # Slice between header and "Limit"
    if start_idx is not None and end_idx is not None:
        data_lines = lines[start_idx:end_idx]
    else:
        data_lines = []
        
    return(data_lines)

def parse_record_time(time_str):
    """Convert 'MM:SS.xx' to float seconds"""
    try:
        mins, sec = time_str.strip().split(":")
        return round(float(mins) * 60 + float(sec), 3)
    except Exception as e:
        print(f"⚠️ Failed to parse record time '{time_str}': {e}")
        return None
    
# def ensure_dedimania_table(bot):
#     """Ensure the Dedimania records table exists."""
#     await ensure_db_connection(bot)
#     await bot.db.execute("""
#     CREATE TABLE IF NOT EXISTS dedimania_records (
#         id SERIAL PRIMARY KEY,
#         Game TEXT,
#         Login TEXT,
#         NickName TEXT,
#         Rank INTEGER,
#         Max INTEGER,
#         Record TEXT,
#         Mode TEXT,
#         CPs INTEGER,
#         MapCPs TEXT,
#         Challenge TEXT,
#         Envir TEXT,
#         RecordDate TIMESTAMP,
#         MapUID TEXT,
#         UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     );
#     """)

if __name__ == "__main__":
    df = fetch_dedi()
    print(f"\n✅ Total records: {len(df)}")
    df.to_csv("dedimania_all_records.csv", index=False, encoding="utf-8")
    print("💾 Saved to dedimania_all_records.csv")
    