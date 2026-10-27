# GridSense

GridSense is a working college project that forecasts hourly household electricity
consumption with a Random Forest and demonstrates smart-grid connectivity using
manually implemented BFS and DFS. The Streamlit dashboard provides dataset status,
model evaluation, historical and future forecasts, source routing, and transformer
failure analysis. The network is simulated; the household dataset is real UCI data.

## Run on Windows

Python 3.11 or newer is required. Python 3.12 was used for verification in this
workspace. A local environment is already installed at `.venv312`:

```powershell
.\.venv312\Scripts\python.exe -m streamlit run app.py
```

Open the localhost URL printed by Streamlit (normally http://localhost:8501).
The first forecasting visit trains the models; subsequent visits reuse cached
results. Stop the server with Ctrl+C. The dashboard runs locally without an API key.

For a new checkout, install dependencies:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
python scripts/prepare_data.py
.\.venv312\Scripts\python.exe -m streamlit run app.py
```

If the machine's policy disables pip downloads, enable package-index access using
its approved configuration. This workspace's sandbox required an approved network
install. `requirements-lock.txt` records the versions actually used; for the same
environment install that file instead of `requirements.txt`.

## Dataset

Source: [UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption).
The measurements describe a single household, not every house in the simulated grid.
Retain the source attribution and consult UCI's dataset page for citation and terms
when redistributing the data.

The supplied ZIP is already extracted to `data/household_power_consumption.txt`.
The original ZIP is unchanged. To reproduce extraction, place exactly one dataset
ZIP at the project root and run:

```powershell
.\.venv312\Scripts\python.exe scripts/prepare_data.py
# Or specify an archive explicitly:
.\.venv312\Scripts\python.exe scripts/prepare_data.py "C:\path\to\dataset.zip"
```

The extractor inspects the archive for the expected filename, copies it to a fixed
safe destination, verifies existing data rather than overwriting differing files,
and checks the original archive's SHA-256 before and after extraction. Neither the
archive nor extracted minute dataset is included in Git. The compact
`data/household_hourly.csv.gz` and its JSON metadata **are included** so Streamlit
Community Cloud can run forecasting without the original 133 MB file or an
external download. The app prefers the original minute file locally and falls
back to these real UCI hourly aggregates when that file is absent. Coverage,
missing hours, and the original audit counts are preserved, and the bundle is
checksum-verified on loading. It is not synthetic data.

To rebuild the committed cloud data after extracting the original ZIP:

```powershell
.\.venv312\Scripts\python.exe scripts/build_hourly_bundle.py
```

Dataset attribution: Georges Hebrail and Alice Berard (2006), *Individual Household
Electric Power Consumption*, UCI Machine Learning Repository,
[DOI: 10.24432/C58K54](https://doi.org/10.24432/C58K54), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The bundled data is an
hourly aggregation using the documented 90% coverage policy. See `data/README.md`
and `data/household_hourly.json` for the transformation and provenance.

For Streamlit Community Cloud, select repository `anshulgathoria-eng/AI-PROJECT`,
branch `master`, entrypoint `app.py`, and Python 3.12. No secrets or data upload
are needed. If both the original and bundled data are absent, the dashboard
provides instructions while graph simulations remain usable.

## Architecture and files

```text
UCI ZIP -> scripts/prepare_data.py -> data/household_power_consumption.txt
    -> data_loader.py -> hourly energy + data-quality report
    -> preprocessing.py -> calendar features + chronological 80/20 split
    -> forecasting.py -> holdout metrics + separately refitted future forecast
    -> app.py / visualization.py -> Streamlit dashboard and Matplotlib charts

grid_simulation.py -> routing / downstream graph views
    -> graph_algorithms.py -> BFS routes / DFS affected consumers
    -> app.py / visualization.py -> interactive simulation
```

Additional files: `requirements.txt`, `requirements-lock.txt`, `pytest.ini`,
`tests/test_data_loader.py`, `tests/test_forecasting.py`,
`tests/test_graph_algorithms.py`, `tests/test_app.py`, `tests/test_extraction.py`,
`scripts/verify_pipeline.py`, `.gitignore`, `data/.gitkeep`, and `data/README.md`.

## Preprocessing and forecasting

- Read semicolon-separated columns and convert `?`, blank, malformed, negative,
  or infinite power values to missing observations.
- Parse Date and Time explicitly as `%d/%m/%Y %H:%M:%S`, discard invalid
  timestamps, average duplicates, and sort chronologically. Timestamps retain the
  source's local clock and have no inferred timezone or daylight-saving adjustment.
- `Global_active_power` represents kW for each minute. A complete hour's kWh is
  `sum(minute kW) / 60`. For hours with at least 54 valid minute readings (90%
  coverage), mean kW times one hour estimates full-hour kWh. This scales minor
  gaps; it does not treat missing readings as zero. Less complete hours remain NaN
  and are excluded from modeling. The loader preserves gaps and reports coverage.
- Features are hour, day of week, month, day of year, weekend, and cyclic hour
  encodings. These are known for future timestamps. No contemporaneous meter
  reading or future target is used as an input, and no backward fill or
  interpolation can cross the holdout boundary.
- Evaluate on the final 20% of usable hours, after training on the first 80%.
  Display MAE and RMSE in kWh, R², and a training-mean baseline MAE. A separate
  model refitted on all usable history predicts 1–168 hours after the dataset end.
  These are historical-period future timestamps, not a forecast from today's date.
- The actual-versus-predicted chart shows the last 14 holdout days; the other
  chart shows the last seven historical days and the future horizon. Metrics
  cover the entire holdout. Forecast CSV download is available.

The model uses 100 trees, fixed random seed 42, maximum depth 18, and at least
four samples per leaf. Change these in `forecasting.py` and restart Streamlit to
retrain. Models are trained in memory; no pickle files are loaded.

## BFS and DFS

BFS uses a queue, parent links, and a visited map. When manually entered demand
or peak next-24-hour forecast exceeds the selected threshold, it finds the nearest
available battery or solar node in the undirected routing graph. It reports the
traversal, shortest path, and edge count. Unavailable sources are not candidates;
failed transformers block traversal. Ties follow adjacency-list order.

DFS uses an explicit stack and visited set. A failed transformer disconnects its
upstream and outgoing supply links. DFS traverses the pre-failure **directed
downstream dependency graph**, starting at the transformer, to list the consumers
that depend on it. This avoids incorrectly classifying houses on the other
transformer as downstream dependents. Red nodes show the affected branch and red
dashed edges show the disconnected links. Resources do not automatically restore
service in this scenario.

## Verification

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
.\.venv312\Scripts\python.exe scripts/verify_pipeline.py
```

Tests cover shortest BFS paths, cycles, disconnected nodes, unavailable resources,
blocked transformers, DFS downstream isolation, missing/invalid/duplicate input,
day-first parsing, coverage and kWh units, temporal splitting, finite model
predictions, and dashboard pages. Synthetic observations exist only as explicitly
labeled test fixtures. The real-data integration test skips only if the local
dataset is missing. The verification script trains on the real dataset and saves
actual metrics to `artifacts/verification.json` and forecasts to
`artifacts/forecast.csv`. These generated outputs are ignored by Git.

See `VALIDATION.md` for the executed checks and measured results in this workspace.

## Limitations

This is a demonstration, not a grid control system. The Random Forest learns
calendar patterns and cannot anticipate weather, appliance changes, future
occupancy, or long-term shifts. It cannot extrapolate new consumption levels well.
Missingness may bias results, and minor missing readings are approximated using
the observed hourly mean. A chronological holdout is not rolling-origin validation;
no uncertainty intervals or parameter tuning are provided. Future performance may
be worse than the historical holdout. BFS minimizes connection count only, with
no capacity, voltage, loss, or load-flow model. DFS analyzes simulated connectivity;
it does not predict real faults. Source availability is set manually, and forecast
assignment to individual simulated consumers is illustrative.
