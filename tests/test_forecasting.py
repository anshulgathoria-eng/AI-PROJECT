import numpy as np
import pandas as pd
import pytest
from preprocessing import chronological_split, time_features
from forecasting import train_and_evaluate, forecast_future


@pytest.fixture
def synthetic_hourly():
    """Synthetic observations for deterministic tests only; not experimental results."""
    index = pd.date_range("2020-01-01", periods=24 * 40, freq="h")
    target = 1.5 + np.sin(2 * np.pi * index.hour.to_numpy() / 24)
    frame = pd.DataFrame({"energy_kwh": target}, index=index)
    frame.iloc[12, 0] = np.nan
    return frame


def test_split_has_no_future_leakage(synthetic_hourly):
    x_train, x_test, y_train, y_test = chronological_split(synthetic_hourly)
    assert x_train.index.max() < x_test.index.min()
    assert not y_train.isna().any() and not y_test.isna().any()
    pd.testing.assert_frame_equal(x_test, time_features(y_test.index))
    assert "energy_kwh" not in x_train


def test_training_predictions_and_future(synthetic_hourly):
    result = train_and_evaluate(synthetic_hourly, n_estimators=12)
    assert np.isfinite(result["comparison"].to_numpy()).all()
    assert all(np.isfinite(list(result["metrics"].values())))
    assert result["metrics"]["MAE"] < result["metrics"]["Baseline MAE"]
    future = forecast_future(synthetic_hourly, 48, n_estimators=12)
    assert len(future) == 48 and np.isfinite(future).all()
    assert future.index.min() > synthetic_hourly.index.max()


def test_invalid_inputs(synthetic_hourly):
    with pytest.raises(ValueError):
        forecast_future(synthetic_hourly, 0)
    with pytest.raises(ValueError):
        chronological_split(synthetic_hourly.head(20))
    with pytest.raises(ValueError):
        chronological_split(synthetic_hourly, test_fraction=1)
