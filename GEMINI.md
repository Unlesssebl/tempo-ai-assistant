# Инструкции для AI-агента — TempoAI Assistant

Этот файл является системным руководством для AI-агентов в данном воркспейсе.
Он содержит **правила, принципы и архитектурные ограничения** проекта.

> [!IMPORTANT]
> Перед внесением изменений ознакомьтесь с документацией в каталоге [`docs/`](docs/):
> - **Интеграция с IntraService:** [`docs/INTRASERVICE.md`](docs/INTRASERVICE.md)
> - **Интеграция с Active Directory:** [`docs/AD_INTEGRATION.md`](docs/AD_INTEGRATION.md)
> - **Чанкинг и векторизация:** [`docs/SMART_CHUNKER.md`](docs/SMART_CHUNKER.md)
> - **Голосовая обработка:** [`docs/VOICE_PROCESSING.md`](docs/VOICE_PROCESSING.md)
> - **План проекта:** [`plan.md`](plan.md)

---

## 0. Поддержание порядка в документации
- **Только правила и инварианты:** Настройки RAG, модели и промпты настраиваются в [`models_config.yaml`](models_config.yaml).
- **Сквозная архитектура:** Схемы IntraService и Active Directory согласовываются с `../prism/20_Architecture/`.

---

## 1. Архитектура системы
- `src/` — Ядро ассистента:
  - `rag/` — Поиск по векторной базе (Qdrant) и гибридный поиск.
  - `llm/` — Клиенты моделей (Gemini API, ротация ключей).
  - `integrations/` — Взаимодействие с IntraService и Active Directory.
- Точки входа:
  - `run_bot.py` / `run_tg_bot.py` — Telegram-бот.
  - `run_max_bot.py` — Бот для мессенджера MAX.
  - `run_all_bots.py` — Одновременный запуск обоих ботов в одном event loop.
  - `run_server.py` — FastAPI REST API сервер.

---

## 2. Ключевые архитектурные принципы
1. **Ротация API-ключей Gemini:**
   - При превышении квоты (429 Rate Limit) происходит автоматическое переключение на следующий ключ из конфигурации.
2. **Qdrant Storage v2:**
   - Векторные коллекции хранятся локально/в контейнере; чанкирование выполняется с сохранением метаданных заголовков.
3. **Изоляция контактов:**
   - База контактов синхронизируется инкрементально из SQLite/AD без дублирования в открытый текст.

---

## 3. Команды разработки и проверок

```bash
# Установка зависимостей
uv sync

# Векторизация базы знаний
uv run scripts/process_documents.py

# Запуск тестов
uv run pytest
```
