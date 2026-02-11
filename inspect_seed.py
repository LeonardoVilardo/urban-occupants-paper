import pickle
import pandas as pd

seed = pickle.load(open('build/seed-uktus15.pickle', 'rb'))
print("Seed shape:", seed.shape)
print("Seed columns:", list(seed.columns))
print("Seed dtypes:")
print(seed.dtypes)
print("\nFirst 10 rows (raw):")
print(seed.head(10))
print("\nSample of first column values:")
for i in range(min(20, len(seed))):
    val = seed.iloc[i, 0]
    print(f"  [{i}] {repr(val)} (type: {type(val).__name__})")
