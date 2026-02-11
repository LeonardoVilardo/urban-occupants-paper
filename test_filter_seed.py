import pickle
import pandas as pd
import urbanoccupants as uo

seed = pickle.load(open('build/seed-uktus15.pickle', 'rb'))
print("Seed shape before filter:", seed.shape)
print("Seed columns:", list(seed.columns))
print("Non-null before filter:")
print("  AGE:", seed[str(uo.synthpop.PeopleFeature.AGE)].notna().sum())
print("  ECON:", seed[str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)].notna().sum())

# Apply filter_features_and_drop_nan
features = [str(uo.synthpop.PeopleFeature.AGE), str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)]
seed_filtered = uo.tus.filter_features_and_drop_nan(seed, features)
print(f"\nAfter filter_features_and_drop_nan({features}):")
print(f"  Seed shape: {seed_filtered.shape}")
print(f"  Rows: {seed_filtered.shape[0]}")

if seed_filtered.shape[0] > 0:
    print("✓ Filter produced non-empty result!")
else:
    print("✗ Filter produced empty result (all rows dropped)")
