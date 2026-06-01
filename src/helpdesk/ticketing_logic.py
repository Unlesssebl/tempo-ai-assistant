"""
Слой Логики: Бизнес-правила для работы с тикетами.
"""

import re
from typing import Any, Dict, List, Optional


def should_offer_ticket(answer: str) -> bool:
    negative_markers = ["не нашел", "не удалось", "не могу", "ошибка", "сбой", "проблем"]
    a = (answer or "").lower()
    return any(marker in a for marker in negative_markers)


def compose_description(user_login: str, summary: str) -> str:
    return f"Информация о заявителе: - {user_login or 'Не указан'}\n\n{summary.strip()}"


def build_ticket_name(query: str, max_len: int = 120) -> str:
    clean = re.sub(r"\s+", " ", (query or "").strip())
    if len(clean) <= max_len:
        return clean or "Обращение пользователя"
    return f"{clean[: max_len - 3]}..."


def auto_summary(text: str, max_len: int = 300) -> str:
    clean = re.sub(r"\s+", " ", (text or "").strip())
    if len(clean) <= max_len:
        return clean
    return f"{clean[: max_len - 3]}..."


def choose_service_by_overlap(query: str, services: List[Dict[str, Any]]) -> tuple[int, float]:
    if not services:
        raise RuntimeError("No services available")
    q_tokens = set(re.findall(r"[a-zA-Zа-яА-Я0-9]+", query.lower()))
    if not q_tokens:
        return int(services[0].get("Id")), 0.0

    best_id, best_score = int(services[0].get("Id")), 0.0
    for svc in services:
        sid = svc.get("Id")
        if sid is None:
            continue
        raw = f"{svc.get('Name', '')} {svc.get('Code', '')}".lower()
        s_tokens = set(re.findall(r"[a-zA-Zа-яА-Я0-9]+", raw))
        if not s_tokens:
            continue
        score = len(q_tokens.intersection(s_tokens)) / max(1, len(s_tokens))
        if score > best_score:
            best_score, best_id = score, int(sid)
    return best_id, best_score


def map_error_code(message: str, delegation_status: str) -> str:
    msg = (message or "").lower()
    if is_transport_error(msg):
        return "intraservice_unavailable"
    if "предоставленный функции токен неправилен" in msg or "initializesecuritycontext" in msg:
        return "intraservice_auth_failed"
    if delegation_status == "failed" or "delegation" in msg:
        return "delegation_failed"
    if "not found in intraservice users" in msg:
        return "identity_not_found"
    if any(m in msg for m in ["401", "unauthorized", "forbidden"]):
        return "intraservice_auth_failed"
    if "403" in msg:
        return "intraservice_forbidden"
    if any(m in msg for m in ["error 5", "timeout", "unavailable"]):
        return "intraservice_unavailable"
    return "intraservice_auth_failed"


def is_transport_error(message: str) -> bool:
    msg = (message or "").lower()
    markers = [
        "remote end closed",
        "connection aborted",
        "remotedisconnected",
        "protocolerror",
        "max retries",
        "failed to establish",
        "not known",
        "name resolution",
        "reset by peer",
        "refused",
        "timeout",
    ]
    return any(m in msg for m in markers)


def normalize_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("Items", "items", "Data", "data", "Result", "result"):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


def safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
