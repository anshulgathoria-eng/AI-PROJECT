"""Run real-data loading, chronological evaluation and future forecasting."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from data_loader import load_hourly_data
from forecasting import train_and_evaluate, forecast_future


if __name__ == "__main__":
    hourly, audit = load_hourly_data()
    result = train_and_evaluate(hourly)
    future = forecast_future(hourly, 24)
    assert np.isfinite(future.to_numpy()).all()
    assert np.isfinite(result["comparison"].to_numpy()).all()
    output = {"dataset_audit": audit, "metrics": result["metrics"],
              "train_hours": result["train_hours"], "test_hours": result["test_hours"],
              "train_end": str(result["train_end"]), "test_start": str(result["test_start"]),
              "forecast_start": str(future.index[0]), "forecast_hours": len(future)}
    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    (destination / "verification.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    future.to_csv(destination / "forecast.csv")
    print(json.dumps(output, indent=2))
