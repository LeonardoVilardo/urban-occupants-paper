import pickle
import pandas as pd
import urbanoccupants as uo

# Load seed (after filter_features_and_drop_nan)
seed = pickle.load(open('build/seed-uktus15.pickle', 'rb'))
features = [str(uo.synthpop.PeopleFeature.AGE), str(uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY)]
seed_filtered = uo.tus.filter_features_and_drop_nan(seed, features)

print(f"Seed after filter: {seed_filtered.shape}")
seed_pairs = set(seed_filtered.index)
print(f"Unique (SN2, SN3) pairs in seed: {len(seed_pairs)}")

# Load diary and check unique pairs
diary = pd.read_csv('data/UKDA-4504-tab/tab/uktus15_diary_wide.tab', sep='\t', low_memory=False, usecols=['serial', 'pnum'])
diary_pairs = set(zip(diary['serial'], diary['pnum']))
print(f"Unique (serial, pnum) pairs in diary: {len(diary_pairs)}")

# Intersection
overlap = seed_pairs & diary_pairs
print(f"Intersection size: {len(overlap)}")
print(f"Overlap %: {100.0 * len(overlap) / len(diary_pairs):.1f}%")

if len(overlap) > 0:
    print("✓ Good overlap (seed and diary share indices)")
else:
    print("✗ No overlap - indices don't match")
