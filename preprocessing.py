"""Features known at prediction time, and a strict temporal holdout."""
import numpy as np
import pandas as pd


def time_features(index):
    index = pd.DatetimeIndex(index)
    return pd.DataFrame({
        "hour": index.hour, "day_of_week": index.day_of_week,
        "month": index.month, "day_of_year": index.day_of_year,
        "weekend": (index.day_of_week >= 5).astype(int),
        "hour_sin": np.sin(2 * np.pi * index.hour / 24),
        "hour_cos": np.cos(2 * np.pi * index.hour / 24),
    }, index=index)


def chronological_split(hourly, test_fraction=0.2):
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be in (0, 1).")
    if not isinstance(hourly.index, pd.DatetimeIndex) or not hourly.index.is_unique:
        raise ValueError("Expected a unique DatetimeIndex.")
    target = hourly.energy_kwh.sort_index().replace([np.inf, -np.inf], np.nan).dropna()
    if len(target) < 48:
        raise ValueError("At least 48 valid hourly observations are needed.")
    cutoff = int(len(target) * (1 - test_fraction))
    if cutoff < 2 or len(target) - cutoff < 2:
        raise ValueError("Both training and test sets need at least two hours.")
    features = time_features(target.index)
    return features.iloc[:cutoff], features.iloc[cutoff:], target.iloc[:cutoff], target.iloc[cutoff:]
