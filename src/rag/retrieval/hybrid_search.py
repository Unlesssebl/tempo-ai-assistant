"""
Hybrid Search: Vector + BM25 с Reciprocal Rank Fusion.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple, Any

from rank_bm25 import BM25Okapi

from src.core.clients import ClientManager
from src.core.config import Config
from src.rag.retrieval.morphology import RussianMorphology
from src.rag.retrieval.fuzzy_name_matcher import FuzzyNameMatcher

logger = logging.getLogger(__name__)

# Словарь для нормализации аббревиатур при поиске имен файлов
ACRONYM_MAP = {
    "абк": "abk", 
    "итз": "itz", 
    "кмк": "kmk", 
    "тэмпо": "tempo", 
    "цхп": "chp",
    "нтз": "ntz",
    "кзмк": "kzmk",
    "зтэо": "zteo",
    "птфк": "technotron",
    "технотрон": "technotron"
}


class HybridSearchService:
    """Hybrid Search с RRF fusion (vector + BM25)."""

    def __init__(self, config: Config):
        self.config = config
        self.client_manager = ClientManager.get_instance(config)
        
        # Кэш для BM25 индекса
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_ids: List[str] = []
        self.corpus_texts: List[str] = []
        self.payload_by_id: Dict[str, Dict] = {}
        
        # Потокобезопасность
        self._bm25_lock = asyncio.Lock()
        self._initialized = False
        
        self.morphology = RussianMorphology()
        self.name_matcher = FuzzyNameMatcher()

    async def initialize(self):
        """Явная инициализация индексов при старте сервиса."""
        async with self._bm25_lock:
            if self._initialized:
                return
            
            logger.info("[+] Инициализация HybridSearchService (BM25 + FuzzyMatcher)...")
            points = await self._load_all_points()
            if points:
                await asyncio.to_thread(self._build_bm25_index, points)
                self._initialized = True
                logger.info("[+] HybridSearchService успешно инициализирован")
            else:
                logger.warning("[!] Нет данных для построения BM25 индекса")

    async def search(self, query: str, limit: int = 10, company_id: Optional[str] = None, qdrant_filter: Optional[Any] = None, intent: Optional[str] = None) -> List[Dict]:
        """Hybrid search с RRF fusion и поддержкой фильтров."""
        if not self._initialized:
            await self.initialize()

        query_lower = query.lower()
        
        # ── Нечёткая коррекция имён ──
        corrected_query, was_corrected = self.name_matcher.correct_query(query)
        if was_corrected:
            logger.info("[F] Запрос скорректирован FuzzyNameMatcher: '%s' → '%s'", query, corrected_query)
            query = corrected_query

        # Векторный поиск (всегда уважает фильтр)
        vector_results = await self._vector_search(query, self.config.vector_fetch_limit, qdrant_filter=qdrant_filter)
        vector_ranking = {r["id"]: rank for rank, r in enumerate(vector_results)}

        # BM25 поиск (теперь с синхронизацией фильтров)
        # Если это emergency - отключаем BM25 для исключения "шума" лексических совпадений
        if intent == "emergency":
            logger.info("🚨 EMERGENCY INTENT: BM25 disabled, relying on Vector/Tags only.")
            bm25_ranking = {}
        else:
            # Ограничиваем BM25 только если это НЕ поиск локаций, контактов или HR-политик
            # (для них лексическая точность критически важна, а вектора могут промахиваться)
            lax_intents = ["location_search", "contact_search", "hr_policy"]
            use_strict_filtering = qdrant_filter and intent not in lax_intents
            allowed_ids = {r["id"] for r in vector_results} if use_strict_filtering else None
            
            # BM25 теперь принимает company_id для независимой фильтрации
            bm25_ranking = self._bm25_ranking(
                query, 
                self.config.bm25_fetch_limit, 
                allowed_ids=allowed_ids, 
                company_id=company_id
            )

        rrf_scores = self._rrf_fusion(vector_ranking, bm25_ranking)
        
        # ─── Аддитивное ранжирование с бонусами (RRF + Bonuses) ───
        target_company_id = company_id
        if company_id:
            # Маппинг для определения предприятия по ключевым словам в запросе
            company_keywords = {
                "technotron": ["технотрон", "птфк", "тихнотрон"],
                "metiz": ["метиз", "саморез", "технотрон-метиз"],
                "ntz": ["нтз"],
                "itz": ["итз"],
                "kmk": ["кмк"],
                "kzmk": ["кзмк"],
                "zteo": ["зтэо"],
                "td": ["тд", "торговый дом"],
                "it": ["айти", "it"],
                "sks": ["скс"],
                "port": ["порт"]
            }
            for cid, keywords in company_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    target_company_id = cid
                    break

        final_rrf_results = {}
        for doc_id, base_score in rrf_scores.items():
            payload = self.payload_by_id.get(doc_id, {})
            source = payload.get("source", "").lower().replace("\\", "/")
            doc_text = (payload.get("original_text") or payload.get("text", "")).lower()
            
            bonus = 0.0
            if not source:
                continue

            # Инициализация system_hints в метаданных документа при начислении бонусных баллов
            if "metadata" not in payload or not isinstance(payload["metadata"], dict):
                payload["metadata"] = {}
            else:
                payload["metadata"] = dict(payload["metadata"])
            payload["metadata"]["system_hints"] = []
            
            # 1. СМАРТ-ПОИСК ЧИСЕЛ (Regex Context Match)
            # Ищем цифры в запросе и проверяем их контекст в документе
            numbers_in_query = re.findall(r'\b\d{1,4}\b', query_lower)
            has_number_bonus = False
            for num in numbers_in_query:
                # Паттерн ищет число рядом с ключевым словом (АБК 2, Кабинет 10, Цех 5)
                context_pattern = rf"(?i)(абк|abk|кабинет|цех|этаж|офис|№|номер|корпус|блок)[\s\-]*{num}\b"
                if re.search(context_pattern, doc_text) or re.search(context_pattern, source):
                    bonus += 0.15 # Существенный бонус за точное совпадение объекта
                    logger.debug(f"🚀 SMART NUMBER BONUS +0.15 for '{num}' in {source}")
                    has_number_bonus = True

            if has_number_bonus:
                payload["metadata"]["system_hints"].append("Содержит искомый номер/кабинет")

            # 2. БУСТ ПО ИМЕНИ ФАЙЛА (Acronym Mapping Match)
            filename = source.split("/")[-1].split(".")[0].lower().replace("_", "")
            # Нормализуем запрос через словарь акронимов
            normalized_query = query_lower
            for cyr, lat in ACRONYM_MAP.items():
                normalized_query = normalized_query.replace(cyr, lat)
            
            clean_query = normalized_query.replace("-", "").replace(" ", "")
            if filename in clean_query or clean_query in filename:
                bonus += 0.3 # Гарантированный топ для навигационных запросов
                logger.info(f"🎯 FILENAME MATCH BONUS +0.3 for {source}")
                payload["metadata"]["system_hints"].append("Точное совпадение имени файла")
            
            # 3. ТЕМАТИЧЕСКИЕ УРОВНИ (Tiers)
            is_target_company = False
            if target_company_id:
                # Маппинг UI-названия компании в имя папки (через ACRONYM_MAP)
                target_folder = target_company_id.lower()
                for cyr, lat in ACRONYM_MAP.items():
                    target_folder = target_folder.replace(cyr, lat)
                
                # Очищаем от лишних префиксов и кавычек для сравнения с путем
                def clean_folder_name(name: str) -> str:
                    name = name.lower()
                    name = name.replace("technotron", "технотрон")
                    name = name.replace("zteo", "зтэо")
                    name = name.replace("kmk", "кмк")
                    name = name.replace("ntz", "нтз")
                    name = name.replace("itz", "итз")
                    name = name.replace("metiz", "метиз")
                    name = name.replace("gk", "гк")
                    name = name.replace("tempo", "тэмпо")
                    for prefix in ["ao", "ooo", "gk", "ip", "ptfk", "ао", "ооо", "гк", "ип", "птфк"]:
                        name = name.replace(prefix, "")
                    return "".join(re.findall(r"[a-zа-я0-9]", name))

                clean_target = clean_folder_name(target_folder)
                clean_source = clean_folder_name(source.split('/')[0])

                is_target_company = (clean_target == clean_source) or (clean_target in clean_source and len(clean_target) > 2) or (clean_source in clean_target and len(clean_source) > 2)

            # Ключевые слова для определения интента
            location_keywords = ["где", "адрес", "найти", "локация", "местоположение", "добраться", "пройти", "проехать", "карта"]
            is_location_query = any(lkw in query_lower for lkw in location_keywords)
            hr_keywords = ["работа", "трудоустройство", "вакансия", "прием", "найм", "увольнение", "отпуск", "больничный", "кадры"]
            is_hr_query = any(hkw in query_lower for hkw in hr_keywords)

            # Уровень 0: Локации
            if "01_company/locations/" in source and is_location_query:
                bonus += 0.5 # Повышаем приоритет общих зданий (АБК), чтобы они на равных конкурировали с файлами внутри папки компании
            
            # Уровень 0.5: HR - Значительно усиливаем приоритет детальных документов
            elif is_hr_query and "02_hr/" in source:
                bonus += 0.25

            # Уровень 0.7: Совпадение с questions_answered (если есть в метаданных)
            q_answered = payload.get("questions_answered", [])
            if q_answered and any(query_lower in str(q).lower() or str(q).lower() in query_lower for q in q_answered):
                bonus += 0.3
                logger.info(f"🎯 MATCH BONUS: Query matches 'questions_answered' in {source}")
                
            # Уровень 1: Предприятие
            if is_target_company:
                bonus += 0.5
            
            final_rrf_results[doc_id] = base_score + bonus

        sorted_ids = sorted(final_rrf_results.keys(), key=lambda x: final_rrf_results[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:limit]:
            payload = self.payload_by_id.get(doc_id, {})
            p_text = payload.get("parent_text", "")
            logger.info(f"DEBUG: HybridSearch point {doc_id} (source: {payload.get('source')}). Has parent: {bool(p_text)}, len: {len(p_text)}")
            results.append({
                "id": doc_id,
                "text": payload.get("text", ""),
                "original_text": payload.get("original_text", ""),
                "source": payload.get("source", "Unknown"),
                "score": final_rrf_results.get(doc_id, 0.0),
                "metadata": payload.get("metadata", {}),
                "parent_text": payload.get("parent_text", ""),
            })

        return results

    async def _vector_search(self, query: str, limit: int, qdrant_filter: Optional[Any] = None) -> List[Dict]:
        """Векторный поиск с правильным task_type и ротацией ключей."""
        loop = asyncio.get_running_loop()
        akm = self.client_manager.api_key_manager
        
        max_retries = 10 if akm else 1
        last_error = None
        
        for attempt in range(max_retries):
            current_key = akm.get_current_key() if akm else self.config.gemini_api_key
            embedder = self.client_manager.get_embedder(api_key=current_key)
            
            try:
                query_vector = await loop.run_in_executor(
                    None,
                    lambda: embedder.encode(query, task_type="RETRIEVAL_QUERY", normalize=True),
                )
                
                # Если успешно - выходим из цикла
                if query_vector.ndim > 1:
                    query_vector = query_vector[0]
                query_list = query_vector.tolist()
                break
                
            except Exception as e:
                last_error = e
                err_str = str(e).upper()
                is_rate_error = any(x in err_str for x in ["429", "RESOURCE_EXHAUSTED"])
                
                if is_rate_error and akm:
                    logger.warning(
                        "Rate limit (429) для embeddings (попытка %d/%d). Ротация ключа... (Key: ...%s)",
                        attempt + 1, max_retries, current_key[-4:]
                    )
                    akm.mark_key_exhausted(current_key, f"embedding rate limit: {err_str}")
                    
                    if akm.is_all_exhausted():
                        logger.error("Все API ключи исчерпаны для эмбеддингов!")
                        from src.core.exceptions import SearchError
                        raise SearchError(f"Embedding quota exceeded for all keys: {e}") from e
                    
                    # Продолжаем цикл для следующей попытки с новым ключом
                    continue
                
                # Другие ошибки не ретраим
                logger.error("Ошибка при генерации вектора запроса: %s", e)
                from src.core.exceptions import SearchError
                raise SearchError(f"Vector generation failed: {e}") from e
        else:
            from src.core.exceptions import SearchError
            raise SearchError(f"Failed to generate vector after {max_retries} attempts.") from last_error

        client = self.client_manager.get_qdrant_client()
        try:
            search_result = await loop.run_in_executor(
                None,
                lambda: client.query_points(
                    collection_name=self.config.collection_name,
                    query=query_list,
                    query_filter=qdrant_filter,
                    limit=limit,
                    with_payload=True,
                ),
            )
        except ValueError as e:
            if "not found" in str(e).lower():
                logger.warning(f"Collection {self.config.collection_name} not found. Skipping vector search.")
                return []
            raise

        results = []
        for point in search_result.points:
            payload = point.payload or {}
            doc_id = str(point.id)
            self.payload_by_id.setdefault(doc_id, payload)
            results.append(
                {
                    "id": doc_id,
                    "score": point.score,
                    "text": payload.get("text", ""),
                    "original_text": payload.get("original_text", ""),
                    "source": payload.get("source", "Unknown"),
                    "parent_text": payload.get("parent_text"),
                    "parent_id": payload.get("parent_id"),
                    "chunk_index": payload.get("chunk_index"),
                }
            )
        return results

    def _bm25_ranking(self, query: str, limit: int, allowed_ids: Optional[set] = None, company_id: Optional[str] = None) -> Dict[str, int]:
        """Ранжирование BM25 для query с опциональной фильтрацией по allowed_ids и company_id."""
        if not self.bm25 or not self.corpus_texts:
            return {}

        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        
        indexed = []
        for i, score in enumerate(scores):
            if score <= 0:
                continue
            doc_id = self.corpus_ids[i]
            
            # 1. Если задан фильтр allowed_ids - проверяем вхождение
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue
                
            # 2. Если задан фильтр по компании - проверяем метаданные документа
            if company_id:
                payload = self.payload_by_id.get(doc_id, {})
                doc_company = str(payload.get("company", ""))
                doc_dept = str(payload.get("department", ""))
                
                # Нормализация для сравнения (убираем АО/ООО, кавычки и приводим к нижнему регистру)
                def normalize(name: str) -> str:
                    name = name.lower()
                    name = name.replace("technotron", "технотрон")
                    name = name.replace("zteo", "зтэо")
                    name = name.replace("kmk", "кмк")
                    name = name.replace("ntz", "нтз")
                    name = name.replace("itz", "итз")
                    name = name.replace("metiz", "метиз")
                    name = name.replace("gk", "гк")
                    name = name.replace("tempo", "тэмпо")
                    
                    for prefix in ["ао", "ооо", "гк", "ип", "птфк", "ao", "ooo", "gk", "ip", "ptfk"]:
                        name = name.replace(prefix, "")
                    return "".join(re.findall(r"[a-zа-я0-9]", name))

                norm_doc = normalize(doc_company)
                norm_target = normalize(company_id)
                norm_gk = normalize("ГК «ТЭМПО»")

                # Разрешаем если это целевая компания, или холдинг, или общий отдел
                # Также разрешаем, если одно название содержится в другом (для надежности)
                is_match = (norm_doc == norm_target) or (norm_doc in norm_target and len(norm_doc) > 2) or (norm_target in norm_doc and len(norm_target) > 2)
                
                if not is_match and norm_doc != norm_gk and doc_dept != "General":
                    continue
                    
            indexed.append((doc_id, score))
            
        indexed.sort(key=lambda x: x[1], reverse=True)
        top = indexed[:limit]
        
        results = {doc_id: rank for rank, (doc_id, score) in enumerate(top)}
        if results:
            first_id, first_score = top[0]
            logger.info(f"📝 BM25: топ результат score={first_score:.2f} для '{query}' (allowed_filter={allowed_ids is not None}, company_filter={company_id is not None})")
        return results

    def _rrf_fusion(self, ranking_a: Dict[str, int], ranking_b: Dict[str, int]) -> Dict[str, float]:
        """Reciprocal Rank Fusion."""
        k = self.config.rrf_k
        all_ids = set(ranking_a.keys()) | set(ranking_b.keys())
        scores: Dict[str, float] = {}
        for doc_id in all_ids:
            score = 0.0
            if doc_id in ranking_a:
                score += 1.0 / (k + ranking_a[doc_id])
            if doc_id in ranking_b:
                score += 1.0 / (k + ranking_b[doc_id])
            scores[doc_id] = score
        return scores

    async def _load_all_points(self) -> List[Tuple[str, Dict]]:
        """Загрузка всех точек из Qdrant для BM25."""
        client = self.client_manager.get_qdrant_client()
        loop = asyncio.get_running_loop()

        all_points: List[Tuple[str, Dict]] = []
        offset = None

        try:
            while True:
                points, next_offset = await loop.run_in_executor(
                    None,
                    lambda off=offset: client.scroll(
                        collection_name=self.config.collection_name,
                        limit=256,
                        offset=off,
                        with_payload=True,
                        with_vectors=False,
                    ),
                )

                for point in points:
                    all_points.append((str(point.id), point.payload or {}))

                if next_offset is None:
                    break
                offset = next_offset
        except ValueError as e:
            if "not found" in str(e).lower():
                logger.warning(f"Collection {self.config.collection_name} not found. BM25 will be disabled.")
                return []
            raise

        return all_points

    def _build_bm25_index(self, points: List[Tuple[str, Dict]]):
        """Построение BM25 индекса."""
        self.corpus_ids = []
        self.corpus_texts = []
        self.payload_by_id = {}

        for doc_id, payload in points:
            text = payload.get("original_text") or payload.get("text", "")
            self.corpus_ids.append(doc_id)
            self.corpus_texts.append(text)
            self.payload_by_id[doc_id] = payload

        tokenized = [self._tokenize(text) for text in self.corpus_texts]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

        # Строим словарь имён для FuzzyNameMatcher (одновременно с BM25)
        self.name_matcher.rebuild(self.corpus_texts)
        logger.info("[+] FuzzyNameMatcher словарь готов")

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\w+", text.lower())
        # Apply morphological normalization
        normalized = []
        for token in tokens:
            lemma = self.morphology.lemmatize_word(token)
            if lemma:
                normalized.append(lemma)
                # Add fuzzy variants for common Russian surname substitutions
                fuzzy_variants = self._generate_fuzzy_variants(lemma)
                if fuzzy_variants:
                    logger.debug(f"Fuzzy variants for '{lemma}': {fuzzy_variants}")
                normalized.extend(fuzzy_variants)
            else:
                # If no lemmatization, use token directly and add fuzzy variants
                normalized.append(token)
                fuzzy_variants = self._generate_fuzzy_variants(token)
                normalized.extend(fuzzy_variants)
        logger.debug(f"Tokenized '{text}' -> {normalized}")
        return normalized

    def _generate_fuzzy_variants(self, word: str) -> List[str]:
        """Generate fuzzy variants for common Russian surname substitutions."""
        variants = []
        logger.debug(f"Generating fuzzy variants for word: '{word}'")
        
        # Common vowel substitutions in Russian surnames
        vowel_substitutions = {
            'е': 'и', 'и': 'е',  # е <-> и
            'а': 'о', 'о': 'а',  # а <-> о
            'ы': 'у', 'у': 'ы',  # ы <-> у
        }
        
        # Generate variants with vowel substitutions
        for from_vowel, to_vowel in vowel_substitutions.items():
            if from_vowel in word:
                variant = word.replace(from_vowel, to_vowel)
                if variant != word:
                    variants.append(variant)
                    logger.debug(f"Added vowel variant: '{variant}' (from '{word}' with {from_vowel}->{to_vowel})")
        
        # Special case for common surname patterns
        if word.endswith('ev'):
            variant = word[:-2] + 'ov'
            variants.append(variant)
            logger.debug(f"Added suffix variant: '{variant}' (from '{word}')")
        elif word.endswith('ov'):
            variant = word[:-2] + 'ev'
            variants.append(variant)
            logger.debug(f"Added suffix variant: '{variant}' (from '{word}')")
        elif word.endswith('eva'):
            variant = word[:-3] + 'ova'
            variants.append(variant)
            logger.debug(f"Added suffix variant: '{variant}' (from '{word}')")
        elif word.endswith('ova'):
            variant = word[:-3] + 'eva'
            variants.append(variant)
            logger.debug(f"Added suffix variant: '{variant}' (from '{word}')")
        
        logger.debug(f"Total fuzzy variants for '{word}': {variants}")
        return variants

    async def clear_cache(self):
        """Очистка кэша BM25 индекса."""
        async with self._bm25_lock:
            self.bm25 = None
            self._bm25_corpus = None
            self.corpus_ids = []
            self.corpus_texts = []
            self.payload_by_id = {}
            logger.info("🧹 Кэш BM25 очищен")
