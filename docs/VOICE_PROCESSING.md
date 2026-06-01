# Голосовая обработка

Голосовые запросы обрабатываются через `src/services/assistant.py → process_voice_query` с использованием Gemini Live API (Native Audio). Реализация WebSocket-логики — `src/llm/audio.py`.

---

## Режимы работы

### Legacy Mode (`enable_tools=False`)

Два последовательных WebSocket-соединения:
1. Транскрипция аудио → текст запроса
2. RAG-поиск по транскрипции
3. Генерация ответа с найденным контекстом

**Плюсы:** стабильный, предсказуемый.  
**Минусы:** выше латентность (~2× по числу handshake).

### Function Calling Mode (`enable_tools=True`, по умолчанию)

Одно WebSocket-соединение:
1. Модель получает аудио
2. Сама решает вызвать `search_knowledge_base(query)`
3. Система выполняет RAG-поиск (с де-контекстуализацией через историю)
4. Модель генерирует аудио-ответ с контекстом

**Плюсы:** ниже латентность, гибкое управление контекстом.  
**Минусы:** модель может не вызвать функцию (простые приветствия), возможны timeout'ы.

> **Рекомендация:** Function Calling Mode — по умолчанию в `models_config.yaml`. Legacy Mode — для диагностики или нестабильного окружения.

---

## Настройка

Параметры голосовой модели задаются в **`models_config.yaml`** (секция `audio_model`) и могут быть переопределены через `.env`. Соответствующий датакласс — `AudioModelConfig` в `src/core/models_loader.py`.

### Ключевые параметры `models_config.yaml`

```yaml
audio_model:
  api_version: "v1alpha"
  generation:
    thinking_budget: 8192       # Thinking-бюджет модели
  voice:
    name: "Kore"                # Голос TTS
  features:
    enable_tools: true          # Function Calling Mode (false = Legacy)
    enable_affective_dialog: false  # Адаптация к тону и эмоциям
    enable_output_transcription: true  # Логирование транскрипции ответа
    vad_disabled: true          # Отключить серверный VAD
  limits:
    response_timeout: 300.0     # Таймаут ответа (сек)
    transcription_timeout: 60.0 # Таймаут транскрипции (сек)
    max_voice_context_chars: 50000
```

### Переопределение через `.env`

```env
GEMINI_AUDIO_MODEL=gemini-2.5-flash-native-audio-latest
LIVE_API_VERSION=v1alpha        # Обязательно для Affective Dialog
AUDIO_VOICE_NAME=Kore
AUDIO_TEMPERATURE=1.0
```

### Программное переключение режима

```python
# Через models_config.yaml → features.enable_tools: false
# Или программно при создании AudioModelConfig:
from src.core.models_loader import AudioModelConfig

config = AudioModelConfig(enable_tools=False)  # Legacy Mode
```

---

## История чата в голосовых запросах

`process_voice_query` поддерживает `session_id`. При его наличии:
- Загружается резюме и последние 5 сообщений из `ChatHistoryManager`
- История передаётся в `system_prompt` голосовой модели
- Пользовательский и ассистентский тексты сохраняются после ответа (из транскрипции)

---

## Активные возможности

- **Thinking** — `thinking_budget: 8192` для лучшего качества ответов
- **Транскрипция** — `enable_output_transcription: true` для логирования
- **Обрезка по чанкам** — контекст обрезается по целым чанкам, не посередине (`max_voice_context_chars`)
- **De-contextualization** — запрос переформулируется с учётом истории перед RAG-поиском
- **Affective Dialog** — `enable_affective_dialog: true`, требует `LIVE_API_VERSION=v1alpha`

---

## Диагностика

Ключевые записи в логах:

| Запись | Значение |
|--------|---------|
| `Input transcript:` | Что услышала модель |
| `Model requested tool call:` | Вызвала ли модель `search_knowledge_base` |
| `Output transcript:` | Что ответила модель |
| `Using Function Calling approach` | Активен Function Calling Mode |
| `Using legacy two-connection approach` | Активен Legacy Mode |
| `API response timeout` | Модель зависла (timeout из конфига) |

### Fallback при проблемах

В `models_config.yaml`:
```yaml
audio_model:
  features:
    enable_tools: false  # Вернуться к Legacy Mode
```

После изменения — перезапустить процесс. Горячая перезагрузка: `POST /api/reload`.
