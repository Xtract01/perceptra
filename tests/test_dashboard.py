"""Run AppTest in fresh .venv subprocesses to preserve the headless service tests.

Day 1 explicitly checks that importing/running the service does not import
Streamlit. Isolating the UI also prevents shared Streamlit runtime/session state.
"""

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = '''
import socket
from unittest.mock import patch
def no_network(*args, **kwargs):
    raise AssertionError("AppTest must run offline")
# Windows asyncio implements socketpair with a loopback connection. Permit that
# internal coordination, while still rejecting every external network address.
original_connect = socket.socket.connect
def loopback_only(sock, address):
    if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
        return original_connect(sock, address)
    return no_network()
socket.socket.connect = loopback_only
socket.create_connection = no_network
import nltk
nltk.download = no_network
from streamlit.testing.v1 import AppTest
from perceptra.analysis import analyze_product
from perceptra.schemas import DatasetError
APP = "app/streamlit_app.py"
def start():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception, [str(x.value) for x in app.exception]
    return app
def run_analysis(app):
    app.button(key="analyze").click().run()
    assert not app.exception, [str(x.value) for x in app.exception]
    return app
'''

CASES = {
    "invalid_data_configuration": '''
        import os
        with patch.dict(os.environ, {"PERCEPTRA_DATA_DIR": "__missing_day3_dataset__"}):
            app = start()
        assert len(app.error) == 1
        assert "missing or invalid" in app.error[0].value
        assert any("PERCEPTRA_DATA_DIR" in item.value for item in app.info)
        assert not app.metric
        assert not app.button
    ''',
    "startup": '''
        with patch("perceptra.analysis.analyze_product") as service:
            app = start()
            assert app.selectbox(key="selected_product").value == "clothing:1078"
            assert not app.metric
            assert app.info
            service.assert_not_called()
    ''',
    "metrics_and_aspect_table": '''
        expected = analyze_product("clothing:1078")
        app = run_analysis(start())
        metrics = {item.label: item.value for item in app.metric}
        assert metrics == {"Reviews analyzed": "200", "Perception rating": f"{expected['perception_rating']:.2f}/10",
                           **{label.title(): f"{expected['sentiment_percentages'][label]:.1f}%" for label in ("positive", "negative", "neutral")}}
        tables = [table.value for table in app.dataframe]
        counts = next(table for table in tables if "Reviews" in table.columns)
        assert list(counts["Reviews"]) == [expected["sentiment_counts"][label] for label in ("positive", "negative", "neutral")]
        aspects = next(table for table in tables if "Aspect" in table.columns)
        assert len(aspects) == len(expected["aspect_analysis"]["aspects"])
        assert list(aspects["Supporting reviews"]) == [item["supporting_review_count"] for item in expected["aspect_analysis"]["aspects"]]
        assert list(aspects["Estimated rating /10"]) == [round(item["rating"], 2) for item in expected["aspect_analysis"]["aspects"]]
        assert any("whole-review" in item.value for item in app.info)
    ''',
    "switch_products": '''
        app = run_analysis(start())
        app.selectbox(key="selected_product").select("clothing:862").run()
        assert not app.exception
        assert not app.metric
        assert "analysis_result" not in app.session_state
        run_analysis(app)
        assert app.session_state["analysis_result"]["product"]["product_id"] == "clothing:862"
        assert next(item.value for item in app.metric if item.label == "Reviews analyzed") == "198"
        for table in app.dataframe:
            if "Product ID" in table.value.columns:
                assert set(table.value["Product ID"]) == {"clothing:862"}
    ''',
    "review_filter_and_pagination": '''
        app = run_analysis(start())
        expected = app.session_state["analysis_result"]["scored_reviews"]
        app.selectbox(key="review_page").select(2).run()
        tables = [table.value for table in app.dataframe if "Original review" in table.value.columns]
        assert list(tables[-1]["Review ID"]) == [row["review_id"] for row in expected[25:50]]
        app.selectbox(key="review_filter").select("Negative").run()
        assert app.selectbox(key="review_page").value == 1
        table = [table.value for table in app.dataframe if "Original review" in table.value.columns][-1]
        assert set(table["Sentiment"]) == {"Negative"}
        assert len(table) == 9
        app.text_input(key="review_search").set_value("__no_review_can_match_this__").run()
        assert not app.exception
        assert any("No reviews match" in item.value for item in app.info)
    ''',
    "matching_search_and_product_filter_reset": '''
        app = run_analysis(start())
        app.selectbox(key="review_page").select(2).run()
        app.text_input(key="review_search").set_value("MATERIAL").run()
        assert not app.exception
        assert app.selectbox(key="review_page").value == 1
        tables = [table.value for table in app.dataframe if "Original review" in table.value.columns]
        assert len(tables[-1]) > 0
        assert all("material" in text.casefold() for text in tables[-1]["Original review"])
        app.selectbox(key="selected_product").select("clothing:862").run()
        assert not app.metric
        run_analysis(app)
        assert app.text_input(key="review_search").value == ""
        assert app.selectbox(key="review_filter").value == "All sentiments"
        assert app.selectbox(key="review_page").value == 1
    ''',
    "missing_resources": '''
        with patch("perceptra.nlp.aspects.check_nltk_resources", side_effect=LookupError("Run prepare_demo_data.py --prepare-nltk")):
            app = run_analysis(start())
        assert app.metric
        assert app.warning
        assert app.session_state["analysis_result"]["aspect_analysis"]["status"] == "missing_resources"
    ''',
    "empty_reviews": '''
        with patch("perceptra.nlp.cleaner.is_english", return_value=False):
            app = run_analysis(start())
        assert not app.metric
        assert any("No usable reviews" in item.value for item in app.info)
        assert app.session_state["analysis_result"]["perception_rating"] is None
    ''',
    "missing_dataset": '''
        with patch("perceptra.ingestion.dataset_loader.load_manifest", side_effect=DatasetError("Internal checksum details")):
            app = start()
        assert len(app.error) == 1
        assert "missing or invalid" in app.error[0].value
        assert "Internal checksum" not in app.error[0].value
        assert not app.button
    ''',
    "empty_catalog": '''
        with patch("perceptra.ingestion.dataset_loader.load_manifest", return_value={"products": []}):
            app = start()
        assert any("No products" in item.value for item in app.info)
        assert not app.selectbox
    ''',
    "invalid_selection": '''
        app = AppTest.from_file(APP, default_timeout=30)
        app.session_state["selected_product"] = "invalid"
        app.run()
        assert not app.exception
        assert app.selectbox(key="selected_product").value == "clothing:1078"
        assert any("unavailable" in item.value for item in app.warning)
    ''',
    "processing_failure_clears_results": '''
        app = run_analysis(start())
        with patch("perceptra.analysis.analyze_product", side_effect=RuntimeError("PRIVATE INTERNAL FAILURE")):
            app.button(key="analyze").click().run()
        assert not app.exception
        assert not app.metric
        assert "analysis_result" not in app.session_state
        assert len(app.error) == 1
        assert "PRIVATE INTERNAL" not in app.error[0].value
    ''',
    "wrong_product_result_is_rejected": '''
        wrong = analyze_product("clothing:862")
        with patch("perceptra.analysis.analyze_product", return_value=wrong):
            app = run_analysis(start())
        assert app.error
        assert not app.metric
        assert "analysis_result" not in app.session_state
    ''',
}


@pytest.mark.parametrize("case", CASES)
def test_dashboard(case, tmp_path):
    environment = os.environ.copy()
    temp = tmp_path / "streamlit-temp"
    temp.mkdir()
    environment.update({"TEMP": str(temp), "TMP": str(temp), "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"})
    result = subprocess.run([sys.executable, "-c", BOOTSTRAP + textwrap.dedent(CASES[case])],
                            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, f"{case}\n{result.stdout}\n{result.stderr}"
