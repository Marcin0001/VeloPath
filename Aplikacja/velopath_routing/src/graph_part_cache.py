from __future__ import annotations

import hashlib
import json
import time
import pickle
from pathlib import Path
from typing import Any, Hashable
from collections.abc import Callable

class GraphPartCache:
    def __init__(
        self,
        cache_dir: str | Path = ".cache/graph_parts",
        ttl_s: int = 86400
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.ttl_s = ttl_s
        self.cache_dir.mkdir(parents = True, exist_ok = True)

    def _make_key(self, query_params: dict[str, Any]) -> str:
        raw = json.dumps(query_params, sort_keys = True, ensure_ascii = False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.pkl"

    def get(self, query_params: dict[str, Any]) -> Any | None:
        path = self._entry_path(self._make_key(query_params))
        if not path.exists():
            return None
        with path.open("rb") as file:
            record = pickle.load(file)
        if time.time() - record["timestamp"] > self.ttl_s:
            path.unlink(missing_ok = True)
            return None
        return record["data"]

    def set(self, query_params: dict[str, Any], data: Any) -> None:
        path = self._entry_path(self._make_key(query_params))
        record = {"timestamp": time.time(), "data": data}
        with path.open("wb") as file:
            pickle.dump(record, file, protocol = pickle.HIGHEST_PROTOCOL)

    def get_or_fetch(self, query_params: dict[str, Any], fetcher: Callable[[], Any]):
        cached = self.get(query_params = query_params)
        if cached is not None:
            return cached
        data = fetcher()
        self.set(query_params, data)
        return data