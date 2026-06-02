import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from rapidfuzz import process, fuzz, utils

logger = logging.getLogger(__name__)

class ContactSearchTool:
    def __init__(self, db_path: str = "data/shared/contacts.db"):
        self.db_path = db_path

    async def search(self, target_person: str, target_company: Optional[str] = None) -> str:
        """
        Поиск контактов в SQLite с использованием нечеткого сравнения (Fuzzy Matching).
        """
        if not target_person:
            return "Не указано имя или должность для поиска."

        # Логирование перед поиском
        logger.info(f"[SQL SEARCH] Intent: contact_search | Person: {target_person} | Company: {target_company}")

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # 1. Извлекаем ВСЕХ контакты (база небольшая, это безопасно)
                query = "SELECT * FROM contacts"
                async with db.execute(query) as cursor:
                    rows = await cursor.fetchall()
                
                if not rows:
                    return "База контактов пуста."

                # Маппинг коротких ID компаний в ключевые слова для поиска в поле company
                COMPANY_ID_TO_KEYWORDS = {
                    "technotron": ["технотрон"],
                    "metiz":      ["метиз"],
                    "kmk":        ["кмк", "тэмпо"],
                    "ntz":        ["нтз", "тэм-по"],
                    "itz":        ["итз"],
                    "kzmk":       ["кзмк"],
                    "zteo":       ["зтэо"],
                    "td":         ["тд", "торговый"],
                    "sks":        ["скс"],
                    "port":       ["порт"],
                    "it":         ["айти"],
                }
                # Подготавливаем слова для бонус-фильтра по компании
                target_comp_words = []
                if target_company:
                    comp_lower = target_company.strip().lower()
                    if comp_lower in COMPANY_ID_TO_KEYWORDS:
                        # Использовать русские ключевые слова вместо ID
                        target_comp_words = COMPANY_ID_TO_KEYWORDS[comp_lower]
                    else:
                        target_comp_words = [w.strip().lower() for w in target_company.split() if len(w.strip()) > 2]

                # 2. Нечеткий поиск
                results_with_scores = []
                for row in rows:
                    # Считаем скор для каждого поля отдельно
                    scores = [
                        fuzz.WRatio(target_person, row['full_name'], processor=utils.default_process),
                        fuzz.WRatio(target_person, row['position'], processor=utils.default_process),
                        fuzz.WRatio(target_person, row['department'], processor=utils.default_process)
                    ]
                    # Дополнительно добавим partial_ratio для ФИО, чтобы лучше ловить частичные совпадения (одно слово)
                    partial_score = fuzz.partial_ratio(target_person, row['full_name'], processor=utils.default_process)
                    
                    max_score = max(max(scores), partial_score)
                    
                    if max_score >= 70: # Порог вхождения
                        # СТРОГИЙ ФИЛЬТР ПО КОМПАНИИ
                        if target_comp_words:
                            row_comp = (row['company'] or "").lower()
                            
                            # Проверяем пересечение слов
                            if not any(w in row_comp for w in target_comp_words):
                                continue
                                
                            # Спец. защита от путаницы Технотрон и Технотрон-Метиз
                            if "метиз" in row_comp and "метиз" not in target_comp_words:
                                continue # Искали Технотрон, а попали на Метиз
                            if "метиз" in target_comp_words and "метиз" not in row_comp:
                                continue # Искали Метиз, а попали на обычный Технотрон
                                
                        results_with_scores.append((max_score, row))

                # Сортируем по убыванию скора
                results_with_scores.sort(key=lambda x: x[0], reverse=True)
                
                # Умная обрезка результатов, чтобы LLM не путалась в похожих фамилиях
                top_results = []
                if results_with_scores:
                    best_score = results_with_scores[0][0]
                    # Если есть явный лидер с высокой уверенностью
                    if best_score >= 90:
                        # Берем только тех, кто отстает от лидера не более чем на 5 баллов
                        top_results = [r for r in results_with_scores if best_score - r[0] <= 5][:3]
                    else:
                        # Иначе берем стандартный топ-3
                        top_results = results_with_scores[:3]

                formatted_results = []
                for score, row in top_results:
                    logger.info(f"[SQL SEARCH] Match found: {row['full_name']} | Score: {score}")
                    formatted_results.append(
                        f"{len(formatted_results) + 1}. {row['full_name']} — {row['position']}\n"
                        f"   Отдел: {row['department']}, Компания: {row['company']}\n"
                        f"   Тел: {row['phone']}"
                    )

                if not formatted_results:
                    return f"По запросу '{target_person}' ничего не найдено."

                return "Найдены контакты:\n" + "\n\n".join(formatted_results)

        except Exception as e:
            logger.error(f"ContactSearchTool error: {e}")
            return "Произошла ошибка при поиске в базе контактов."
