import logging
from typing import Optional, Any
from pydantic import BaseModel, Field
import asyncpg
from src.core.config import Config

logger = logging.getLogger(__name__)

class ContactSearchInput(BaseModel):
    """Схема входных аргументов для инструмента поиска контактов."""
    search_query: str = Field(
        description="Имя, фамилия, должность или функция искомого лица (например, 'Иванов', 'Управляющий')"
    )
    company_filter: Optional[str] = Field(
        default=None,
        description="Название компании для фильтрации контактов (например, 'КМК', 'ЗТЭО', 'ИТЗ')"
    )
    exact_phone: Optional[str] = Field(
        default=None,
        description="Точный номер телефона для поиска владельца контакта"
    )

class ContactSearchTool:
    """Инструмент для поиска контактов в PostgreSQL с использованием pg_trgm."""
    
    def __init__(self, config: Optional[Config] = None, db_path: Optional[str] = None):
        # Принимаем config или инициализируем его по умолчанию. 
        # db_path оставлен для обратной совместимости, но больше не используется.
        self.config = config or Config.from_env()
        self.db_url = self.config.database_url

    async def search(
        self, 
        search_query: str = "", 
        company_filter: Optional[str] = None, 
        exact_phone: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Выполняет поиск контактов в PostgreSQL с использованием триграммного поиска.
        """
        # Логирование перед поиском
        logger.info(
            f"[PG SEARCH] query: '{search_query}' | company: '{company_filter}' | phone: '{exact_phone}'"
        )

        # Валидация входных данных через Pydantic схему
        try:
            params_validated = ContactSearchInput(
                search_query=search_query,
                company_filter=company_filter,
                exact_phone=exact_phone
            )
        except Exception as e:
            logger.error(f"Validation error in ContactSearchTool: {e}")
            return f"Ошибка валидации параметров поиска: {e}"

        # Если поисковый запрос состоит только из цифр, а exact_phone не задан,
        # перенаправляем запрос в exact_phone для точного поиска по номеру
        q_digits = "".join(c for c in params_validated.search_query if c.isdigit())
        if q_digits and len(q_digits) >= 4 and not params_validated.exact_phone:
            params_validated.exact_phone = params_validated.search_query
            params_validated.search_query = ""

        if not params_validated.search_query and not params_validated.exact_phone:
            return "Не указано имя, должность или телефон для поиска."

        conditions = []
        params = []
        param_idx = 1
        select_sml = "0.0 as sml"

        # Фильтр по имени/должности с триграммным сходством
        if params_validated.search_query:
            params.append(params_validated.search_query)  # $1
            params.append(f"%{params_validated.search_query}%")  # $2
            select_sml = "similarity(full_name, $1) as sml"
            conditions.append(
                "(similarity(full_name, $1) > 0.3 OR full_name ILIKE $2 OR position ILIKE $2)"
            )
            param_idx = 3

        # Фильтр по компании
        if params_validated.company_filter:
            params.append(f"%{params_validated.company_filter}%")
            conditions.append(f"company ILIKE ${param_idx}")
            param_idx += 1

        # Фильтр по номеру телефона (с очисткой от нецифровых символов)
        if params_validated.exact_phone:
            phone_digits = "".join(c for c in params_validated.exact_phone if c.isdigit())
            if len(phone_digits) >= 4:
                params.append(f"%{phone_digits}%")
                conditions.append(
                    f"regexp_replace(phone, '\\D', '', 'g') ILIKE ${param_idx}"
                )
                param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT id, company, department, full_name, position, phone, {select_sml}
            FROM contacts
            WHERE {where_clause}
            ORDER BY sml DESC
            LIMIT 5
        """

        try:
            if not self.db_url:
                raise ValueError("DATABASE_URL не задана в конфигурации.")

            conn = await asyncpg.connect(self.db_url)
            try:
                rows = await conn.fetch(query, *params)
            finally:
                await conn.close()

            if not rows:
                search_term = params_validated.search_query or params_validated.exact_phone
                return f"По запросу '{search_term}' ничего не найдено."

            formatted_results = []
            for i, row in enumerate(rows, 1):
                logger.info(f"[PG SEARCH] Match found: {row['full_name']} | Similarity: {row.get('sml', 0.0):.3f}")
                formatted_results.append(
                    f"{i}. {row['full_name'] or '—'} — {row['position'] or '—'}\n"
                    f"   Отдел: {row['department'] or '—'}, Компания: {row['company'] or '—'}\n"
                    f"   Тел: {row['phone'] or '—'}"
                )

            return "Найдены контакты:\n\n" + "\n\n".join(formatted_results)

        except Exception as e:
            logger.exception(f"ContactSearchTool error: {e}")
            return "Произошла ошибка при поиске в базе контактов."
