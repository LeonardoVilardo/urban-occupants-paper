import pandas as pd
import numpy as np

df = pd.read_csv('data/UKDA-4504-tab/tab/uktus15_individual.tab', sep='\t', low_memory=False, nrows=50)

print("DVAge column info:")
print("  dtype:", df['DVAge'].dtype)
print("  sample values:", df['DVAge'].head(10).tolist())
print("  any NaN?", df['DVAge'].isna().sum())

print("\ndilodefr column info:")
print("  dtype:", df['dilodefr'].dtype)
print("  sample values:", df['dilodefr'].head(10).tolist())
print("  any NaN?", df['dilodefr'].isna().sum())

# try the mapping directly
from scripts.tus.seed_uktus15 import map_age, map_dilodefr

print("\nDirect map_age on first 10 DVAge values:")
for i, v in enumerate(df['DVAge'].head(10)):
    result = map_age(v)
    print(f"  map_age({v}) = {result}")

print("\nDirect map_dilodefr on first 10 dilodefr values:")
for i, v in enumerate(df['dilodefr'].head(10)):
    result = map_dilodefr(v)
    print(f"  map_dilodefr({v}) = {result}")
