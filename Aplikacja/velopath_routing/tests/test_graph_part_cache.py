import time
import pytest
from src import graph_part_cache
from pathlib import Path

def test_set_and_get_cached_data(tmp_path: Path) -> None:
    cache = graph_part_cache.GraphPartCache(
        cache_dir = tmp_path
    )
    query_params = {
        "bbox": (12.34, 56.78, 43.21, 87.65),
        "network_type": "bike",
    }
    data = {"nodes": 20, "edges": 45}

    assert cache.get(query_params = query_params) is None
    
    cache.set(query_params = query_params, data = data)
    assert cache.get(query_params = query_params) == data

def test_cache_entry_expiration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = graph_part_cache.GraphPartCache(
        cache_dir = tmp_path,
        ttl_s = 100
    )

    query_params = {
        "bbox": (12.34, 56.78, 43.21, 87.65),
        "network_type": "bike",
    }

    monkeypatch.setattr(
        time,
        "time",
        lambda: 400.0
    )
    cache.set(query_params = query_params, data = "graph_cache")
    assert list(tmp_path.iterdir()) != []

    monkeypatch.setattr(
        time,
        "time",
        lambda: 450.0
    )
    assert cache.get(query_params = query_params) == "graph_cache"
    assert list(tmp_path.iterdir()) != []

    monkeypatch.setattr(
        time,
        "time",
        lambda: 500.0
    )
    assert cache.get(query_params = query_params) == "graph_cache"
    assert list(tmp_path.iterdir()) != []

    monkeypatch.setattr(
        time,
        "time",
        lambda: 500.0001
    )
    assert cache.get(query_params = query_params) is None
    assert list(tmp_path.iterdir()) == []

def test_get_or_fetch_fetcher_call(tmp_path: Path) -> None:
    cache = graph_part_cache.GraphPartCache(
        cache_dir = tmp_path
    )
    query_params = {
        "bbox": (12.34, 56.78, 43.21, 87.65),
        "network_type": "bike",
    }
    call_count = 0

    def fetcher():
        nonlocal call_count
        call_count += 1
        return f"fetched_{call_count}"

    assert cache.get_or_fetch(query_params = query_params, fetcher = fetcher) == "fetched_1"
    assert cache.get_or_fetch(query_params = query_params, fetcher = fetcher) == "fetched_1"
    assert call_count == 1