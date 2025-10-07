# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 09:42:17 2025

@author: Hola
"""

import pandas as pd
# Points system based on rank
def assign_points(rank):
    if rank == 1:
        return 10
    elif rank == 2:
        return 7
    elif rank == 3:
        return 4
    elif 4 <= rank <= 10:
        return 3
    elif 11 <= rank <= 20:
        return 2
    elif 21 <= rank <= 30:
        return 1
    else:
        return 0  # Rank > 30
def scoring_function(df):
    
    # Apply the function to assign points based on the rank
    df['Points'] = df['Rank'].apply(assign_points)

    # Number of maps played: count unique 'Challenge' for each player
    df['Maps Played'] = df.groupby(['Login', 'NickName'])['Challenge'].transform('nunique')

    # Average rank on scoring maps: only include players that have a valid rank
    df['Average Rank'] = df.groupby(['Login', 'NickName'])['Rank'].transform('mean')

    # Group by player and aggregate
    score_df = df.groupby(['Login', 'NickName']).agg(
        Points=('Points', 'sum'),
        Maps_Played=('Maps Played', 'max'),
        Average_Rank=('Average Rank', 'mean')
    ).reset_index()
    
    return(score_df)

team_prefixes = [
    "ĊĦ »", "ѕнιғт", "LeG", "нот", "Јғғ", "Сяс", "הѕс", "»тят",
    "νѕρ", "ғฟ๏", "ѕωα", "Law", "4W : : ", "nsc", "»ЯтА",
    "ωаѕρ .", "ғаιהτ.", "sigN", "GC l|", "kings"
]

def assign_team_from_nickname(nickname):
    if pd.isna(nickname):
        return None
    nickname = nickname.strip()
    for prefix in team_prefixes:
        if nickname.lower().startswith(prefix.lower()):
            return prefix.strip()
    return None

