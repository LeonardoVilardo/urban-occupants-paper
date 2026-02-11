from datetime import time

import pandas as pd

from .utils import time_mapper
from .datadicts import diary


def transform_diary_data_to_timeseries(diary_data):
    """Transforms the diary data set to a timeseries.

    Parameters:
        * diary_data: the diary data as pandas Dataframe

    Returns:
        The time varying columns of the diary data set as a pandas DataFrame time series.
    """
    ac_loc = pd.DataFrame(
        {
            'activity': diary_data['ACT1_001'],
            'location': diary_data['WHER_001'],
            'secondary_activity': diary_data['ACT2_001'],
            'who_with_adult0': diary_data['WIT0_001'],
            'who_with_adult1': diary_data['WIT1_001'],
            'who_with_adult2': diary_data['WIT2_001'],
            'who_with_adult3': diary_data['WIT3_001'],
            'who_with_adult4': diary_data['WIT4_001'],
            'who_with_adult5': diary_data['WIT5_001'],
            'who_with_adult6': diary_data['WIT6_001'],
            'who_with_child0': diary_data['KID01'],
            'who_with_child1': diary_data['KID11'],
            'who_with_child2': diary_data['KID21'],
            'who_with_child3': diary_data['KID31'],
            'who_with_child4': diary_data['KID41'],
            'who_with_child5': diary_data['KID51'],
            'time_of_day': pd.Series([time(4, 0)] * len(diary_data), index=diary_data.index)
        },
        dtype='category'
    )

    for i in range(2, 145):
        time_of_day = time_mapper(i)
        next_frame = pd.DataFrame(
            {
                'activity': diary_data['ACT1_{:0>3}'.format(i)],
                'location': diary_data['WHER_{:0>3}'.format(i)],
                'secondary_activity': diary_data['ACT2_{:0>3}'.format(i)],
                'who_with_adult0': diary_data['WIT0_{:0>3}'.format(i)],
                'who_with_adult1': diary_data['WIT1_{:0>3}'.format(i)],
                'who_with_adult2': diary_data['WIT2_{:0>3}'.format(i)],
                'who_with_adult3': diary_data['WIT3_{:0>3}'.format(i)],
                'who_with_adult4': diary_data['WIT4_{:0>3}'.format(i)],
                'who_with_adult5': diary_data['WIT5_{:0>3}'.format(i)],
                'who_with_adult6': diary_data['WIT6_{:0>3}'.format(i)],
                'who_with_child0': diary_data['KID0{}'.format(i)],
                'who_with_child1': diary_data['KID1{}'.format(i)],
                'who_with_child2': diary_data['KID2{}'.format(i)],
                'who_with_child3': diary_data['KID3{}'.format(i)],
                'who_with_child4': diary_data['KID4{}'.format(i)],
                'who_with_child5': diary_data['KID5{}'.format(i)],
                'time_of_day': pd.Series([time_of_day] * len(diary_data), index=diary_data.index),
            },
            dtype='category'
        )
        ac_loc = ac_loc.append(next_frame, ignore_index=False)

    ac_loc['activity'] = pd.Series(
        pd.Categorical(ac_loc['activity'], categories=[ac for ac in diary.ACT1_001]),
        index=ac_loc.index
    )
    ac_loc['secondary_activity'] = pd.Series(
        pd.Categorical(ac_loc['secondary_activity'], categories=[ac for ac in diary.ACT2_001]),
        index=ac_loc.index
    )
    ac_loc['location'] = pd.Series(
        pd.Categorical(ac_loc['location'], categories=[loc for loc in diary.WHER_001]),
        index=ac_loc.index
    )
    ac_loc['time_of_day'] = ac_loc['time_of_day'].astype('category')
    ac_loc = ac_loc.set_index(['time_of_day'], drop=True, append=True)
    ac_loc = ac_loc.sort_index()
    return ac_loc
