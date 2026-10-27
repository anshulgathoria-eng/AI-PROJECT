"""Read UCI minute measurements and aggregate energy without filling across time."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT / "data" / "household_power_consumption.txt"


def load_hourly_data(path=DEFAULT_DATASET, min_coverage=0.9):
    """Return hourly kWh and an audit report.

    Global_active_power is average kW over each minute, so sum(kW)/60 is
    energy in kWh. Incomplete hours are scaled to 60 minutes only when at
    least min_coverage of their measurements are valid. Other hours stay NaN.
    No interpolation/backfill is used; test observations cannot fill training.
    Timestamps are local, timezone-naive as provided by the source.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Place the UCI ZIP in the project folder "
            "and run python scripts/prepare_data.py, or extract "
            "household_power_consumption.txt into data/. See README.md."
        )
    if not 0 < min_coverage <= 1:
        raise ValueError("min_coverage must be in (0, 1].")
    raw = pd.read_csv(path, sep=";", usecols=["Date", "Time", "Global_active_power"],
                      na_values=["?", "", "NA"], dtype="string")
    dates = pd.to_datetime(raw["Date"] + " " + raw["Time"],
                           format="%d/%m/%Y %H:%M:%S", errors="coerce")
    values = pd.to_numeric(raw["Global_active_power"], errors="coerce")
    values = values.where(values.ge(0) & values.lt(float("inf")))
    valid_time = dates.notna()
    minute = pd.Series(values[valid_time].to_numpy(dtype=float, na_value=float("nan")),
                       index=pd.DatetimeIndex(dates[valid_time]), name="power_kw")
    duplicate_count = int(minute.index.duplicated().sum())
    minute = minute.groupby(level=0).mean().sort_index()
    if minute.empty:
        raise ValueError("The dataset has no valid timestamps.")
    # Each row represents one minute; reject off-minute input explicitly.
    if ((minute.index.second != 0) | (minute.index.microsecond != 0)).any():
        raise ValueError("Expected readings on whole-minute timestamps.")
    hourly = pd.DataFrame({"observed_minutes": minute.resample("h").count()})
    hourly["coverage"] = hourly["observed_minutes"] / 60.0
    hourly["energy_kwh"] = minute.resample("h").mean().where(hourly.coverage >= min_coverage)
    hourly.index.name = "timestamp"
    report = {
        "source": str(path.resolve()), "input_rows": len(raw),
        "invalid_timestamps": int((~valid_time).sum()),
        "missing_or_invalid_power": int(values.isna().sum()),
        "duplicate_timestamps": duplicate_count, "total_hours": len(hourly),
        "usable_hours": int(hourly.energy_kwh.notna().sum()),
        "excluded_hours": int(hourly.energy_kwh.isna().sum()),
        "min_coverage": min_coverage,
    }
    return hourly, report
