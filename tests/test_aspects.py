"""Day 1 resource/compatibility checks only; no service aspect integration yet."""

import pytest

from perceptra import config


def test_missing_nltk_resources_have_actionable_error(monkeypatch):
    import nltk
    def missing(*args, **kwargs):
        raise LookupError("Missing fixture resource")
    monkeypatch.setattr(nltk.data, "find", missing)
    with pytest.raises(LookupError, match="prepare_demo_data.py --prepare-nltk"):
        config.check_nltk_resources()
    assert nltk.data.path == [str(config.NLTK_DATA_DIR)]
