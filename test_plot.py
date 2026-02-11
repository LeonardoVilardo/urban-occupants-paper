import pandas as pd
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import urbanoccupants as uo
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

seed = pd.read_pickle('build/seed-uktus15.pickle')
markov_ts = pd.read_pickle('build/markov-ts-uktus15.pickle')

ALL_FEATURES = [
    uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY,
    uo.synthpop.PeopleFeature.AGE
]

seed_filtered, markov_ts_filtered = uo.tus.filter_features(seed, markov_ts, ALL_FEATURES)

# Convert to numerical
mapping = {
    uo.Activity.HOME: 1.0,
    uo.Activity.SLEEP_AT_HOME: 0.5,
    uo.Activity.NOT_AT_HOME: 0
}
markov_ts_num = markov_ts_filtered.map(mapping)

# Unstack
unstacked = markov_ts_num.unstack(['SN1', 'SN2', 'SN3'])
print('Unstacked shape:', unstacked.shape)
print('Unstacked index levels:', unstacked.index.names)
print('Unstacked columns:', len(unstacked.columns), 'people')
print('Unstacked any NaN:', unstacked.isnull().any().any())
print('Unstacked sample:\n', unstacked.iloc[:5, :3])

# Try to reproduce the error
try:
    filtered = gaussian_filter(unstacked, sigma=0.7)
    print('\nFiltered array shape:', filtered.shape)
    print('Filtered min/max:', filtered.min(), filtered.max())
    print('Filtered all zeros:', (filtered == 0).all())
    print('Filtered any NaN:', np.isnan(filtered).any())
    
    # Now try heatmap without display
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(filtered, cbar=False, ax=ax)
    fig.savefig('/tmp/test_heatmap.png')
    print('\nSUCCESS: heatmap created and saved')
except Exception as e:
    import traceback
    print('\nERROR:', type(e).__name__)
    print(str(e))
    traceback.print_exc()
