import os
from pathlib import Path
import subprocess
import sys

from perceptra.config import NLTK_DATA_DIR, PROJECT_ROOT, VENV_DIR, check_nltk_resources, configure_nltk


def test_all_imports_are_side_effect_free():
    code = r'''
import importlib, os, pathlib, socket, sys
sys.dont_write_bytecode = True
import nltk
def forbidden(*args, **kwargs):
    raise AssertionError("Import attempted network/download/collection")
nltk.download = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
def guard(event, args):
    if event == 'open':
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError(f"Import attempted a file write: {path}")
    if event in {'socket.connect', 'socket.bind', 'subprocess.Popen', 'os.mkdir', 'os.remove', 'os.rename'}:
        raise AssertionError(f"Import attempted a side effect: {event}")
sys.addaudithook(guard)
for name in (
    'perceptra', 'perceptra.config', 'perceptra.schemas',
    'perceptra.ingestion.youtube', 'perceptra.ingestion.dataset_loader',
    'perceptra.nlp.cleaner', 'perceptra.nlp.sentiment', 'perceptra.nlp.aspects',
    'perceptra.analysis', 'fetch_youtube', 'save_data', 'clean_data',
    'sentiment_analysis', 'dynamic_aspects',
):
    importlib.import_module(name)
assert 'streamlit' not in sys.modules
print('All project modules imported without writes, downloads, or network access.')
'''
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=PROJECT_ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("All project modules imported")


def test_dependencies_and_nltk_resources_are_venv_local():
    import importlib.metadata
    import nltk
    assert Path(sys.prefix).resolve() == VENV_DIR.resolve()
    assert sys.prefix != sys.base_prefix
    for package in ("vaderSentiment", "nltk", "streamlit", "pytest", "langdetect"):
        location = Path(importlib.metadata.distribution(package).locate_file("")).resolve()
        assert location.is_relative_to(VENV_DIR.resolve()), (package, location)
    configure_nltk()
    assert nltk.data.path == [str(NLTK_DATA_DIR)]
    check_nltk_resources()


def test_wrappers_expose_canonical_functions_and_help():
    import clean_data
    import dynamic_aspects
    import fetch_youtube
    import save_data
    import sentiment_analysis
    from perceptra.ingestion import youtube
    from perceptra.nlp import aspects, cleaner, sentiment
    assert clean_data.clean_pipeline is cleaner.clean_pipeline
    assert sentiment_analysis.analyze_sentiment is sentiment.analyze_sentiment
    assert dynamic_aspects.extract_aspects is aspects.extract_aspects
    assert fetch_youtube.fetch_comments is youtube.fetch_comments
    assert save_data.collect_and_save is youtube.collect_and_save
    for name in ("clean_data.py", "sentiment_analysis.py", "dynamic_aspects.py", "fetch_youtube.py", "save_data.py"):
        result = subprocess.run([sys.executable, name, "--help"], cwd=PROJECT_ROOT,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_optional_collector_is_not_required_for_import():
    # The normal MVP install deliberately excludes the collectors extra.
    from perceptra.ingestion.youtube import fetch_comments
    assert fetch_comments("unused", max_comments=0) == []
