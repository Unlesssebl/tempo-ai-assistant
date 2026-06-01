"""
Кэширование чанков в JSON с автоинвалидацией

Ускоряет повторную векторизацию без пересоздания чанков.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional


class ChunksCache:
    """JSON-кэш для хранения готовых чанков с метаданными"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create(
        self,
        source_path: Path,
        chunker_fn: Callable[[Path], List[Dict]],
        force_refresh: bool = False,
    ) -> List[Dict]:
        """
        Возвращает чанки из кэша или создаёт новые.

        Args:
            source_path: Путь к исходному документу
            chunker_fn: Функция создания чанков: (Path) -> List[Dict]
            force_refresh: Игнорировать кэш и пересоздать чанки

        Returns:
            List[Dict]: Чанки с метаданными
        """
        cache_path = self._get_cache_path(source_path)
        source_hash = self._compute_hash(source_path)

        # Проверка валидности кэша
        if not force_refresh and cache_path.exists():
            try:
                cached = self._load_cache(cache_path)
                if cached["source_hash"] == source_hash:
                    print(f"  + Кэш: {source_path.name} ({len(cached['chunks'])} чанков)")
                    return cached["chunks"]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  ! Повреждён кэш {cache_path.name}: {e}")

        # Кэш невалиден — создаём чанки
        print(f"  > Chunking: {source_path.name}")
        chunks = chunker_fn(source_path)

        # Добавляем оценку токенов
        for chunk in chunks:
            if "tokens" not in chunk:
                chunk["tokens"] = self._estimate_tokens(chunk.get("text", ""))

        # Сохраняем в кэш
        self._save_cache(cache_path, source_path, source_hash, chunks)
        return chunks

    def _get_cache_path(self, source_path: Path) -> Path:
        """Путь к файлу кэша для исходного документа."""
        # Сохраняем структуру папок относительно data/
        rel_path = source_path.stem  # Без расширения
        parent = source_path.parent.name

        if parent != "data":
            cache_name = f"{parent}_{rel_path}.json"
        else:
            cache_name = f"{rel_path}.json"

        return self.cache_dir / cache_name

    def _compute_hash(self, path: Path) -> str:
        """MD5 хэш содержимого файла."""
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _estimate_tokens(self, text: str) -> int:
        """Оценка количества токенов (русский текст)."""
        # 1 токен ≈ 2.5 символа для русского
        return int(len(text) / 2.5)

    def _load_cache(self, cache_path: Path) -> Dict:
        """Загрузка кэша из JSON."""
        return json.loads(cache_path.read_text(encoding="utf-8"))

    def _save_cache(self, cache_path: Path, source_path: Path, source_hash: str, chunks: List[Dict]):
        """Сохранение чанков в JSON."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        total_tokens = sum(chunk.get("tokens", 0) for chunk in chunks)

        cache_data = {
            "source": str(source_path),
            "source_hash": source_hash,
            "created": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "total_tokens": total_tokens,
            "chunks": chunks,
        }

        cache_path.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  + Кэш сохранён: {len(chunks)} чанков, ~{total_tokens} токенов")

    def clear_cache(self, source_path: Optional[Path] = None):
        """
        Удаление кэша.

        Args:
            source_path: Удалить кэш конкретного файла (или всё, если None)
        """
        if source_path:
            cache_path = self._get_cache_path(source_path)
            if cache_path.exists():
                cache_path.unlink()
                print(f"Удалён кэш: {cache_path.name}")
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            print(f"Очищен кэш: {self.cache_dir}")

    def get_stats(self) -> Dict:
        """Статистика кэша."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_chunks = 0
        total_tokens = 0

        for cache_file in cache_files:
            try:
                cached = self._load_cache(cache_file)
                total_chunks += cached.get("total_chunks", 0)
                total_tokens += cached.get("total_tokens", 0)
            except Exception:
                continue

        return {
            "cached_documents": len(cache_files),
            "total_chunks": total_chunks,
            "total_tokens": total_tokens,
        }
