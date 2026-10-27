import json
import numpy as np
import pandas as pd
import pytest
import data_loader
from data_loader import BUNDLED_DATASET, DEFAULT_DATASET, load_app_data, load_hourly_data
from forecasting import train_and_evaluate, forecast_future


def test_bundle_loads_and_forecasts_without_raw_data(monkeypatch, tmp_path):
    monkeypatch.setattr(data_loader, "DEFAULT_DATASET", tmp_path / "absent.txt")
    assert data_loader.resolve_dataset() == BUNDLED_DATASET
    hourly, report = load_app_data(data_loader.resolve_dataset())
    assert report["usable_hours"] == 34143
    assert report["excluded_hours"] == 446
    assert "Bundled" in report["representation"]
    assert hourly.energy_kwh.isna().sum() == 446
    result = train_and_evaluate(hourly, n_estimators=8)
    future = forecast_future(hourly, 24, n_estimators=8)
    assert np.isfinite(result["comparison"].to_numpy()).all()
    assert np.isfinite(future).all()


@pytest.mark.integration
def test_bundle_matches_original_hourly_pipeline():
    if not DEFAULT_DATASET.exists():
        pytest.skip("Original local UCI dataset is absent")
    original, audit = load_hourly_data()
    bundled, report = load_app_data(BUNDLED_DATASET)
    pd.testing.assert_frame_equal(original, bundled, check_freq=False, rtol=1e-12, atol=1e-12)
    for key in ["input_rows", "usable_hours", "excluded_hours", "missing_or_invalid_power"]:
        assert audit[key] == report[key]


def test_corrupted_bundle_is_rejected(tmp_path):
    path = tmp_path / BUNDLED_DATASET.name
    path.write_bytes(b"corrupted")
    metadata_path = BUNDLED_DATASET.with_suffix("").with_suffix(".json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    path.with_suffix("").with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        load_app_data(path)
