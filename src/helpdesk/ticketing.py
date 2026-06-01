from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import src.helpdesk.ticketing_logic as logic
from src.core.config import Config
from src.helpdesk.intraservice_client import IntraServiceAPIClient

logger = logging.getLogger(__name__)


@dataclass
class TicketCreationResult:
    ticket_created: bool
    ticket_number: Optional[str]
    ticket_creation_reason: str
    ticket_draft_saved: bool = False
    fallback_all_used: bool = False
    long_context_summary_used: bool = False
    created_via: str = "AI_ASSISTANT"
    trace_id: Optional[str] = None
    auth_scheme_used: str = "none"
    delegation_status: str = "not_attempted"
    error_code: Optional[str] = None


@dataclass
class TicketContext:
    query: str
    assistant_answer: str
    user_name: Optional[str] = None
    user_login: Optional[str] = None
    extra_info_1: Optional[str] = None
    extra_info_2: Optional[str] = None
    extra_fields: dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None


class TicketingService:
    """Слой Оркестрации: Координация процесса создания заявки."""

    def __init__(self, config: Config):
        self.config = config
        self.api = IntraServiceAPIClient(config)

    def is_enabled(self) -> bool:
        return self.api.is_enabled()

    async def create_ticket(self, ctx: TicketContext) -> TicketCreationResult:
        trace_id = uuid.uuid4().hex[:8]
        logger.info("[ticket:%s] create_ticket started user=%s", trace_id, ctx.user_login)

        if not self.is_enabled():
            return self._result_disabled(trace_id)

        try:
            # 1. Сбор базовых параметров
            initial_status = await self._resolve_status(trace_id)
            priority_id = await self._resolve_priority(trace_id)
            requester_id = await self._resolve_requester(ctx, trace_id)

            # 2. Определение сервиса и типа
            svc_data = await self._resolve_service_and_type_info(ctx, trace_id)
            service_id, type_id, fallback_all, long_summary, description = svc_data

            # 3. Формирование payload
            payload = self._build_payload(
                ctx, service_id, type_id, priority_id, initial_status, description, requester_id
            )

            # 4. Отправка запроса
            self.api.require_delegation_guard()
            response = await self.api.request("POST", "/api/task", payload=payload, trace_id=trace_id)

            # 5. Обработка результата
            task_id = self._extract_task_id(response)
            return TicketCreationResult(
                ticket_created=True,
                ticket_number=str(task_id),
                ticket_creation_reason="Заявка создана в helpdesk",
                fallback_all_used=fallback_all,
                long_context_summary_used=long_summary,
                trace_id=trace_id,
                auth_scheme_used=self.api.auth_scheme_used,
                delegation_status=self.api.delegation_status,
            )

        except Exception as exc:
            logger.exception("[ticket:%s] Ticket creation failed", trace_id)
            return self._result_error(trace_id, exc)

    async def _resolve_status(self, trace_id: str) -> Optional[int]:
        if self.config.intraservice_initial_status_id:
            return self.config.intraservice_initial_status_id
        try:
            data = await self.api.request("GET", "/api/taskstatus", trace_id=trace_id)
            for row in logic.normalize_list(data):
                if bool(row.get("IsInitial")):
                    return logic.safe_int(row.get("Id"))
        except Exception:
            pass
        return 1

    async def _resolve_priority(self, trace_id: str) -> int:
        if self.config.intraservice_medium_priority_id:
            return self.config.intraservice_medium_priority_id
        try:
            data = await self.api.request("GET", "/api/taskpriority", trace_id=trace_id)
            for row in logic.normalize_list(data):
                name = str(row.get("Name", "")).lower()
                if "medium" in name or "сред" in name:
                    return logic.safe_int(row.get("Id"))
        except Exception:
            pass
        return 9

    async def _resolve_requester(self, ctx: TicketContext, trace_id: str) -> Optional[int]:
        if not self.config.ticket_create_on_behalf or not ctx.user_login:
            return None
        data = await self.api.request("GET", "/api/user", params={"login": ctx.user_login}, trace_id=trace_id)
        users = logic.normalize_list(data)
        if not users:
            raise RuntimeError(f"User {ctx.user_login} not found")
        return logic.safe_int(users[0].get("Id"))

    async def _resolve_service_and_type_info(self, ctx: TicketContext, trace_id: str):
        summary = ctx.summary or logic.auto_summary(ctx.query)
        description = logic.compose_description(ctx.user_login, summary)
        long_summary = len(ctx.query) > self.config.ticket_long_context_chars

        # Динамическое разрешение, если ID не заданы в конфиге
        if not (self.config.intraservice_default_service_id and self.config.intraservice_default_type_id):
            try:
                data = await self.api.request("GET", "/api/service", params={"for": "createtask"}, trace_id=trace_id)
                services = logic.normalize_list(data)
                service_id, conf = logic.choose_service_by_overlap(ctx.query, services)
                if conf < self.config.ticket_confidence_threshold:
                    service_id = self.config.intraservice_default_service_id or 1

                type_id = self.config.intraservice_default_type_id or 1
                return service_id, type_id, False, long_summary, description
            except Exception:
                pass

        return (
            self.config.intraservice_default_service_id or 1,
            self.config.intraservice_default_type_id or 1,
            False,
            long_summary,
            description,
        )

    def _build_payload(self, ctx, svc_id, type_id, prio_id, status_id, desc, req_id):
        name = logic.build_ticket_name(ctx.query)
        if self.config.ticket_auto_mark_enabled:
            name = f"[AI Assistant] {name}"

        payload = {"Name": name, "ServiceId": svc_id, "TypeId": type_id, "PriorityId": prio_id, "Description": desc}
        if status_id:
            payload["StatusId"] = status_id
        if req_id:
            payload["UserId"] = payload["CreatorId"] = req_id
        if ctx.extra_fields:
            payload.update(ctx.extra_fields)

        # Хардкод категории для ТЭМПО (как в оригинале)
        if svc_id == 106 and not payload.get("CategoryIds"):
            payload["CategoryIds"] = "57"

        return payload

    def _extract_task_id(self, response: Any) -> int:
        if isinstance(response, dict):
            task_data = response.get("Task", response)
            tid = logic.safe_int(task_data.get("Id"))
            if tid:
                return tid
        raise RuntimeError("Response has no Task Id")

    def _result_disabled(self, trace_id: str) -> TicketCreationResult:
        return TicketCreationResult(
            ticket_created=False,
            ticket_number=None,
            ticket_creation_reason="IntraService integration is disabled",
            ticket_draft_saved=True,
            trace_id=trace_id,
            error_code="intraservice_auth_failed",
        )

    def _result_error(self, trace_id: str, exc: Exception) -> TicketCreationResult:
        err_code = logic.map_error_code(str(exc), self.api.delegation_status)
        return TicketCreationResult(
            ticket_created=False,
            ticket_number=None,
            ticket_creation_reason=f"Ошибка: {str(exc)[:100]}...",
            ticket_draft_saved=True,
            trace_id=trace_id,
            auth_scheme_used=self.api.auth_scheme_used,
            delegation_status=self.api.delegation_status,
            error_code=err_code,
        )
