"""Transform UKTUS 2014-2015 diary data to markov time series occupancy states.

Produces markov-ts.pickle compatible with the paper's plot pipeline,
using UKTUS15 column naming instead of pytus2000 expectations.
"""
import click
import pandas as pd
import numpy as np

import urbanoccupants as uo

# Home and sleep definitions (verified from data exploration)
HOME_CODES = {11}
SLEEP_CODES = {110, 111, 120}

from datetime import time

# Time of day for each slot (144 slots = 10-minute bins from 00:00 to 23:50)
# Uses midnight-start convention (like the original TUS 2000 pipeline)
# to ensure plot alignment when comparing old and new datasets.
def _slot_to_time_of_day(slot_index):
    total_minutes = (slot_index - 1) * 10
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return time(hour=hours, minute=minutes)

TIME_OF_DAY_LABELS = [_slot_to_time_of_day(i) for i in range(1, 145)]


@click.command()
@click.argument('path_to_input')
@click.argument('path_to_output')
def read_markov_ts_uktus15(path_to_input, path_to_output):
    """Read UKTUS 2014-2015 diary data and transform to markov time series.
    
    Reads uktus15_diary_wide.tab, maps activities and locations to occupancy states
    (HOME, SLEEP_AT_HOME, NOT_AT_HOME), and writes markov-ts.pickle compatible with
    the paper's population cluster plot.
    
    Parameters:
        path_to_input: path to uktus15_diary_wide.tab
        path_to_output: path to write markov-ts.pickle
    """
    print(f"Reading UKTUS15 diary data from {path_to_input}")
    diary_data = _read_diary_data(path_to_input)
    print(f"Read {len(diary_data)} diary records")
    
    print("Transforming to occupancy states...")
    markov_ts = _transform_to_markov_timeseries(diary_data)
    
    print(f"Markov time series shape: {markov_ts.shape}")
    print(f"Index names: {markov_ts.index.names}")
    print(f"Columns: {markov_ts.columns.tolist()}")
    print(f"Unique states: {pd.unique(markov_ts[0].dropna()).tolist()}")
    
    print(f"Writing to {path_to_output}")
    markov_ts.to_pickle(path_to_output)
    print("Done.")


def _read_diary_data(path_to_input):
    """Read UKTUS15 diary file, extracting person ID, day type, and activity/location columns."""
    # Activity and location columns: act1_1 ... act1_144, wher_1 ... wher_144
    activity_cols = [f"act1_{i}" for i in range(1, 145)]
    location_cols = [f"wher_{i}" for i in range(1, 145)]
    id_cols = ["serial", "pnum", "ddayw"]
    
    cols_to_read = id_cols + activity_cols + location_cols
    
    df = pd.read_csv(path_to_input, sep="\t", usecols=cols_to_read, dtype={
        "serial": int,
        "pnum": int,
        "ddayw": int,
    })
    
    # Convert activity and location columns to numeric (handle missing as NaN)
    for col in activity_cols + location_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def _transform_to_markov_timeseries(diary_data):
    """Transform activity/location columns to occupancy states.
    
    Creates a DataFrame with:
    - Index: MultiIndex(SN1, SN2, SN3, daytype, time_of_day)
    - Columns: [0] (single column with Activity enums)
    """
    records = []
    
    for _, row in diary_data.iterrows():
        sn1 = 1  # constant: no stratification ID in UKTUS15
        sn2 = int(row["serial"])
        sn3 = int(row["pnum"])
        
        # Map day type: 1=weekday, 2-3=weekend
        daytype = "weekday" if row["ddayw"] == 1 else "weekend"
        
        # Process each 10-minute time slot
        for slot in range(1, 145):
            activity_col = f"act1_{slot}"
            location_col = f"wher_{slot}"
            
            activity = row[activity_col]
            location = row[location_col]
            
            # Determine occupancy state
            is_home = location in HOME_CODES if pd.notna(location) else False
            is_sleep = activity in SLEEP_CODES if pd.notna(activity) else False
            
            if pd.isna(location) or pd.isna(activity):
                state = np.nan
            elif is_home and is_sleep:
                state = uo.Activity.SLEEP_AT_HOME
            elif is_home:
                state = uo.Activity.HOME
            else:
                state = uo.Activity.NOT_AT_HOME
            
            time_of_day = TIME_OF_DAY_LABELS[slot - 1]
            
            records.append({
                'SN1': sn1,
                'SN2': sn2,
                'SN3': sn3,
                'daytype': daytype,
                'time_of_day': time_of_day,
                'state': state
            })
    
    df = pd.DataFrame(records)
    
    # Create MultiIndex
    df_indexed = df.set_index(['SN1', 'SN2', 'SN3', 'daytype', 'time_of_day'])
    
    # Extract state column and rename to 0 (matches original pipeline)
    markov_ts = pd.DataFrame(df_indexed['state'], columns=[0])
    
    # Convert to categorical with all possible Activity values
    markov_ts[0] = markov_ts[0].astype('category')
    markov_ts[0] = markov_ts[0].cat.set_categories([
        uo.Activity.HOME,
        uo.Activity.SLEEP_AT_HOME,
        uo.Activity.NOT_AT_HOME
    ])
    
    return markov_ts


if __name__ == '__main__':
    read_markov_ts_uktus15()
