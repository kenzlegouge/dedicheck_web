import re
import pandas as pd
import requests
from io import StringIO
import os
import aiohttp
import asyncio


CLEAN_REGEX = re.compile(r"(\$[0-9a-fA-F]{3})|(\$[wWtTzZiIoOsSgGnNmM])|(\$[hHlL](\[.*\])?)")

def clean_string(s):
    if isinstance(s, str):
        return CLEAN_REGEX.sub("", s)
    return s

async def fetch_records_table(uid, top_n=30):
    """
    Async: Fetch Dedimania ET records for a given UID and return (challenge_name, dataframe)
    # Required otherwise discord breaks down
    """
    URL = f"http://dedimania.net:8000/ET?uid={uid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, timeout=10) as resp:
            text = await resp.text()

    lines = text.strip().splitlines()
    if not lines:
        return None, pd.DataFrame()

    # map info
    map_info = lines[0].split(",", maxsplit=6)
    challenge_name = map_info[4] if len(map_info) > 4 else uid

    # parse records
    records = []
    for line in lines[1:]:
        cols = line.split(",", maxsplit=6)
        if len(cols) < 7:
            continue
        records.append(cols)

    df = pd.DataFrame(records, columns=["Time_ms","Unknown1","Unknown2","Login","Unknown3","Nickname","Server"])
    df["Time_ms"] = pd.to_numeric(df["Time_ms"], errors="coerce")
    df["Nickname"] = df["Nickname"].apply(clean_string)
    df["Nickname"] = df["Nickname"].fillna("")
    df["Time_s"] = df["Time_ms"] / 1000.0
    df.insert(0, "Rank", range(1, len(df) + 1))
    df = df.head(top_n)

    return challenge_name, df[["Rank", "Time_s", "Nickname", "Login"]]

def format_records(df):
    """Return a Discord-friendly string of the table"""
    LRM = "\u200E"  # Left-to-Right Mark

    lines = [
        LRM + "Rank | Time (s) | Nickname | Login",
        LRM + "---------------------------",
    ]
    for _, row in df.iterrows():
        # prepend LRM to force LTR per line
        lines.append(
            LRM + f"{row.Rank:>2} | {row.Time_s:>6.2f} | {row.Nickname} | {row.Login}"
        )

    return "```\n" + "\n".join(lines) + "\n```"

def load_previous(uid):
    """Load previous records for a UID from CSV"""
    path = f"records/{uid}.csv"
    if os.path.exists(path):
        prev_df= pd.read_csv(path)
        prev_df["Nickname"] = prev_df["Nickname"].fillna("")
        return prev_df

    return pd.DataFrame()

def save_records(uid, df):
    """Save current records for a UID to CSV"""
    os.makedirs("records", exist_ok=True)
    path = f"records/{uid}.csv"
    df.to_csv(path, index=False)

def load_uids(file_path="maps.txt"):
    uids = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                uids.append(line)
    return uids

def add_uid(uid, file_path="maps.txt", max_uids=100):
    """Add a UID to maps.txt if it doesn't already exist."""
    uids = load_uids(file_path)

    if uid in uids:
        return False, f"UID `{uid}` already exists."

    if len(uids) >= max_uids:
        return False, f"UID limit of {max_uids} reached."

    with open(file_path, "a") as f:
        f.write(uid + "\n")

    return True, f"UID `{uid}` added successfully."

def detect_new_records(prev_df, current_df):
    """
    Compare previous vs current top10 DataFrames.
    Return a DataFrame of new or improved records.
    """
    if prev_df.empty:
        return current_df  # first load, everything is "new"

    prev_set = set(zip(prev_df["Login"], prev_df["Time_s"]))
    curr_set = set(zip(current_df["Login"], current_df["Time_s"]))

    new_entries = curr_set - prev_set

    mask = [(row.Login, row.Time_s) in new_entries for _, row in current_df.iterrows()]
    return current_df[mask]


from collections import Counter

def get_top1_counts(records_folder="records/"):
    """
    Scan all CSVs in records_folder and count how many times each Nickname
    has Rank 1.
    Returns a Counter {Nickname: count}.
    """
    counter = Counter()
    for filename in os.listdir(records_folder):
        if not filename.endswith(".csv"):
            continue
        path = os.path.join(records_folder, filename)
        try:
            df = pd.read_csv(path)
            # Only check Rank 1
            top1 = df[df["Rank"] == 1]
            for nickname in top1["Nickname"]:
                counter[nickname] += 1
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
    return counter

def load_uid_map(path="maps_dict.txt"):
    """
    Load a TSV with UID + Name.
    Builds a dict keyed by whatever is between the first *...* in the name.
    """
    df = pd.read_csv(path, sep="\t", header=None, names=["uid", "name"])
    # extract whatever is between the first pair of *...*
    df["short_key"] = df["name"].str.extract(r"\*(.*?)\*")  # non-greedy
    # create a dict short_key(lower) -> uid
    key_to_uid = {k.lower(): v for k, v in zip(df.short_key, df.uid)}
    uid_to_name = dict(zip(df.uid, df.name))
    return uid_to_name, key_to_uid
