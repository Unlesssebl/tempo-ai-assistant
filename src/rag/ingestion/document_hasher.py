"""
Хеширование документов для инкрементального обновления.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict

from src.core.config import Config


class DocumentHasher:
    """Отслеживание изменений документов через SHA256."""

    def __init__(self, config: Config):
        self.config = config
        self.hash_file = Path(config.document_hashes_path)
        self.hashes = self._load_hashes()

    def _get_rel_path(self, filepath: Path) -> str:
        """Приведение пути к относительному и нормализованному виду (с прямыми слешами)."""
        try:
            rel = filepath.relative_to(Path(self.config.data_path))
            return str(rel).replace("\\", "/")
        except ValueError:
            return str(filepath).replace("\\", "/")

    def compute_hash(self, filepath: Path) -> str:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()

    def has_changed(self, filepath: Path) -> bool:
        current_hash = self.compute_hash(filepath)
        stored_hash = self.hashes.get(self._get_rel_path(filepath))
        return current_hash != stored_hash

    def update_hash(self, filepath: Path):
        self.hashes[self._get_rel_path(filepath)] = self.compute_hash(filepath)

    def save(self):
        self.hash_file.parent.mkdir(parents=True, exist_ok=True)
        with self.hash_file.open("w", encoding="utf-8") as f:
            json.dump(self.hashes, f, ensure_ascii=False, indent=2)

    def _load_hashes(self) -> Dict[str, str]:
        if not self.hash_file.exists():
            return {}
        try:
            with self.hash_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
