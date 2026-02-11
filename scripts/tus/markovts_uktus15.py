"""
Read UKTUS 2014-2015 (8128) diary data and produce occupancy state time series.

Transformations:
1. Read diary with serial, pnum, KindOfDay, act1_1...act1_144, wher_1...wher_144
2. Map daytype to 'weekday'/'weekend' strings
3. Collapse duplicates per (serial, pnum, daytype) using per-slot MODE
4. Convert each slot to occupancy state (SLEEP_AT_HOME, HOME, NOT_AT_HOME)
5. Build long DataFrame with index (SN1, SN2, SN3, daytype, time_of_day)
6. Save as pickle
"""

import click
import pandas as pd
import numpy as np
from datetime import datetime, time
from scipy.stats import mode

from urbanoccupants.person import Activity


# Constants from UKTUS15_VERIFICATION.md
HOME_CODES = {11}
SLEEP_CODES = {110, 111, 120}
MISSING_WHER_CODES = {-9, -7, -2, 0, 10, 99}


def daytype_to_category(kindofday):
    """Map KindOfDay to 'weekday' or 'weekend' string."""
    # KindOfDay encoding: 1=Monday, 2=Tuesday, ..., 7=Sunday
    # Weekday: Mon-Fri (1-5), Weekend: Sat-Sun (6-7)
    if pd.isna(kindofday):
        return None
    kindofday = int(kindofday)
    return 'weekend' if kindofday >= 6 else 'weekday'


def slot_to_time_of_day(slot_index):
    """Convert slot index (1-144) to datetime.time.
    
    slot 1 -> 00:00, slot 2 -> 00:10, ..., slot 144 -> 23:50
    Uses midnight-start convention (like the original TUS 2000 pipeline)
    to ensure plot alignment when comparing old and new datasets.
    """
    total_minutes = (slot_index - 1) * 10
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return time(hour=hours, minute=minutes)


def aggregate_duplicate_diaries(group_df, slot_columns):
    """Aggregate duplicate diaries for a (serial, pnum, daytype) group using MODE.
    
    For each slot, compute mode across diaries. If tie, pick smallest value.
    """
    result = {}
    for slot in slot_columns:
        values = group_df[slot].dropna().values
        if len(values) == 0:
            result[slot] = np.nan
        else:
            # scipy.stats.mode returns (mode_value, count)
            mode_result = mode(values)
            result[slot] = mode_result.mode if hasattr(mode_result, 'mode') else mode_result[0]
    return pd.Series(result)


def map_to_occupancy_state(act_value, wher_value, missing_wher_counts):
    """Convert (act, wher) pair to occupancy state.
    
    SLEEP_AT_HOME: act in SLEEP_CODES AND wher == 11
    HOME: wher == 11 AND act not in SLEEP_CODES
    NOT_AT_HOME: else (including missing/invalid wher)
    """
    # Treat missing/invalid wher as NOT_AT_HOME, but track for logging
    if pd.isna(wher_value):
        wher_value = -9  # Mark as missing for tracking
    
    wher_value = int(wher_value)
    
    if wher_value in MISSING_WHER_CODES and wher_value not in HOME_CODES:
        if wher_value not in missing_wher_counts:
            missing_wher_counts[wher_value] = 0
        missing_wher_counts[wher_value] += 1
        return Activity.NOT_AT_HOME
    
    if pd.isna(act_value):
        return Activity.NOT_AT_HOME
    
    act_value = int(act_value)
    
    # Decision logic
    if wher_value in HOME_CODES:
        if act_value in SLEEP_CODES:
            return Activity.SLEEP_AT_HOME
        else:
            return Activity.HOME
    else:
        return Activity.NOT_AT_HOME


@click.command()
@click.argument('path_to_input')
@click.argument('path_to_output')
def read_markov_ts_uktus15(path_to_input, path_to_output):
    """Read UKTUS 2014-2015 diary and produce occupancy state time series.
    
    Output: pickle file with index (SN1, SN2, SN3, daytype, time_of_day)
            and values Activity enums {HOME, SLEEP_AT_HOME, NOT_AT_HOME}
    """
    print("[1] Reading diary file...")
    diary_df = pd.read_csv(
        path_to_input,
        sep='\t',
        dtype={'serial': 'int64', 'pnum': 'int64', 'KindOfDay': 'int64'}
    )
    print(f"    Loaded {len(diary_df)} diary records")
    
    # Column names for activity and location slots
    act_cols = [f'act1_{i}' for i in range(1, 145)]
    wher_cols = [f'wher_{i}' for i in range(1, 145)]
    
    print(f"\n[2] Mapping daytype and creating groups...")
    # Add daytype column
    diary_df['daytype'] = diary_df['KindOfDay'].apply(daytype_to_category)
    
    # Create a group key for duplicate detection
    diary_df['group_key'] = list(zip(diary_df['serial'], diary_df['pnum'], diary_df['daytype']))
    
    # Count duplicates
    dup_counts = diary_df['group_key'].value_counts()
    n_dups = (dup_counts > 1).sum()
    total_dup_records = dup_counts[dup_counts > 1].sum()
    print(f"    Found {n_dups} groups with duplicates ({total_dup_records} total duplicate records)")
    
    print(f"\n[3] Aggregating duplicate diaries using per-slot MODE...")
    # Aggregate duplicates per (serial, pnum, daytype)
    aggregated_list = []
    for group_key, group_df in diary_df.groupby('group_key'):
        if len(group_df) > 1:
            # Aggregate using mode
            agg_row = aggregate_duplicate_diaries(group_df, act_cols + wher_cols)
            agg_row['serial'] = group_key[0]
            agg_row['pnum'] = group_key[1]
            agg_row['daytype'] = group_key[2]
            aggregated_list.append(agg_row)
        else:
            # Single diary, keep as is
            row = group_df.iloc[0]
            agg_row = pd.Series({col: row[col] for col in act_cols + wher_cols})
            agg_row['serial'] = group_key[0]
            agg_row['pnum'] = group_key[1]
            agg_row['daytype'] = group_key[2]
            aggregated_list.append(agg_row)
    
    diary_agg_df = pd.DataFrame(aggregated_list)
    print(f"    After aggregation: {len(diary_agg_df)} unique (serial, pnum, daytype) rows")
    
    print(f"\n[4] Converting slots to occupancy states...")
    missing_wher_counts = {}
    
    # Build long format DataFrame
    rows = []
    for idx, row in diary_agg_df.iterrows():
        serial = int(row['serial'])
        pnum = int(row['pnum'])
        daytype = row['daytype']
        
        for slot_num in range(1, 145):
            act_col = f'act1_{slot_num}'
            wher_col = f'wher_{slot_num}'
            
            act_value = row[act_col]
            wher_value = row[wher_col]
            
            state = map_to_occupancy_state(act_value, wher_value, missing_wher_counts)
            time_of_day = slot_to_time_of_day(slot_num)
            
            rows.append({
                'SN1': 1,
                'SN2': serial,
                'SN3': pnum,
                'daytype': daytype,
                'time_of_day': time_of_day,
                'state': state
            })
    
    markov_ts_long = pd.DataFrame(rows)
    markov_ts = markov_ts_long.set_index(['SN1', 'SN2', 'SN3', 'daytype', 'time_of_day'])['state']
    
    # Convert to DataFrame (column 0) to match 4504 format for compatibility with popcluster.py
    markov_ts = markov_ts.to_frame(name=0)
    
    print(f"\n[5] Building final time series...")
    print(f"    Total rows: {len(markov_ts)}")
    print(f"    Index names: {markov_ts.index.names}")
    print(f"    Unique states: {markov_ts[0].unique()}")
    
    # Missing wher code summary
    if missing_wher_counts:
        print(f"\n    Missing/invalid wher codes (→ NOT_AT_HOME):")
        for code, count in sorted(missing_wher_counts.items()):
            print(f"      Code {code}: {count} slots")
    
    print(f"\n[6] Validation checks...")
    # Check index uniqueness
    if markov_ts.index.is_unique:
        print(f"    ✓ Index is unique")
    else:
        print(f"    ✗ Index has duplicates! This is an error.")
        raise ValueError("Index is not unique")
    
    # Check state set
    valid_states = {Activity.HOME, Activity.SLEEP_AT_HOME, Activity.NOT_AT_HOME}
    unique_states = set(markov_ts[0].unique())
    if unique_states.issubset(valid_states):
        print(f"    ✓ States {unique_states} are valid")
    else:
        print(f"    ✗ Invalid states: {unique_states - valid_states}")
        raise ValueError(f"Invalid states found: {unique_states - valid_states}")
    
    # Check 144 entries per (person, daytype)
    entries_per_person_day = markov_ts.reset_index().groupby(['SN2', 'SN3', 'daytype']).size()
    if (entries_per_person_day == 144).all():
        print(f"    ✓ Each (person, daytype) has exactly 144 entries")
    else:
        bad_counts = entries_per_person_day[entries_per_person_day != 144]
        print(f"    ✗ Some (person, daytype) have != 144 entries: {len(bad_counts)} groups")
        raise ValueError(f"Invalid entry counts for {len(bad_counts)} groups")
    
    # Check both daytypes present
    daytypes = set(markov_ts.reset_index()['daytype'].unique())
    if daytypes == {'weekday', 'weekend'}:
        print(f"    ✓ Both 'weekday' and 'weekend' present")
    else:
        print(f"    ✗ Missing daytypes: {{'weekday', 'weekend'}} - {daytypes}")
        raise ValueError(f"Missing daytypes: expected {{'weekday', 'weekend'}}, got {daytypes}")
    
    # Spot-check: at time_of_day=04:00, most should be SLEEP_AT_HOME/HOME
    sleep_time = time(4, 0)
    sleep_entries = markov_ts[markov_ts.index.get_level_values('time_of_day') == sleep_time][0]
    sleep_or_home = sleep_entries.isin({Activity.SLEEP_AT_HOME, Activity.HOME}).sum()
    pct = 100.0 * sleep_or_home / len(sleep_entries) if len(sleep_entries) > 0 else 0
    print(f"    At 04:00, {sleep_or_home}/{len(sleep_entries)} ({pct:.1f}%) are SLEEP_AT_HOME/HOME")
    
    print(f"\n[7] Saving to pickle...")
    markov_ts.to_pickle(path_to_output)
    print(f"    ✓ Saved to {path_to_output}")
    
    n_people = len(markov_ts.reset_index()[['SN2', 'SN3']].drop_duplicates())
    print(f"\n✓ Success: {n_people} individuals, {len(markov_ts)} total time series entries")


if __name__ == '__main__':
    read_markov_ts_uktus15()
