Place `household_power_consumption.txt` here, or run `python scripts/prepare_data.py`
from the project root with the UCI dataset ZIP present. The loader reads only the
local file. Keep the original ZIP unchanged. See the root README for attribution,
format, missing-data policy, units, and extraction instructions.

Cloud deployments use the committed `household_hourly.csv.gz` and
`household_hourly.json` when the original minute file is absent. This contains
the complete real dataset's hourly aggregates, including missing hours and
coverage counts; it is not synthetic. The JSON records the processing policy,
original data hash, bundle checksum, and data-quality report. Rebuild it with
`python scripts/build_hourly_bundle.py` after extracting the original dataset.

Attribution: Georges Hebrail and Alice Berard (2006), *Individual Household
Electric Power Consumption*, UCI Machine Learning Repository,
https://doi.org/10.24432/C58K54. Source:
https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption.
License: Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/.

Changes: aggregated minute-level Global_active_power to hourly energy estimates
in kWh using the hourly mean of valid kW readings, retaining hours with at least
54 valid minutes. Hours below that threshold remain missing. No interpolation,
timezone conversion, synthetic readings, or target-based feature generation was
applied. See the repository README for the detailed policy and limitations.
