# Copilot instructions for this repository

This file is a concise guide for AI coding assistants to be productive in this repository.

**Quick summary**
- Project purpose: research scripts + a small Python library (`urbanoccupants`) to create and analyse synthetic occupancy data and run an external energy simulation Java jar.
- Main workflows: data preparation (`scripts/tus/*`), building simulation inputs (`scripts/simulationinput.py`), running the Java simulator (`scripts/runsim.py`), plotting and building paper (`Makefile`).

**How to run / debug locally**
- Create the conda environment: `conda env create -f conda-environment.yml` (or `conda-environment-patched.yml`).
- Build inputs and run full pipeline: `make paper` (may take hours and downloads an external jar).
- Run tests: `make test` (invokes `py.test`).
- Generate simulation DB only: `make build/sim-input.db` and then `python scripts/runsim.py <jar> <sim-input.db> <sim-output.db> config/default.yaml`.

**Important files & what they contain (examples to open first)**
- `README.md`: project overview and data requirements.
- `Makefile`: canonical build/test/run recipes used by maintainers.
- `config/*.yaml`: simulation parameter sets; consumed by `urbanoccupants.utils.read_simulation_config`.
- `scripts/simulationinput.py`: orchestration that creates `build/sim-input.db` (shows DB table names, sampling flow and multiprocessing pattern).
- `scripts/runsim.py`: wrapper that launches the Java simulator jar.
- `urbanoccupants/hipf.py`: numerical algorithm (HIPF) used to fit weights — good reference for numerical/dataframe expectations.
- `urbanoccupants/tus.py`: maps raw TUS values to enums; many mapping dicts and the `markov_chain_for_cluster` factory.
- `urbanoccupants/synthpop.py`: example use of `fit_hipf`, `sample_households`, `feature_id` and multiprocessing param-tuple conventions.
- `urbanoccupants/datamodel.py`: canonical DB table name constants used across scripts.

**Project-specific conventions & patterns**
- Multiprocessing param tuple pattern: many worker functions are written to accept a single tuple parameter (e.g. `markov_chain_for_cluster`, `run_hipf`, `sample_households`). When adding parallel work, follow the same yield-of-tuples + `Pool.imap_unordered(function, generator)` pattern.
- Config processing: use `urbanoccupants.utils.read_simulation_config(path)` to parse YAML and to get typed values (enums, timedeltas, datetimes). Rely on keys like `people-features`, `household-features`, `time-step-size-minutes`.
- Dataframe shapes/indices: many functions expect pandas DataFrames with specific MultiIndex layouts (seed uses index levels like `(household_id, person_id)`, markov timeseries index includes `daytype` and `time_of_day`). Check `hipf.fit_hipf` and `WeekMarkovChain` validation for examples.
- Enums + mapping: `urbanoccupants/tus.py` contains large mapping tables (`LOCATION_MAP`, `ACTIVITY_MAP`, `AGE_MAP`, ...). Follow their style for new mappings (explicit Enum values mapped from external codes).
- Database IO: outputs are SQLite DBs written with `pandas.DataFrame.to_sql` in `scripts/simulationinput.py`. Use the table name constants in `urbanoccupants/datamodel.py`.

**Dependencies & environment notes**
- `setup.py` lists `install_requires=['pytus2000']`; other runtime imports across scripts include `pandas`, `numpy`, `pykov`, `sqlalchemy`, `requests_cache`, `tqdm`, `click`, and `PyYAML`.
- Java simulator: `Makefile` downloads `build/energy-agents.jar`; `scripts/runsim.py` spawns `java -jar`. Tests and reproductions require this jar for end-to-end runs.
- Python compatibility: `setup.py` indicates Python 3 (3.6 historically). Prefer running inside the conda environment provided.

**Testing and quick checks**
- Unit tests live under `urbanoccupants/tests` and `tests/` for scripts. Use `py.test` or `make test`.
- For quick import checks: run `python -c "import urbanoccupants; print('ok')"` inside the repo environment.

**When editing code, common pitfalls to avoid**
- Do not change the multiprocessing param-tuple signatures unless you update all call sites (lots of `imap_unordered` usage).
- Preserve dataframe index conventions: many pieces rely on MultiIndex levels and specific column names.
- When adjusting config keys, update `read_simulation_config` and all `config/*.yaml` copies.

If any part is unclear or you want the instructions expanded with examples (e.g. typical quick-fix PRs, common test failures), tell me which areas to expand.
