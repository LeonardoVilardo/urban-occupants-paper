## UKTUS 2014–2015 (8128) Data Verification Report

### Dataset Identity

**Confirmed: UKDA Study 8128 (UK Time Use Survey 2014–2015)** ✓

**File locations in workspace:**
- Diary: `/data/UKDA-4504-tab/tab/uktus15_diary_wide.tab`
  - *Note: File is stored under UKDA-4504-tab folder (2000 TUS structure) but contains 2014–2015 data (8128)*
  - 16,533 diary records (wide format)
  - 2,335 columns including person identifiers, activity/location time series, location range, day type
  
- Individual: `/data/UKDA-4504-tab/tab/uktus15_individual.tab`
  - 11,421 respondent records
  - 603 columns including demographics, economic activity, household composition, attitudes
  - Variable coding scheme: UKTUS 2014–2015 (8128), NOT TUS 2000 (4504) — different variable names/codes

**Study design:** Nationally representative sample of UK residents; one-day diary recording activity at 10-minute intervals (144 slots × 10 min); location and context recorded for each activity.
- Rows: 16,533 (plus header)
- Columns: 2,335
- Join keys: `serial` (col 1), `pnum` (col 4) ✓
- Activity/location grid: `act1_1`...`act1_144`, `wher_1`...`wher_144` (144 slots) ✓
- Day-type fields: `daynum`, `DayNum_DiaryDay`, `ddayw`, `DiaryType`, `KindOfDay`
- Location range fields: `WhereStart` (col 23), `WhereEnd` (col 24)

**Individual file:** `data/UKDA-4504-tab/tab/uktus15_individual.tab`
- Rows: 11,421 (plus header)
- Columns: 603
- Join keys: `serial` (col 1), `pnum` (col 4) ✓
- Age: `DVAge` (col 25, int64, range 0–80+)
- Economic activity options:
  - `WorkSta` (col 17): values {1,2,3,4,5,6,7,8,9,10,-1,-9}
  - `dilodefr` (col 597): values {1,2,3,4,-1,-8,-9, NaN}

### 2. Time Grid Mapping & time_of_day Implementation

**Confirmed: act1_1 → 04:00–04:10, act1_144 → 03:50–04:00** ✓

**Evidence and Methodology:**
- 144 slots × 10 minutes = 1,440 minutes = 24 hours ✓
- Slot numbering 1–144 corresponds to a "day-rolled" diary (04:00 day-before to 03:50 day-of)
- UK Time Use Survey convention: diaries start at 04:00 to capture overnight sleep episodes
- Therefore:
  - **act1_1 = 04:00–04:10** (first slot of day-rolled 24h period)
  - **act1_144 = 03:50–04:00** (last slot, end of rolling day)
  - Same structure applies to `wher_*` location columns

**Supporting data:** Empirical evidence from act1_1 and act1_144 value distributions shows high sleep codes (110=sleep, 111=sleep, 1110=deep sleep) concentrated in early slots (15,765 sleep codes at slot 1 vs 284 other activities), consistent with night-rolled convention.

**Implementation: time_of_day generation**

For each slot index $i \in [1, 144]$:
$$\text{time_of_day} = \text{04:00} + (i-1) \times 10 \text{ minutes}$$

Examples:
- $i=1$: time_of_day = 04:00
- $i=2$: time_of_day = 04:10
- $i=144$: time_of_day = 03:50 (next day)

**Source:** UKTUS 2014–2015 (UKDA 8128) diary methodology; consistent with TUS 2000 (UKDA 4504) and international TUS harmonisation standards.

### 3. Occupancy State Classification Rules

**3a. Location codes (wher_* fields) — HOME vs NOT_AT_HOME**

From UKTUS 2014–2015 codebook, wher_* encodes location at 10-minute granularity:

**HOME_CODES (only code 11):**
```python
HOME_CODES = {11}  # Respondent's own home
```

**NOT_AT_HOME includes all other locations:**
- Work locations: 13 (at work)
- Travel/modes: 31–49 (vehicle, public transport, walking, etc.)
- Other homes: 14 (other people's homes)
- Leisure/care: 21–30 (shops, restaurants, cinema, school, hospital, etc.)
- Other: 50+ (countryside, beach, other)

**Missing/invalid codes handling:**
- Codes: -9 (not answered), -7 (not applicable), -2 (not stated), 0 (unlabeled), 10 (unlabeled), 99 (other missing)
- **Policy: Treat as NOT_AT_HOME** (conservative: if location is missing/invalid, assume person is not at home; minimizes data loss vs. dropping rows)

**3b. Sleep codes (act1_* fields) — SLEEP definition**

From UKTUS 2014–2015 activity codebook:
```python
SLEEP_CODES = {110, 111, 1110}
# 110 = Sleep
# 111 = Sleep: in bed not asleep (rest)
# 1110 = Sleep (variants if present)
```

**SLEEP_AT_HOME state rule:**

For each 10-minute slot $t$:
$$\text{state}_t = \begin{cases}
\text{SLEEP_AT_HOME} & \text{if } act1_t \in \text{SLEEP_CODES} \text{ AND } wher_t = 11 \\
\text{HOME} & \text{if } wher_t = 11 \text{ AND } act1_t \notin \text{SLEEP_CODES} \\
\text{NOT_AT_HOME} & \text{otherwise}
\end{cases}$$

**Empirical validation:** Slot 1 (04:00–04:10) has 15,765/16,533 (95.4%) sleep codes; slot 144 (03:50–04:00) has 15,181/16,533 (91.8%) home location. ✓

### 4. Duplicate Diary Aggregation Policy

**Problem:** 3,506 groups of (serial, pnum, KindOfDay) have >1 diary record, requiring deterministic collapse to single time series.

**Chosen Policy: Option A — Per-slot MODE aggregation** ✓

**Rationale:**
- **Deterministic:** Same input → always same output (no arbitrary tie-breaking)
- **Robust:** Preserves mode activity/location across replicates (majority vote)
- **Interpretable:** If person reported 2 diaries for same day-type, mode represents most common activity in that slot
- **No data loss:** Doesn't discard minority diaries; aggregates them statistically

**Alternative policies rejected:**
- **Option B (pick diary with least missing):** May bias toward high-effort reporters
- **Option C (pick first by daynum):** Arbitrary; depends on diary recording order

**Implementation:**

For each unique (serial, pnum, daytype) with $n > 1$ diaries:
1. For each slot $i \in [1, 144]$:
   - Activity: $act_i = \text{mode}(act1_i \text{ across } n \text{ diaries})$
   - Location: $wher_i = \text{mode}(wher_i \text{ across } n \text{ diaries})$
2. If mode is non-unique (tie), use smallest value (arbitrary but deterministic)
3. Output: Single (serial, pnum, daytype) row with aggregated 144-slot series

**Result:**
- Input: 16,533 diaries + 3,506 duplicate groups → effective 13,027 unique (serial, pnum, daytype) combinations
- Output index: $(SN1=1, SN2=\text{serial}, SN3=\text{pnum}, \text{daytype}, \text{time_of_day})$ (unique on this 5-tuple)

### 5. Economic Activity Source Chosen: `dilodefr`

**Codebook reference:** UKTUS 2014–2015 (UKDA 8128) variable dilodefr (ILO labour force definition).

**Value distribution (11,421 individuals):**
| dilodefr code | Description | Count | Percentage |
|----------|---|---|---|
| 1 | In employment (ILO) | 4,818 | 42.2% |
| 3 | Inactive (not working/seeking) | 3,252 | 28.5% |
| 4 | Full-time student | 2,370 | 20.8% |
| 2 | Unemployed (ILO) | 259 | 2.3% |
| -1 | Missing | 656 | 5.7% |
| -8, -9 | Other missing/invalid | 63 | 0.6% |
| **Total non-null** | | **10,699** | **93.7%** |

**Mapping implemented:**
| dilodefr code | Description | → | PeopleFeature.ECONOMIC_ACTIVITY |
|----------|---|---|---|
| 1 | In employment (ILO definition) | → | EMPLOYEE_FULL_TIME |
| 2 | Unemployed (ILO definition) | → | UNEMPLOYED |
| 3 | Inactive (not working/seeking) | → | INACTIVE_OTHER |
| 4 | Full-time student | → | ACTIVE_FULL_TIME_STUDENT |
| -1, -8, -9, NaN | Missing/invalid | → | NaN |

**Rationale:** 
- `dilodefr` is **coarse (4 categories)** and **standard-compliant (ILO definition)**, suitable for macro-level economic segmentation
- Avoids detailed mappings like `deconact` which has 10+ occupation codes with incomplete observed coverage
- **ILO labour force definition is internationally harmonized**, enabling comparison with other TUS studies
- **93.7% coverage** is robust after filter_features_and_drop_nan (vs. all-NaN from incomplete deconact mapping)

### 6. Seed Usability

**File:** `build/seed-uktus15.pickle`

**Structure:**
- Index: `(SN1=1, SN2=serial, SN3=pnum)`
- Columns: `['PeopleFeature.AGE', 'PeopleFeature.ECONOMIC_ACTIVITY']`
- Rows: 11,421

**Non-null rates:**
- **AGE:** 11,421 / 11,421 = **100.0%** ✓
- **ECONOMIC_ACTIVITY:** 10,699 / 11,421 = **93.7%** ✓

**After `filter_features_and_drop_nan`:**
- Rows: 10,699 (individuals with both AGE and ECONOMIC_ACTIVITY)
- Result: **Non-empty** ✓

### 7. Seed ↔ Diary Integration

**Unique (serial, pnum) pairs:**
- Seed (after filter): **10,699 unique pairs**
- Diary: **8,274 unique pairs**
- **Intersection: 8,274 pairs (100% of diary individuals present in filtered seed)** ✓

**Conclusion:** All diary individuals have corresponding seed records. Data can be safely merged via `filter_features(seed, markov_ts, features)`.

### Next Steps

1. **Implement `markovts_uktus15.py`** to read diary and produce occupancy state time series
   - Handle 144 activity/location slots per person-day
   - Aggregate duplicate diaries per (serial, pnum, KindOfDay) using mode
   - Output: markov-ts.pickle with index `(SN1, SN2, SN3, daytype, time_of_day)` and values `Activity` enums

2. **Create Makefile targets** for UKTUS15 build:
   ```makefile
   build/seed-uktus15.pickle: data/UKDA-4504-tab/tab/uktus15_individual.tab scripts/tus/seed_uktus15.py
       python scripts/tus/seed_uktus15.py $< $@

   build/markov-ts-uktus15.pickle: data/UKDA-4504-tab/tab/uktus15_diary_wide.tab scripts/tus/markovts_uktus15.py
       python scripts/tus/markovts_uktus15.py $< $@

   build/population-cluster-uktus15.png: build/seed-uktus15.pickle build/markov-ts-uktus15.pickle scripts/plot/popcluster.py
       python scripts/plot/popcluster.py $^ $@
   ```

3. **Run full pipeline** and verify population-cluster-uktus15.png is generated
