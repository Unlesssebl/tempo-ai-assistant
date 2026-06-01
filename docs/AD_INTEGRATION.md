# Интеграция с Active Directory

---

## Текущий статус

| Функция | Статус |
|---------|--------|
| `os.getlogin()` — логин пользователя Windows | ✅ Реализовано |
| Ручной ввод имени в настройках Desktop | ✅ Реализовано |
| Полное имя через Windows API (ctypes) | ✅ Реализовано |
| `UserProfileProvider` — базовый профиль из ОС | ✅ Реализовано |
| Базовая интеграция AD (ldap3) | 🔵 Планируется |
| RBAC по группам AD | 🔴 Планируется |
| SSO (Kerberos) | 🔴 Планируется |

---

## Текущая реализация: `UserProfileProvider`

Класс `src/core/user_profile.py` собирает базовый профиль пользователя из операционной системы без обращения к AD:

```python
from src.core.user_profile import UserProfileProvider

profile = UserProfileProvider.get_combined_profile()
# {
#   "pc_name": "WORKSTATION-001",
#   "login": "a.turkaev",
#   "last_name": "",       # Пусто до интеграции с AD
#   "first_name": "",
#   "department": "TEMPO", # Из USERDOMAIN
#   "position": "",
#   "email": ""
# }
```

`user_login` и `user_name` из профиля передаются в `AssistantService` для персонализации ответов и создания заявок в Helpdesk.

---

## Фаза 1: Базовая интеграция

### Атрибуты из AD

| Атрибут AD | Поле | Пример |
|-----------|------|--------|
| `displayName` | ФИО | Туркаев Ален |
| `title` | Должность | Инженер тех. поддержки |
| `department` | Отдел | Департамент ИТ |
| `mail` | Email | a.turkaev@tempo.ru |
| `manager` | Руководитель | CN=Иванов Петр,... |
| `memberOf` | Группы | IT_Department, All_Users |

### Пример реализации (ldap3)

```python
from ldap3 import Server, Connection, ALL

def get_user_from_ad(username: str, ad_server: str, ad_user: str, ad_password: str):
    server = Server(ad_server, get_info=ALL)
    conn = Connection(server, ad_user, ad_password, auto_bind=True)

    conn.search(
        'dc=tempo,dc=local',
        f'(sAMAccountName={username})',
        attributes=['displayName', 'title', 'department', 'mail', 'manager', 'memberOf']
    )

    if conn.entries:
        entry = conn.entries[0]
        return {
            "name": str(entry.displayName),
            "title": str(entry.title),
            "department": str(entry.department),
            "email": str(entry.mail),
            "groups": [str(g) for g in entry.memberOf]
        }
    return None
```

**Библиотеки:** `ldap3` (чистый Python, предпочтительно) или `python-ldap` (быстрее, требует C).

---

## Фаза 2: RBAC — Разграничение доступа

Документы в Qdrant помечаются метаданными `access_groups`. При поиске применяется фильтр по группам пользователя:

```python
results = search(
    query,
    filter={"access_groups": {"$in": user.groups}}
)
```

---

## Фаза 3: SSO (Single Sign-On)

Windows Integrated Authentication: клиент автоматически получает Kerberos-токен, сервер валидирует его через AD без ввода пароля.

**Библиотеки:** `pywin32` (Windows), `gssapi` (Kerberos cross-platform).

> Частичная Kerberos-поддержка уже реализована в `ticketing.py` для интеграции с IntraService (NTLM/Negotiate). См. `docs/INTRASERVICE.md`.

---

## Фаза 4: Org Chart Awareness

Использование атрибутов AD для ответов на вопросы об оргструктуре:
- «Кто мой руководитель?» → поле `manager`
- «Кто в моём отделе?» → фильтр по `department`
- «К кому обратиться по вопросу X?» → маршрутизация по отделам

---

## Фаза 5: Интеграция корпоративных систем

| Система | Протокол | Возможности |
|---------|----------|-------------|
| 1C | REST/OData | Остаток отпуска, зарплата |
| Jira | REST | Мои задачи, статусы |
| Outlook | MS Graph | Календарь, письма |
| Bitrix24 | REST | Сотрудники, задачи |
