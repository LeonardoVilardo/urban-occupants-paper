# Quick Reference: Legacy Environment Setup

## TL;DR – Get Started in 30 Seconds

```bash
cd /Users/leovilardo/urban-occupants-paper
CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml
conda activate urban-occupants-legacy
pytest urbanoccupants/tests/ -v
```

---

## Environment Specs

| Component | Version |
|-----------|---------|
| Python | 3.7.x |
| pandas | 1.3.x |
| numpy | 1.21.x |
| scipy | 1.7.x |
| geopandas | 0.5.x |
| gdal | 2.2.x |
| fiona | 1.7.x |

All packages: **conda-forge only** (no mixing with defaults)

---

## What Was Fixed

1. **census.py**: Moved geopandas import inside function (makes import optional)
2. **3 test files**: Changed `pandas.util.testing` → `pandas.testing` (pandas 1.0+ API)
3. **New conda YAML**: Replaces old Python 3.6 environment with clean Python 3.7 stack

---

## If Conda Solver Fails

1. **Check exact error message**:
   ```bash
   CONDA_SUBDIR=osx-64 conda env create -f conda-environment-legacy.yml 2>&1 | tail -20
   ```

2. **Most common**: "fiona 1.7 requires gdal 2.1"
   - Try relaxing fiona: change `fiona=1.7.*` to `fiona=1.*` in YAML, retry
   - Or downgrade both: `fiona=1.6.*` + `gdal=2.1.*`

3. **Last resort**:
   - Use Python 3.8: change `python=3.7` to `python=3.8` in YAML
   - Or check LEGACY_ENVIRONMENT_SETUP.md for 5 escalation options

---

## Verify Installation

```bash
# Check versions
python --version                    # Must be 3.7.x
python -c "import pandas; print(pandas.__version__)"  # Must be 1.3.x

# Check key imports
python -c "from urbanoccupants import Activity; print('✓')"
python -c "import geopandas; print('✓')"

# Run all tests
pytest urbanoccupants/tests/ -v
```

**Expected output**: 4 test files pass (markov_chain, hipf_toy_example, hipf_two_controls, person/features)

---

## Files to Know

| File | Purpose |
|------|---------|
| `conda-environment-legacy.yml` | New clean environment (use this, not old `conda-environment.yml`) |
| `LEGACY_ENVIRONMENT_SETUP.md` | Detailed guide (read if problems occur) |
| `CHANGES_SUMMARY.md` | What changed and why |
| `CODE_DIFF_REFERENCE.md` | Exact code diffs (for reference) |

---

## Common Issues & Fixes

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: pandas.util.testing` | Tests should pass now (updated to pandas.testing) |
| `libgif.7.dylib not found` | Use `CONDA_SUBDIR=osx-64` prefix; rebuild env |
| `geopandas import fails but rest of code works` | Good! That's expected (lazy import). Only fails if you call `read_haringey_shape_file()` |
| Solver timeout (>10 min) | Kill and retry: `conda env remove -n urban-occupants-legacy` then recreate |

---

## Optional Cleanup

Remove old broken environments if they exist:
```bash
conda env remove -n urban-occupants          # Old one
conda env remove -n urban-occupants-legacy   # If you're redoing setup
```

---

## Key Points to Remember

✓ **Always use** `CONDA_SUBDIR=osx-64` on macOS (enables 64-bit resolution)  
✓ **Never mix** conda-forge with defaults channel  
✓ **Pin together**: numpy + scipy must be compatible versions  
✓ **Test imports separately**: geopandas is optional, gdal is not (for geo features)  
✓ **Refer to** LEGACY_ENVIRONMENT_SETUP.md if anything breaks  

---

## Next Steps

1. Create the environment (30 sec)
2. Run tests to verify (2 min)
3. If tests pass: ready to use `make paper` or run individual scripts
4. If tests fail: check error message, see "If Conda Solver Fails" above

---

*For detailed troubleshooting, solutions to dependency conflicts, and background on why these versions were chosen, see **LEGACY_ENVIRONMENT_SETUP.md**.*
