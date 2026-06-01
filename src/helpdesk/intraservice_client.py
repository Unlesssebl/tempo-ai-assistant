"""
Слой I/O: Клиент для работы с IntraService API.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from src.core.config import Config

logger = logging.getLogger(__name__)


@dataclass
class IntraServiceResponse:
    status_code: int
    body: str
    headers: dict[str, str]


class IntraServiceAPIClient:
    """HTTP клиент для IntraService с поддержкой NTLM/Kerberos и Basic Auth."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = (config.intraservice_base_url or "").rstrip("/")
        self._auth_scheme_used = "none"
        self._delegation_status = "not_attempted"

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    @property
    def auth_scheme_used(self) -> str:
        return self._auth_scheme_used

    @property
    def delegation_status(self) -> str:
        return self._delegation_status

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Any:
        trace = trace_id or "-"
        mode = self._normalize_auth_mode(self.config.helpdesk_auth_mode)

        try:
            if mode in ("negotiate", "kerberos", "ntlm"):
                response = await self._run_in_thread(
                    self._request_negotiate_sync,
                    method,
                    path,
                    params,
                    payload,
                    trace,
                )
            elif mode == "basic":
                response = await self._request_basic(method, path, params, payload, trace)
            else:
                raise RuntimeError(f"Unsupported HELPDESK_AUTH_MODE: {mode}")
        except Exception as exc:
            self._update_delegation_on_error(exc, mode)

            if mode in ("negotiate", "kerberos", "ntlm") and self.config.helpdesk_allow_basic_fallback:
                if self.config.intraservice_login and self.config.intraservice_password:
                    logger.warning("[ticket:%s] falling back to basic auth", trace)
                    response = await self._request_basic(method, path, params, payload, trace)
                else:
                    raise
            else:
                raise

            if response is None:
                raise RuntimeError("No response from IntraService after fallback") from exc

        if response.status_code >= 400:
            err_msg = self._extract_error(response.body)
            raise RuntimeError(f"IntraService error {response.status_code}: {err_msg}")

        if not response.body:
            return None

        try:
            return json.loads(response.body)
        except Exception:
            return response.body

    def require_delegation_guard(self):
        if not self.config.helpdesk_require_delegation:
            return
        if self._delegation_status != "success":
            raise RuntimeError("Delegation required but was not successful")
        if self._auth_scheme_used == "basic":
            raise RuntimeError("Delegation required but basic fallback was used")

    async def _request_basic(self, method: str, path: str, params, payload, trace_id) -> IntraServiceResponse:
        raw = f"{self.config.intraservice_login}:{self.config.intraservice_password}".encode("utf-8")
        token = base64.b64encode(raw).decode("ascii")
        headers = {"Authorization": f"Basic {token}"}

        verify = self.config.intraservice_ssl_verify
        if verify is None and self.config.intraservice_ssl_cert_path:
            verify = self.config.intraservice_ssl_cert_path
        ssl_verify = verify if verify is not None else True

        async with httpx.AsyncClient(timeout=20.0, verify=ssl_verify, follow_redirects=True) as client:
            response = await client.request(
                method, f"{self.base_url}{path}", params=params, json=payload, headers=headers
            )

        self._auth_scheme_used = "basic"
        self._delegation_status = "not_attempted"
        return IntraServiceResponse(
            status_code=response.status_code,
            body=response.text or "",
            headers={k.lower(): v for k, v in response.headers.items()},
        )

    def _request_negotiate_sync(self, method, path, params, payload, trace_id) -> IntraServiceResponse:
        import requests
        from requests_negotiate_sspi import HttpNegotiateAuth

        parsed = urlparse(self.base_url)
        spn_raw = (self.config.helpdesk_spn or "").strip()
        spn_service, spn_host = "HTTP", parsed.hostname
        if "/" in spn_raw:
            s, h = spn_raw.split("/", 1)
            if s.strip():
                spn_service = s.strip()
            if h.strip():
                spn_host = h.strip()

        delegate = bool(self.config.helpdesk_require_delegation)
        auth = HttpNegotiateAuth(service=spn_service, host=spn_host, delegate=delegate)

        verify = self.config.intraservice_ssl_verify
        if verify is None and self.config.intraservice_ssl_cert_path:
            verify = self.config.intraservice_ssl_cert_path

        session = requests.Session()
        session.verify = verify if verify is not None else True
        session.headers.update({"Connection": "close", "Cache-Control": "no-cache"})

        response = session.request(
            method=method,
            url=f"{self.base_url}{path}",
            params=params,
            json=payload,
            auth=auth,
            timeout=30,
            allow_redirects=True,
        )

        headers = {k.lower(): v for k, v in response.headers.items()}
        scheme = self._infer_negotiate_scheme(headers)

        self._auth_scheme_used = scheme
        if delegate:
            self._delegation_status = "success" if response.status_code < 400 else "failed"

        return IntraServiceResponse(status_code=response.status_code, body=response.text or "", headers=headers)

    async def _run_in_thread(self, fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    def _normalize_auth_mode(self, mode: str) -> str:
        value = (mode or "").strip().lower()
        return value if value in {"kerberos", "ntlm", "basic", "negotiate"} else "negotiate"

    def _infer_negotiate_scheme(self, headers: dict[str, str]) -> str:
        if self.config.helpdesk_negotiate_force_kerberos:
            return "kerberos"
        challenge = headers.get("www-authenticate", "").lower()
        return "ntlm" if "ntlm" in challenge and "kerberos" not in challenge else "kerberos"

    def _update_delegation_on_error(self, exc: Exception, mode: str):
        if mode in ("negotiate", "kerberos", "ntlm"):
            from src.helpdesk.ticketing_logic import is_transport_error

            if is_transport_error(str(exc)):
                if self._delegation_status != "success":
                    self._delegation_status = "unknown"
            else:
                self._delegation_status = "failed"

    def _extract_error(self, body: str) -> str:
        try:
            data = json.loads(body)
            return data.get("Message", body)
        except Exception:
            return body
