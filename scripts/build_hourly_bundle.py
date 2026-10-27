"""Build a small, reproducible cloud dataset from the original real UCI measurements."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_loader import BUNDLED_DATASET, DEFAULT_DATASET, load_hourly_data


def build_bundle():
    hourly, audit = load_hourly_data(DEFAULT_DATASET)
    audit["source"] = DEFAULT_DATASET.name
    hourly.to_csv(BUNDLED_DATASET, float_format="%.15g",
                  compression={"method": "gzip", "mtime": 0})
    with BUNDLED_DATASET.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    with DEFAULT_DATASET.open("rb") as stream:
        raw_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    metadata = {
        "source_url": "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption",
        "citation": "Hebrail, G. & Berard, A. (2006). Individual Household Electric Power Consumption. UCI Machine Learning Repository.",
        "doi": "https://doi.org/10.24432/C58K54",
        "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "transformation": "Global_active_power converted to hourly kWh via mean kW times one hour, requiring at least 54/60 valid minutes. Other hours remain missing. Source local timestamps retained; no interpolation.",
        "sha256": digest, "raw_sha256": raw_digest, "audit": audit,
    }
    BUNDLED_DATASET.with_suffix("").with_suffix(".json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Built {BUNDLED_DATASET.name}: {BUNDLED_DATASET.stat().st_size:,} bytes; "
          f"{audit['usable_hours']:,} usable hours. SHA256: {digest}")


if __name__ == "__main__":
    build_bundle()
