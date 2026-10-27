"""Random Forest evaluation and future predictions."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from preprocessing import chronological_split, time_features


def new_model(n_estimators=100):
    return RandomForestRegressor(n_estimators=n_estimators, max_depth=18,
                                  min_samples_leaf=4, n_jobs=-1, random_state=42)


def train_and_evaluate(hourly, test_fraction=0.2, n_estimators=100):
    x_train, x_test, y_train, y_test = chronological_split(hourly, test_fraction)
    model = new_model(n_estimators)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    baseline = np.full(len(y_test), y_train.mean())
    return {
        "evaluation_model": model,
        "comparison": pd.DataFrame({"Actual": y_test, "Predicted": predictions,
                                     "Training mean baseline": baseline}, index=y_test.index),
        "metrics": {"MAE": float(mean_absolute_error(y_test, predictions)),
                    "RMSE": float(np.sqrt(mean_squared_error(y_test, predictions))),
                    "R²": float(r2_score(y_test, predictions)),
                    "Baseline MAE": float(mean_absolute_error(y_test, baseline))},
        "train_hours": len(y_train), "test_hours": len(y_test),
        "train_end": y_train.index[-1], "test_start": y_test.index[0],
    }


def forecast_future(hourly, horizon=24, n_estimators=100):
    if not isinstance(horizon, int) or not 1 <= horizon <= 168:
        raise ValueError("Forecast horizon must be an integer from 1 to 168 hours.")
    target = hourly.energy_kwh.replace([np.inf, -np.inf], np.nan).dropna().sort_index()
    if len(target) < 48:
        raise ValueError("At least 48 valid hourly observations are needed.")
    model = new_model(n_estimators)
    model.fit(time_features(target.index), target)
    # Start beyond the dataset's final hour, even if it had insufficient coverage.
    future_index = pd.date_range(hourly.index.max() + pd.Timedelta(hours=1), periods=horizon, freq="h")
    return pd.Series(model.predict(time_features(future_index)), index=future_index, name="Forecast kWh")
