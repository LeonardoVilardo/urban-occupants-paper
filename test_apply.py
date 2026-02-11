import pandas as pd
import urbanoccupants as uo
from scripts.tus.seed_uktus15 import map_age, map_dilodefr

df = pd.read_csv('data/UKDA-4504-tab/tab/uktus15_individual.tab', sep='\t', low_memory=False, nrows=50)

# Test apply
print("Test applying map_age:")
result = df['DVAge'].apply(map_age)
print("Type of result:", type(result))
print("Result dtype:", result.dtype)
print("First 10 values of result:")
print(result.head(10).tolist())

# Put in a DataFrame and check
test_df = pd.DataFrame(index=pd.RangeIndex(len(df)))
test_df['age'] = result
print("\nDataFrame with applied mapping:")
print(test_df.head(10))
print("Non-null count:", test_df['age'].notna().sum())

# Alternative: use a Series and convert properly
idx = pd.MultiIndex.from_arrays([[1]*len(df), df['serial'].values, df['pnum'].values], names=['SN1','SN2','SN3'])
seed = pd.DataFrame(index=idx)
seed[str(uo.synthpop.PeopleFeature.AGE)] = df['DVAge'].apply(map_age).values
print("\nAfter assigning via .values:")
print(seed.head(10))
print("Non-null count:", seed.iloc[:,0].notna().sum())
