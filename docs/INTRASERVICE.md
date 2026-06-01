# IntraService API

Интеграция с корпоративным Helpdesk. Реализация — `src/services/ticketing.py`.

---

## Endpoints

| Действие | Endpoint | Метод |
|----------|----------|-------|
| Создать заявку | `/api/task` | POST |
| Список заявок | `/api/task` | GET |
| Конкретная заявка | `/api/task/{id}` | GET |
| Изменить заявку | `/api/task/{id}` | PUT |
| Шаблон новой заявки | `/api/newtask?serviceid={sid}&tasktypeid={tid}` | GET |
| Права по заявке | `/api/task/{id}/usertaskrights` | GET |
| Статусы | `/api/taskstatus` | GET |
| Приоритеты | `/api/taskpriority` | GET |
| Типы заявок | `/api/tasktype?serviceid={sid}` | GET |
| Сервисы | `/api/service?for=createtask` | GET |
| Пользователи | `/api/user?login={login}` | GET |
| Загрузка файла | `/api/TaskFile` | POST |

---

## Создание заявки

### Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `Name` | String | Название заявки |
| `ServiceId` | int | Идентификатор сервиса |
| `StatusId` | int | Начальный статус (см. `/api/taskstatus?IsInitial=true`) |
| `PriorityId` | int | Идентификатор приоритета |
| `TypeId` | int | Тип заявки |

### Дополнительные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `Description` | String | Текст заявки |
| `CreatorId` | int | Заявитель (требует право `ChangeCreator`) |
| `ExecutorIds` | String | ID исполнителей через запятую |
| `FileTokens` | String | Токены прикреплённых файлов |
| `Deadline` | DateTime | Срок выполнения |
| `CategoryIds` | String | ID категорий через запятую |
| `IsMassIncident` | bool | Массовый инцидент |

### Пример запроса

```http
POST /api/task
Authorization: Basic <base64(login:password)>
Content-Type: application/json

{
  "Name": "[AI Assistant] Не работает принтер",
  "ServiceId": 11,
  "StatusId": 31,
  "PriorityId": 9,
  "TypeId": 1,
  "Description": "Пользователь: {user_name} ({user_login})\n\n{query}"
}
```

### Рекомендуемый workflow

1. Получить шаблон: `GET /api/newtask?serviceid=11&tasktypeid=1` → взять дефолтные ID
2. Заполнить обязательные поля (можно переопределить из `.env`)
3. Создать заявку: `POST /api/task`

---

## Создание от имени пользователя

### Вариант A: Из описания (рекомендуется, `TICKET_CREATE_ON_BEHALF=0`)

Заявка создаётся от сервисной учётки, пользователь указывается в `Description`:
```
Пользователь: {user_name}
Логин: {user_login}
```

### Вариант B: Через `CreatorId`

```json
{ "CreatorId": 1234 }
```

Требует право `ChangeCreator` у сервисной учётки. Пользователь должен существовать в IntraService.

### Вариант C: Через `UserEmail` (авто-создание пользователя)

```json
{
  "UserEmail": "user@company.com",
  "UserPassword": "temp123",
  "UserConfirmPassword": "temp123",
  "UserName": "User Name",
  "UserCompanyId": 1924,
  "UserRoleId": 55
}
```

Если пользователь с таким email существует — заявка создаётся от него. Иначе — создаётся новый пользователь.

---

## Прикрепление файлов

### Шаг 1: Загрузить файл

```http
POST /api/TaskFile
Content-Type: multipart/form-data
Authorization: Basic <base64(login:password)>

file0: <binary>
file0Name: screenshot
```

**Ответ:** `{"FileTokens": "abc-123-def"}`

### Шаг 2: Передать токен при создании заявки

```json
{ "FileTokens": "abc-123-def" }
```

---

## Авторизация

Режим задаётся в `.env` через `HELPDESK_AUTH_MODE`:

| Режим | Описание |
|-------|----------|
| `negotiate` | Kerberos → NTLM fallback (рекомендуется для production) |
| `kerberos` | Только Kerberos |
| `ntlm` | Только NTLM |
| `basic` | Basic Auth (для отладки) |

### Права сервисной учётки

| Право | Требование |
|-------|-----------|
| `CreateTask` | ✅ Обязательно |
| `ViewTask` | ✅ Обязательно |
| `ChangeCreator` | ⚠️ Для создания от имени другого пользователя |
| `EditTask` | ⚠️ Для редактирования заявок |

### Проверка прав

```http
GET /api/task/{id}/usertaskrights
```

---

## Конфигурация `.env`

```env
# Подключение
INTRASERVICE_BASE_URL=https://servicedesk.corporate.loc
HELPDESK_AUTH_MODE=negotiate          # negotiate | ntlm | basic

# Basic Auth (только для HELPDESK_AUTH_MODE=basic или fallback)
INTRASERVICE_LOGIN=IntraTest
INTRASERVICE_PASSWORD=***

# Fallback на Basic при неудаче Negotiate
HELPDESK_ALLOW_BASIC_FALLBACK=0

# Требовать delegation перед созданием заявки (0 — не требовать)
HELPDESK_REQUIRE_DELEGATION=1

# Источник идентичности пользователя: login | upn | email
HELPDESK_IDENTITY_SOURCE=login

# Фиксированные ID значений по умолчанию
INTRASERVICE_DEFAULT_SERVICE_ID=11
INTRASERVICE_DEFAULT_TYPE_ID=1
INTRASERVICE_INITIAL_STATUS_ID=31
INTRASERVICE_MEDIUM_PRIORITY_ID=9

# Создавать от имени пользователя (1) или от сервисной учётки (0)
TICKET_CREATE_ON_BEHALF=0

# SSL: путь к сертификату, true (стандартный) или false (отключить)
INTRASERVICE_SSL_VERIFY=cert/ServiceDesk.corporate.loc.crt
```

---

## Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `400: Статус не существует` | Неверный `StatusId` | `GET /api/taskstatus?IsInitial=true` |
| `400: Приоритет не существует` | Неверный `PriorityId` | `GET /api/taskpriority` |
| `401 Unauthorized` | Неверный логин/пароль | Проверить credentials в `.env` |
| `403 Forbidden` | Нет прав | Выдать права `CreateTask`/`ViewTask` |
| Connection reset | SSL/Network | Проверить сеть и `INTRASERVICE_SSL_VERIFY` |
