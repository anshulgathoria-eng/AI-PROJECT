"""Launch with: python -m streamlit run app.py"""
import matplotlib.pyplot as plt
import streamlit as st
from data_loader import DEFAULT_DATASET, load_hourly_data
from forecasting import train_and_evaluate, forecast_future
from graph_algorithms import bfs_nearest_source
from grid_simulation import NODES, ROUTING, analyze_failure
from visualization import network_figure, forecast_figure, evaluation_figure

st.set_page_config(page_title="GridSense", page_icon="⚡", layout="wide")
st.title("⚡ GridSense")
st.caption("Household energy forecasting · simulated grid connectivity")


@st.cache_data(show_spinner="Loading UCI minute observations…")
def cached_data(path, modified):
    return load_hourly_data(path)


@st.cache_data(show_spinner="Training and evaluating the Random Forest…")
def cached_evaluation(hourly):
    result = train_and_evaluate(hourly)
    # No executable model files are read or saved.
    result.pop("evaluation_model")
    return result


@st.cache_data(show_spinner="Fitting historical data and forecasting…")
def cached_future(hourly, horizon):
    return forecast_future(hourly, horizon)


def show_plot(fig):
    st.pyplot(fig)
    plt.close(fig)


page = st.sidebar.radio("Explore", ["Overview", "Energy Forecasting", "Smart Grid Simulation",
                                    "BFS Optimization", "DFS Fault Analysis", "About"])
hourly, report = None, None
try:
    hourly, report = cached_data(str(DEFAULT_DATASET), DEFAULT_DATASET.stat().st_mtime_ns)
except FileNotFoundError:
    st.warning("UCI dataset missing. Place the ZIP in this project folder and run "
               "`python scripts/prepare_data.py`, then refresh. You can still explore the grid simulations.")
except (ValueError, OSError) as exc:
    st.error(f"Could not load dataset: {exc}")

if page == "Overview":
    st.header("Forecast demand. Explore grid connections.")
    st.write("GridSense learns hourly household energy patterns with a Random Forest. "
             "A separate simulated network demonstrates BFS source routing and DFS fault connectivity.")
    if hourly is not None:
        a, b, c = st.columns(3)
        a.metric("Usable hourly observations", f"{report['usable_hours']:,}")
        b.metric("Mean energy per usable hour", f"{hourly.energy_kwh.mean():.3f} kWh")
        c.metric("Hours excluded for low coverage", f"{report['excluded_hours']:,}")
        st.success(f"Real UCI dataset loaded: {report['input_rows']:,} minute rows.")
        st.write(f"Dataset period: {hourly.index.min()} to {hourly.index.max()} (source local time).")
        st.line_chart(hourly[["energy_kwh"]].tail(24 * 14), y_label="kWh per hour")
        with st.expander("Data quality and aggregation policy"):
            st.json(report)
            st.write("? and invalid power values become missing. Duplicate timestamps are averaged. "
                     "Hours with fewer than 54 valid minutes are excluded. For accepted hours, "
                     "mean kW × one hour estimates kWh, scaling minor gaps to a full hour. "
                     "Missing hours remain gaps; there is no interpolation across the train/test boundary.")
    st.info("This is one household's historical data. The grid and all resource availability are simulated.")

elif page == "Energy Forecasting":
    st.header("Energy Forecasting")
    if hourly is not None:
        horizon = st.slider("Forecast horizon (hours after dataset end)", 1, 168, 24)
        try:
            result = cached_evaluation(hourly)
            future = cached_future(hourly, horizon)
            columns = st.columns(4)
            for column, (name, value) in zip(columns, result["metrics"].items()):
                column.metric(name + (" (kWh)" if name != "R²" else ""), f"{value:.3f}")
            st.caption(f"Chronological 80/20 split: {result['train_hours']:,} training hours through "
                       f"{result['train_end']}; {result['test_hours']:,} test hours starting {result['test_start']}.")
            show_plot(evaluation_figure(result["comparison"]))
            st.subheader("Future forecast from the end of the historical dataset")
            show_plot(forecast_figure(hourly, future))
            st.dataframe(future.to_frame(), width="stretch")
            st.download_button("Download forecast CSV", future.to_csv(), "gridsense_forecast.csv", "text/csv")
            st.caption("Holdout predictions use a model fitted only to training hours. Future forecasts "
                       "use a separate model refitted on all usable historical hours. Calendar-only "
                       "features cannot anticipate weather, appliance changes, or unusual events. "
                       "No confidence intervals are estimated. R² can be negative.")
        except ValueError as exc:
            st.error(str(exc))

elif page == "Smart Grid Simulation":
    st.header("Simulated electrical network")
    show_plot(network_figure())
    st.write("Lines represent simulated connections. The grid supplies two transformers, each with "
             "two houses and alternative resources. BFS treats these lines as undirected routes; "
             "fault analysis follows directed supply connections from a transformer to its children.")

elif page == "BFS Optimization":
    st.header("BFS: nearest available alternative source")
    consumer = st.selectbox("Consumer", [n for n in NODES if NODES[n] == "house"])
    available = st.multiselect("Available simulated sources", ["Battery A", "Battery B", "Solar"],
                               default=["Battery A", "Battery B", "Solar"])
    failed = st.multiselect("Unavailable transformers (BFS cannot pass through them)", ["T1", "T2"])
    demand_mode = st.radio("Demand input", ["Manual scenario", "Peak model forecast"], horizontal=True)
    demand = None
    if demand_mode == "Manual scenario":
        demand = st.number_input("Simulated hourly demand (kWh)", min_value=0.0, value=3.0, step=0.1)
    elif hourly is not None:
        demand = float(cached_future(hourly, 24).max())
        st.metric("Peak next-24-hour household forecast", f"{demand:.3f} kWh")
        st.caption("The household forecast is assigned to the selected simulated consumer for demonstration.")
    else:
        st.warning("Load the UCI dataset to use forecast demand.")
    threshold = st.number_input("High-demand threshold (kWh in one hour)", min_value=0.0, value=2.0, step=0.1)
    route = []
    if demand is not None and demand > threshold:
        result = bfs_nearest_source(ROUTING, consumer, set(available), failed)
        st.write("Traversal: " + " → ".join(result["traversal"]))
        route = result["path"]
        if route:
            st.success(f"Source: {result['source']} · {result['connections']} connections · " + " → ".join(route))
        else:
            st.warning("No available source is reachable through the functioning network.")
    elif demand is not None:
        st.info("Demand does not exceed the threshold; no alternative-source search is triggered.")
    show_plot(network_figure(route=route, highlight=failed))
    st.caption("BFS minimizes the number of connections. Source capacity, losses, voltage, "
               "switching constraints, and physical power flow are outside this simulation.")

elif page == "DFS Fault Analysis":
    st.header("DFS: transformer failure connectivity")
    transformer = st.selectbox("Failed transformer", ["T1", "T2"])
    result = analyze_failure(transformer)
    st.write("DFS traversal: " + " → ".join(result["traversal"]))
    st.warning("Potentially affected consumers: " + ", ".join(result["consumers"]))
    show_plot(network_figure(highlight=result["traversal"], failed=transformer))
    st.write("Failure disconnects the transformer's upstream and outgoing supply links (red dashed lines). "
             "DFS follows the pre-failure directed downstream topology to identify its dependent consumers. "
             "Local batteries and solar do not automatically restore supply in this fault scenario.")
    st.caption("This is connectivity analysis of a simulated outage, not electrical fault prediction.")

else:
    st.header("About GridSense")
    st.write("A college demonstration combining Pandas/NumPy preprocessing, scikit-learn Random Forest "
             "regression, manual BFS/DFS algorithms, Matplotlib charts, and Streamlit.")
    st.markdown("Dataset: [UCI Individual Household Electric Power Consumption]"
                "(https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption).")
    st.write("Forecasts describe historical household patterns. They are not current grid measurements "
             "or dispatch advice. Calendar seasonality may generalize poorly when household behavior changes. "
             "The source timestamps have no timezone offset; no daylight-saving corrections are inferred.")
