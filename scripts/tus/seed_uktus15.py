#!/usr/bin/env python
"""Create seed pickle from UKTUS 2014-2015 individual file (8128).

Maps age (DVAge) and economic activity (preferring dilodefr, fallback to WorkSta).
Produces index (SN1=1, SN2=serial, SN3=pnum) with columns [PeopleFeature.AGE, PeopleFeature.ECONOMIC_ACTIVITY].
"""
import sys
import pandas as pd
import numpy as np
import click

import urbanoccupants as uo
from urbanoccupants.types import AgeStructure, EconomicActivity


def map_age(age_val):
    """Map numeric age to AgeStructure enum."""
    try:
        a = int(age_val)
    except (ValueError, TypeError):
        return np.nan
    if a < 5:
        return AgeStructure.AGE_0_TO_4
    elif a < 8:
        return AgeStructure.AGE_5_TO_7
    elif a < 10:
        return AgeStructure.AGE_8_TO_9
    elif a < 15:
        return AgeStructure.AGE_10_TO_14
    elif a == 15:
        return AgeStructure.AGE_15
    elif a < 18:
        return AgeStructure.AGE_16_TO_17
    elif a < 20:
        return AgeStructure.AGE_18_TO_19
    elif a < 25:
        return AgeStructure.AGE_20_TO_24
    elif a < 30:
        return AgeStructure.AGE_25_TO_29
    elif a < 45:
        return AgeStructure.AGE_30_TO_44
    elif a < 60:
        return AgeStructure.AGE_45_TO_59
    elif a < 65:
        return AgeStructure.AGE_60_TO_64
    elif a < 75:
        return AgeStructure.AGE_65_TO_74
    elif a < 85:
        return AgeStructure.AGE_75_TO_84
    elif a < 90:
        return AgeStructure.AGE_85_TO_89
    else:
        return AgeStructure.AGE_90_AND_OVER


def map_dilodefr(val):
    """Map dilodefr (coarse 3-cat + 1) to EconomicActivity.
    
    dilodefr=1: Employed
    dilodefr=2: Unemployed/Looking for work
    dilodefr=3: Inactive
    dilodefr=4: Student
    """
    try:
        x = int(val)
    except (ValueError, TypeError):
        return np.nan
    if x == 1:
        return EconomicActivity.EMPLOYEE_FULL_TIME  # coarse: "employed"
    elif x == 2:
        return EconomicActivity.UNEMPLOYED  # "unemployed"
    elif x == 3:
        return EconomicActivity.INACTIVE_OTHER  # "inactive"
    elif x == 4:
        return EconomicActivity.ACTIVE_FULL_TIME_STUDENT  # "student"
    else:
        return np.nan


def map_worksta(val):
    """Fallback: map WorkSta to EconomicActivity."""
    try:
        x = int(val)
    except (ValueError, TypeError):
        return np.nan
    if x == 1:
        return EconomicActivity.EMPLOYEE_FULL_TIME
    elif x == 2:
        return EconomicActivity.EMPLOYEE_FULL_TIME
    elif x == 3:
        return EconomicActivity.SELF_EMPLOYED
    elif x == 4:
        return EconomicActivity.UNEMPLOYED
    elif x == 5:
        return EconomicActivity.ACTIVE_FULL_TIME_STUDENT
    elif x == 6:
        return EconomicActivity.RETIRED
    elif x == 7:
        return EconomicActivity.INACTIVE_FULL_TIME_STUDENT
    else:
        return np.nan


@click.command()
@click.argument('path_to_input')
@click.argument('path_to_output')
def read_seed_uktus15(path_to_input, path_to_output):
    """Read individual file and output seed pickle."""
    print(f"Reading individual file from: {path_to_input}")
    df = pd.read_csv(path_to_input, sep='\t', low_memory=False)
    
    # Verify required columns
    if not all(k in df.columns for k in ['serial', 'pnum']):
        print("ERROR: serial or pnum missing", file=sys.stderr)
        sys.exit(2)
    
    # Create index
    idx = pd.MultiIndex.from_arrays(
        [[1] * len(df), df['serial'].values, df['pnum'].values],
        names=['SN1', 'SN2', 'SN3']
    )
    seed = pd.DataFrame(index=idx)
    
    # Map AGE from DVAge
    if 'DVAge' not in df.columns:
        print("ERROR: DVAge column missing", file=sys.stderr)
        sys.exit(2)
    seed[str(uo.synthpop.PeopleFeature.AGE)] = df['DVAge'].apply(map_age).values
    
    # Map ECONOMIC_ACTIVITY: prefer dilodefr, fallback to WorkSta
    econ_source = None
    if 'dilodefr' in df.columns:
        econ_source = 'dilodefr'
        seed[str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)] = df['dilodefr'].apply(map_dilodefr).values
    elif 'WorkSta' in df.columns:
        econ_source = 'WorkSta'
        seed[str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)] = df['WorkSta'].apply(map_worksta).values
    else:
        print("ERROR: neither dilodefr nor WorkSta found", file=sys.stderr)
        sys.exit(2)
    
    # Report
    n_read = seed.shape[0]
    age_nonnull = seed[str(uo.synthpop.PeopleFeature.AGE)].notna().sum()
    econ_nonnull = seed[str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)].notna().sum()
    age_pct = 100.0 * age_nonnull / n_read
    econ_pct = 100.0 * econ_nonnull / n_read
    
    print(f"Read {n_read} individuals from {path_to_input}")
    print(f"Economic activity source: {econ_source}")
    print(f"Age non-null: {age_nonnull} ({age_pct:.1f}%)")
    print(f"Economic activity non-null: {econ_nonnull} ({econ_pct:.1f}%)")
    
    seed.to_pickle(path_to_output)
    print(f"Wrote seed to {path_to_output}")


if __name__ == '__main__':
    read_seed_uktus15()
