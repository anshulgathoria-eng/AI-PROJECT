"""Execute actual Streamlit page scripts and widgets without requiring a browser."""
import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from data_loader import DEFAULT_DATASET
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_missing_dataset_keeps_simulation_available(monkeypatch, tmp_path):
    monkeypatch.setattr("data_loader.DEFAULT_DATASET", tmp_path / "missing.txt")
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert any("dataset missing" in w.value for w in app.warning)
    app.sidebar.radio[0].set_value("DFS Fault Analysis").run()
    assert not app.exception
    assert any("H1, H2" in w.value for w in app.warning)


@pytest.mark.integration
def test_dashboard_pages_and_interactions():
    if not DEFAULT_DATASET.exists():
        pytest.skip("Real UCI dataset is not installed")
    app = AppTest.from_file(APP, default_timeout=120).run()
    assert not app.exception
    assert app.success
    for page in ["Energy Forecasting", "Smart Grid Simulation", "BFS Optimization", "DFS Fault Analysis", "About"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        if page == "Energy Forecasting":
            assert len(app.metric) == 4
            app.slider[0].set_value(48).run()
            assert not app.exception
        elif page == "BFS Optimization":
            assert app.success
            app.multiselect[0].set_value([]).run()
            assert not app.exception
            assert any("No available source" in w.value for w in app.warning)
            app.radio[0].set_value("Peak model forecast").run()
            assert not app.exception
        elif page == "DFS Fault Analysis":
            app.selectbox[0].set_value("T2").run()
            assert not app.exception
            assert "H3, H4" in app.warning[0].value
