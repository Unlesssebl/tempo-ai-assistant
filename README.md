# TEMPO AI Assistant

Корпоративный AI-ассистент на базе RAG (Retrieval-Augmented Generation). Отвечает на вопросы сотрудников по внутренней документации текстом и голосом, интегрируется с Helpdesk (IntraService).

## Быстрый старт

### 1. Установка зависимостей

```bash
# Рекомендуется: uv (быстрее, используется в проекте)
uv sync

### 2. Конфигурация

```bash
cp env.example .env
# Заполните TELEGRAM_TOKEN и GEMINI_API_KEY_1 в .env
# Модели и параметры RAG настраиваются в models_config.yaml
```

**Режим отладки (Debug-логирование):**
По умолчанию детальные логи ротации ключей и моделей скрыты (установлен уровень `INFO`). Для включения подробного отладочного вывода добавьте в `.env` или укажите в терминале при запуске:
```bash
LOG_LEVEL=DEBUG
```

### 3. Подготовка базы знаний

Положите документы в папку `data/`, затем:

```bash
# Полный цикл: чанкинг + векторизация (рекомендуется)
uv run scripts/process_documents.py

# Инициализация базы (без кэша, первый запуск)
uv run scripts/init_database.py
```

### 4. Запуск

```bash
# Telegram-бот (только TG)
uv run run_bot.py
# или
uv run run_tg_bot.py

# MAX-бот (только MAX мессенджер)
uv run run_max_bot.py

# Оба бота (Telegram + MAX) одновременно в одном event loop
uv run run_all_bots.py

# HTTP API сервер
python run_server.py

# Сервер + Telegram бот одновременно
uv run run_server.py --with-bot

# Desktop-клиент (требует запущенный сервер)
python run_client.py
```