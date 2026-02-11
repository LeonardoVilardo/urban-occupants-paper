# Summary of Changes for Urban Occupants Legacy Environment

All changes have been successfully implemented. Here's what was done:

## 1. New Conda Environment File

**File**: [conda-environment-legacy.yml](./conda-environment-legacy.yml)

A brand-new conda environment configuration with:
- **Python 3.7** (balance between legacy compatibility and modern improvements)
- **Core numerics**: numpy 1.21.*, pandas 1.3.*, scipy 1.7.*
- **Geo stack** (conda-forge only, pinned for binary compatibility):
  - gdal 2.2.*
  - fiona 1.7.*
  - geopandas 0.5.*
  - shapely 1.7.*
  - pyproj 2.4.*
  - poppler 0.71.*
  - giflib 5.1.*
- **Git dependencies**: pytus2000@v0.5.1, Pykov

**Setup**:
```bash
cd /Users/leovilardo/urban-occupants-paper
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml
conda activate urban-occupants-legacy
```

## 2. Code Changes

### [urbanoccupants/urbanoccupants/census.py](./urbanoccupants/urbanoccupants/census.py)

**Change**: Moved geopandas import from module level into the function that uses it.

**Before** (line 19):
```python
import geopandas as gpd
```

**After** (now inside `read_haringey_shape_file`, line 162):
```python
def read_haringey_shape_file(geographical_layer=GeographicalLayer.LSOA):
    """Reads shape file of Haringey from London Data Store."""
    import geopandas as gpd  # ← Moved here
    ...
```

**Benefit**:
- `import urbanoccupants` now succeeds even if geopandas has import errors
- Makes geopandas optional for code paths that don't call `read_haringey_shape_file()`
- Isolates binary compatibility issues to only the geo-specific function

---

### [urbanoccupants/tests/test_markov_chain.py](./urbanoccupants/tests/test_markov_chain.py)

**Change**: Updated pandas import on line 8.

**Before**:
```python
from pandas.util.testing import assert_frame_equal
```

**After**:
```python
from pandas.testing import assert_frame_equal
```

**Reason**: `pandas.util.testing` was removed in pandas 1.0+. Modern API uses `pandas.testing`.

---

### [urbanoccupants/tests/test_hipf_with_toy_example.py](./urbanoccupants/tests/test_hipf_with_toy_example.py)

**Change**: Updated pandas import on line 12.

**Before**:
```python
from pandas.util.testing import assert_series_equal
```

**After**:
```python
from pandas.testing import assert_series_equal
```

**Reason**: Same as above.

---

### [urbanoccupants/tests/test_hipf_with_two_controls.py](./urbanoccupants/tests/test_hipf_with_two_controls.py)

**Change**: Updated pandas import on line 15.

**Before**:
```python
from pandas.util.testing import assert_series_equal
```

**After**:
```python
from pandas.testing import assert_series_equal
```

**Reason**: Same as above.

---

## 3. Comprehensive Setup Guide

**File**: [LEGACY_ENVIRONMENT_SETUP.md](./LEGACY_ENVIRONMENT_SETUP.md)

A detailed guide covering:
- Problem summary and root causes
- Environment creation and verification
- Five escalation options for conda solver conflicts
  1. Relax non-critical constraints
  2. Downgrade fiona & gdal together
  3. Remove pinned version on one dependency
  4. Use strict channel priority
  5. Last resort: upgrade to Python 3.8
- Troubleshooting common macOS issues (dyld, binary mismatches, missing libs)
- Future maintenance recommendations

---

## How to Proceed

### Quick Start
```bash
cd /Users/leovilardo/urban-occupants-paper
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml
conda activate urban-occupants-legacy

# Verify installation
python -c "import pandas; import geopandas; print('✓ Both imports OK')"
pytest urbanoccupants/tests/ -v
```

### If Conda Solver Fails
Refer to **LEGACY_ENVIRONMENT_SETUP.md**, section "If Conda Solver Fails" for detailed escalation steps.

### If Tests Still Fail
- Check that you used `CONDA_SUBDIR=osx-64` (critical for macOS binary compatibility)
- Verify `python --version` outputs 3.7.x
- Verify `python -c "import pandas; print(pandas.__version__)"` outputs 1.3.x
- See LEGACY_ENVIRONMENT_SETUP.md for troubleshooting

---

## Files Changed

| File | Change Type | Lines |
|------|-------------|-------|
| conda-environment-legacy.yml | **NEW** | 50 |
| LEGACY_ENVIRONMENT_SETUP.md | **NEW** | 400+ |
| urbanoccupants/urbanoccupants/census.py | Import moved (1 line) | 19 → 162 |
| urbanoccupants/tests/test_markov_chain.py | Import updated | 8 |
| urbanoccupants/tests/test_hipf_with_toy_example.py | Import updated | 12 |
| urbanoccupants/tests/test_hipf_with_two_controls.py | Import updated | 15 |

---

## Key Design Decisions

1. **Python 3.7** (not 3.6): Python 3.6 reached end-of-life in Dec 2021. Using 3.7 gives security patches while maintaining good legacy compatibility.

2. **conda-forge only**: Avoids binary mismatches from mixing channels. The geo stack (GDAL, fiona, poppler) is particularly sensitive to this.

3. **Pinned patch versions** (e.g., `gdal=2.2.*`): Locks major.minor but allows patch updates. Balances reproducibility with security.

4. **Lazy geopandas import**: Most scripts in this repo don't use geo features. Deferring the import makes the module usable even if geopandas is broken.

5. **Clear escalation path**: Instead of a single "magic" environment, the guide explains *how* to fix conflicts, not just what to do.

---

## Testing Checklist

- [ ] Environment creates without errors (run `conda env create -f conda-environment-legacy.yml`)
- [ ] `import urbanoccupants` works
- [ ] `import geopandas` works (only needed if using geo functions)
- [ ] `pytest urbanoccupants/tests/` passes all 4 test files
- [ ] Scripts in `scripts/` execute without import errors
- [ ] `make paper` completes (full pipeline test, may take hours)
