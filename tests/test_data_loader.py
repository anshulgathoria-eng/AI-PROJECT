import pandas as pd
import pytest
from data_loader import load_hourly_data, DEFAULT_DATASET


def test_missing_values_and_hourly_units(tmp_path):
    path = tmp_path / "measurements.txt"
    times = pd.date_range("2007-02-01", periods=180, freq="min")
    frame = pd.DataFrame({"Date": times.strftime("%d/%m/%Y"), "Time": times.strftime("%H:%M:%S"),
                          "Global_active_power": ["2.0"] * 180})
    frame.loc[:5, "Global_active_power"] = "?"  # 54/60 accepted
    frame.loc[60:66, "Global_active_power"] = "?"  # 53/60 excluded
    frame.to_csv(path, sep=";", index=False)
    hourly, report = load_hourly_data(path)
    assert hourly.index[0] == pd.Timestamp("2007-02-01")  # day-first, not Jan 2
    assert hourly.iloc[0].energy_kwh == pytest.approx(2.0)  # not 120 kWh
    assert pd.isna(hourly.iloc[1].energy_kwh)
    assert hourly.iloc[2].energy_kwh == pytest.approx(2.0)
    assert report["missing_or_invalid_power"] == 13
    assert report["excluded_hours"] == 1


def test_invalid_duplicate_and_absent_hours(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("Date;Time;Global_active_power\n01/02/2007;00:00:00;2\n"
                    "01/02/2007;00:00:00;4\n01/02/2007;02:00:00;-1\n"
                    "bad;bad;5\n", encoding="utf-8")
    hourly, report = load_hourly_data(path, min_coverage=1/60)
    assert hourly.iloc[0].energy_kwh == 3
    assert pd.isna(hourly.iloc[1].energy_kwh)
    assert pd.isna(hourly.iloc[2].energy_kwh)
    assert report["invalid_timestamps"] == 1
    assert report["duplicate_timestamps"] == 1


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="prepare_data"):
        load_hourly_data(tmp_path / "missing.txt")


@pytest.mark.integration
def test_real_dataset_loads():
    if not DEFAULT_DATASET.exists():
        pytest.skip("Real UCI dataset is not installed")
    hourly, report = load_hourly_data()
    assert report["input_rows"] == 2075259
    assert hourly.index.min() == pd.Timestamp("2006-12-16 17:00")
    assert hourly.index.max() == pd.Timestamp("2010-11-26 21:00")
    assert report["usable_hours"] > 33000
    assert hourly.energy_kwh.dropna().ge(0).all()
