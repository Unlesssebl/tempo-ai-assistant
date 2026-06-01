"""
Метрики качества RAG.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from src.core.config import Config


@dataclass
class MetricsCollector:
    """Сбор метрик в JSONL."""

    config: Config

    def log_search(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool,
        retrieval_status: Optional[str] = None,
    ):
        if not self.config.enable_metrics:
            return

        self._write_event(
            {
                "type": "search",
                "timestamp": time.time(),
                "query": query,
                "num_results": num_results,
                "latency": latency,
                "cache_hit": cache_hit,
                "retrieval_status": retrieval_status,
            }
        )

    def _write_event(self, event: Dict):
        metrics_dir = Path("logs") / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        file_path = metrics_dir / "search_metrics.jsonl"
        with file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
