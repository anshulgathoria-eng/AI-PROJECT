# Executed validation

Validated in this workspace using Python 3.12.4 and the installed versions in
`requirements-lock.txt`. The dataset was the supplied UCI ZIP, not synthetic data.

## Archive and data

`python scripts/prepare_data.py` inspected and extracted the sole dataset member:
`household_power_consumption.txt`, 132,960,755 bytes. The ZIP SHA-256 was identical
before extraction, after extraction, and at the final check:

```text
9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff
```

Real loader results:

| Check | Result |
|---|---:|
| Input minute rows | 2,075,259 |
| Invalid timestamps | 0 |
| Duplicate timestamps | 0 |
| Missing/invalid power readings | 25,979 |
| Hourly bins | 34,589 |
| Usable hours at ≥90% coverage | 34,143 |
| Excluded hours | 446 |

The hourly range is 2006-12-16 17:00 through 2010-11-26 21:00, source local time.
Both boundary hours have incomplete coverage and are excluded from modeling.

## Real-data model evaluation

Executed:

```powershell
.\.venv312\Scripts\python.exe scripts/verify_pipeline.py
```

The script completed successfully, verified finite holdout and future predictions,
and generated `artifacts/verification.json` and `artifacts/forecast.csv`.

| Metric | Measured value |
|---|---:|
| MAE | 0.455601 kWh |
| RMSE | 0.641164 kWh |
| R² | 0.257143 |
| Training-mean baseline MAE | 0.635019 kWh |

Training: 27,314 usable hours, ending 2010-02-05 03:00.
Holdout: 6,829 usable hours, starting 2010-02-05 04:00.
The separate all-history refit produced 24 finite hourly forecasts starting
2010-11-26 22:00. These metrics describe one historical holdout and do not
establish present-day forecasting accuracy or grid-level performance.

## Tests and application startup

Executed the final suite:

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
```

Result: **14 passed, 1 warning in 32.99 seconds**, with no skips.
The warning is a Pandas deprecation inside Streamlit's built-in chart code.
Earlier test runs encountered a temporary-directory sandbox restriction and
incorrect relative paths in the dashboard tests; the final run used approved
local execution and corrected absolute application paths.

Tests exercised real UCI loading, synthetic test-fixture predictions, temporal
isolation, missing values and unit conversion, invalid/duplicate timestamps,
safe archive extraction, BFS shortest paths and unreachable resources, DFS cycles
and downstream transformer dependencies, all six dashboard pages, horizon changes,
forecast demand input, no available sources, and missing-dataset fallback.

The following server command started successfully:

```powershell
.\.venv312\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --browser.gatherUsageStats false
```

`http://127.0.0.1:8501/_stcore/health` returned HTTP 200 with body `ok`.
The application was opened in the Codex browser panel. Page execution and widget
interactions were verified with Streamlit AppTest; no manual browser visual review
is claimed.
