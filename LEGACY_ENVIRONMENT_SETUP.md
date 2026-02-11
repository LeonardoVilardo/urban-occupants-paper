# Urban Occupants Legacy Environment Setup Guide

## Overview
This document explains how to set up a clean conda environment for the `urban-occupants-paper` repository on macOS using Python 3.7 and a compatible legacy software stack (circa 2017–2018).

## Problem Summary
The original repository expected Python 3.6 with pandas 0.19.2, numpy 1.12.1, and geopandas 0.2.1. Modern resolvers break because:
- **pandas.util.testing** was removed in pandas 1.0+ (use `pandas.testing` instead)
- **geopandas import at module level** causes failures if not installed; better to import only where needed
- **Geo stack binary mismatches** on macOS when mixing conda channels or using incompatible GDAL/poppler versions

## New Environment: `conda-environment-legacy.yml`

The new environment file pins:
- **Python 3.7** (latest in 3.7.x series, good balance of modernity vs. legacy compatibility)
- **numpy 1.21.x** (last compatible with scipy 1.7 and pandas 1.3)
- **pandas 1.3.x** (supports modern API but still compatible with legacy code patterns)
- **scipy 1.7.x** (last series before major breaking changes)
- **Geo stack (conda-forge only)**:
  - gdal 2.2.* 
  - fiona 1.7.*
  - geopandas 0.5.*
  - shapely 1.7.*
  - pyproj 2.4.*
  - poppler 0.71.*
  - giflib 5.1.*

All packages use **conda-forge** exclusively to ensure binary compatibility on macOS (no mixing with defaults channel).

## How to Use

### 1. Create the Environment

```bash
# Navigate to repository root
cd /Users/leovilardo/urban-occupants-paper

# Remove old broken environment if needed
conda env remove -n urban-occupants-legacy

# Create fresh environment with strict macOS 64-bit resolution
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml
conda activate urban-occupants-legacy
```

The `CONDA_SUBDIR=osx-64` flag ensures conda explicitly uses 64-bit macOS packages and avoids mixed-architecture issues.

### 2. If Conda Solver Fails

If conda's solver complains about incompatible versions (e.g., "fiona 1.7 requires gdal 2.1, got 2.2"), follow this escalation:

#### Option A: Relax non-critical constraints
For example, if the solver complains about matplotlib or seaborn:
```yaml
- matplotlib=3.*        # Instead of 3.3.*
- seaborn=0.*         # Instead of 0.11.*
```
Re-run:
```bash
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml --force
```

#### Option B: Downgrade fiona & gdal together
If fiona/gdal conflict, try:
```yaml
- gdal=2.1.*          # Instead of 2.2.*
- fiona=1.6.*         # Pair with 2.1
```

#### Option C: Remove pinned version on one dependency
Comment out the patch version for fiona to let conda choose:
```yaml
- fiona=1.*           # Let conda pick 1.7 or 1.6
- gdal=2.2.*
```

#### Option D: Use strict channel priority
Add this to your conda config (`~/.condarc`):
```yaml
channel_priority: strict
channels:
  - conda-forge
  - defaults
```
Then retry. This prevents cross-channel contamination.

#### Option E: Last resort — use Python 3.8
If the entire Python 3.7 stack conflicts, upgrade:
```yaml
- python=3.8
- numpy=1.21.*
- pandas=1.3.*
```
(Python 3.8 released Dec 2019, still compatible with 2017–2018 code in most cases)

### 3. Install Development Dependencies

After environment creation, the pip packages are installed automatically:
- `pytus2000@v0.5.1` (from Git)
- `Pykov` (from Git)
- `./urbanoccupants/` (local editable install)
- `pandoc-*` plugins

### 4. Verify Installation

```bash
# Check Python & pandas versions
python --version              # Should show 3.7.x
python -c "import pandas; print(pandas.__version__)"  # Should show 1.3.x

# Test imports
python -c "from urbanoccupants import Activity; print('OK')"

# Run tests
cd urbanoccupants
pytest tests/ -v
```

## Code Changes Made

### 1. [urbanoccupants/census.py](../urbanoccupants/urbanoccupants/census.py)

**Problem**: `import geopandas as gpd` at module level caused failures if geopandas wasn't installed or had binary issues.

**Solution**: Move import inside the single function that uses it.

**Change**:
```python
# Before (line 19):
import geopandas as gpd

# After: Removed from module-level imports, added inside function:
def read_haringey_shape_file(geographical_layer=GeographicalLayer.LSOA):
    """Reads shape file of Haringey from London Data Store."""
    import geopandas as gpd  # ← Added here
    ...
```

**Impact**: 
- `import urbanoccupants` now succeeds even if geopandas fails to import
- Only code paths that actually call `read_haringey_shape_file()` will fail if geopandas is broken
- Makes geopandas truly optional for scripts that don't use geographical features

### 2. [urbanoccupants/tests/test_markov_chain.py](../urbanoccupants/tests/test_markov_chain.py) (line 8)

**Problem**: `from pandas.util.testing import assert_frame_equal` doesn't exist in pandas 1.0+

**Solution**: Use `pandas.testing` instead

```python
# Before:
from pandas.util.testing import assert_frame_equal

# After:
from pandas.testing import assert_frame_equal
```

### 3. [urbanoccupants/tests/test_hipf_with_toy_example.py](../urbanoccupants/tests/test_hipf_with_toy_example.py) (line 12)

**Problem**: Same as above

**Solution**:
```python
# Before:
from pandas.util.testing import assert_series_equal

# After:
from pandas.testing import assert_series_equal
```

### 4. [urbanoccupants/tests/test_hipf_with_two_controls.py](../urbanoccupants/tests/test_hipf_with_two_controls.py) (line 15)

**Problem**: Same as above

**Solution**:
```python
# Before:
from pandas.util.testing import assert_series_equal

# After:
from pandas.testing import assert_series_equal
```

## Troubleshooting

### Symptom: `ModuleNotFoundError: No module named 'pandas.util.testing'`
**Fix**: Use `python -m pytest` instead of `pytest` to ensure the correct Python path. Or reinstall the environment.

### Symptom: `libgif.7.dylib` or `libpoppler.71.dylib` not found
**Fix**: This indicates binary mismatches. Ensure you used `CONDA_SUBDIR=osx-64` and conda-forge only. Rebuild:
```bash
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml --force
```

### Symptom: `ImportError: cannot import name 'diary' from 'pytus2000'`
**Fix**: The Git tag `v0.5.1` of pytus2000 may need to be installed with `pip install --no-deps` first, then dependencies added manually. Try:
```bash
pip install git+https://github.com/timtroendle/pytus2000@v0.5.1 --no-deps
pip install pytus2000-dependencies  # Check what's actually needed
```
Refer to pytus2000 repo's `setup.py` for exact dependencies.

### Symptom: Fiona fails to build on macOS (linking errors)
**Fix**: Pre-built wheels for fiona on conda-forge may be stale. Try:
```bash
conda remove fiona gdal -y
CONDA_SUBDIR=osx-64 conda install fiona=1.7 gdal=2.2 -c conda-forge --force
```

### Symptom: Tests still fail with deprecated pandas warnings
**Fix**: Ignore them for now; they indicate code patterns that are deprecated but still work. To silence:
```bash
pytest tests/ -W ignore::DeprecationWarning
```

## Future Maintenance

If you need to update this environment:
1. **Never mix channels**: Always use `conda-forge` only; avoid `defaults`
2. **Test geo imports separately**: Try `python -c "import geopandas; print('OK')"` after any change
3. **Pin numpy & scipy together**: They must be compatible; always test `import scipy` after updating numpy
4. **Use CONDA_SUBDIR=osx-64 always**: Makes reproducibility easier

## References

- Original repo pins (from `conda-environment.yml`): Python 3.6, pandas 0.19.2, geopandas 0.2.1
- pandas API migration: https://pandas.pydata.org/docs/whatsnew/v1.0.0.html#deprecations-removals
- conda-forge packages: https://conda-forge.org
- GDAL/fiona compatibility: https://github.com/Toblerity/Fiona/releases
