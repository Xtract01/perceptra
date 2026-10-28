from unittest.mock import Mock

import pytest

from perceptra.ingestion.youtube import collect_and_save, fetch_comments


def test_collector_enforces_requested_limit_without_extra_page():
    client = Mock()
    request = client.commentThreads.return_value.list.return_value
    request.execute.return_value = {"items": [
        {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "A comment", "likeCount": 0}}}}
        for _ in range(100)
    ]}
    assert len(fetch_comments("video", 50, client=client)) == 50
    client.commentThreads.return_value.list_next.assert_not_called()
    with pytest.raises(ValueError, match="nonnegative"):
        fetch_comments("video", -1, client=client)


def test_saver_only_collects_when_called(monkeypatch, tmp_path):
    from perceptra.ingestion import youtube
    monkeypatch.setattr(youtube, "collect_reviews", lambda *args, **kwargs: [{"comment": "Example", "likes": 0}])
    path = tmp_path / "raw.json"
    rows = collect_and_save("query", path)
    assert rows[0]["comment"] == "Example"
    assert path.exists()
