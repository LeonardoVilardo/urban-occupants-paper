import pickle
import pandas as pd

seed = pickle.load(open('build/seed-uktus15.pickle', 'rb'))
print("Seed index info:")
print("  names:", seed.index.names)
print("  nlevels:", seed.index.nlevels)
print("  First 5 index tuples:")
for i in range(5):
    print("   ", seed.index[i])

diary = pd.read_csv('data/UKDA-4504-tab/tab/uktus15_diary_wide.tab', sep='\t', low_memory=False, usecols=['serial', 'pnum'])
print("\nDiary (serial, pnum) pairs (first 5):")
for i in range(5):
    print("   ", (diary.iloc[i]['serial'], diary.iloc[i]['pnum']))

# Check if (serial, pnum) as tuples match
seed_tuples = set((idx[1], idx[2]) for idx in seed.index)  # take SN2, SN3 from (SN1, SN2, SN3)
diary_pairs = set(zip(diary['serial'], diary['pnum']))
print(f"\nSeed (SN2, SN3) tuples: {len(seed_tuples)}")
print(f"Diary (serial, pnum) pairs: {len(diary_pairs)}")
overlap = seed_tuples & diary_pairs
print(f"Overlap: {len(overlap)}")

if len(overlap) > 0:
    print("Sample overlap (first 5):")
    for i, pair in enumerate(list(overlap)[:5]):
        print("   ", pair)
