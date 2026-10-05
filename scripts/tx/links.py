"""Checagem de links do relatório: garante que nenhum link foi inventado.

Resultados possíveis por URL:
  ok            - respondeu 2xx/3xx
  broken        - 404/410 (a página não existe)
  inconclusive  - o site bloqueia robôs (401/403/429/999), o robots.txt proíbe, ou deu erro de servidor; abra manualmente
  error         - falha de rede/DNS/timeout ou endereço recusado pela proteção de rede (netguard)

Cada redirecionamento é conferido de novo (rede interna e robots.txt). Na rede real, o robots.txt é
respeitado como em `fetch`; quando se injeta um `opener` (testes), a conferência do robots.txt é opcional.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from . import netguard, webfetch
from .model import FIELD_KEYS, URL_RE

USER_AGENT = webfetch.USER_AGENT
BLOCKED = {401, 403, 429, 999}
REDIRECT_CODES = webfetch.REDIRECT_CODES
MAX_REDIRECTS = webfetch.MAX_REDIRECTS


def collect_urls(report: dict[str, Any]) -> list[str]:
    """URLs em `value` e `source` de todos os campos de evidência (sem duplicatas, em ordem)."""
    urls: list[str] = []

    def add(x: Any) -> None:
        values = x if isinstance(x, list) else [x]
        for v in values:
            if isinstance(v, str) and URL_RE.match(v.strip()) and v.strip() not in urls:
                urls.append(v.strip())

    for p in report.get("products", []):
        for key in FIELD_KEYS:
            f = p.get(key)
            if isinstance(f, dict):
                add(f.get("value"))
                add(f.get("source"))
    for s in report.get("sources", []) or []:
        if isinstance(s, dict):
            add(s.get("url"))
    return urls


def _default_status(req: urllib.request.Request, timeout: float) -> int:
    with webfetch._default_open(req, timeout) as resp:  # noqa: S310 (esquema e rede validados por netguard)
        return resp.status


def check_url(
    url: str,
    timeout: float = 10.0,
    opener: Callable[..., int] | None = None,
    resolver: Callable[..., Any] | None = None,
    check_robots: bool | None = None,
) -> dict[str, Any]:
    status_of = opener or _default_status
    robots_on = (opener is None) if check_robots is None else check_robots
    current = url
    last_exc = ""
    for hop in range(MAX_REDIRECTS + 1):
        ok, why = netguard.check_url(current, resolver)
        if not ok:
            return {"url": url, "status": None, "result": "error", "detail": f"endereço recusado: {why}"}
        if robots_on:
            state, detail = webfetch.robots_check(current, webfetch._default_open, timeout)
            if state == "blocked":
                return {"url": url, "status": None, "result": "inconclusive", "detail": f"{detail}; abra manualmente"}
        redirected = False
        for method in ("HEAD", "GET"):
            req = urllib.request.Request(current, method=method, headers={"User-Agent": USER_AGENT})
            try:
                status = status_of(req, timeout)
                return {"url": url, "status": status, "result": "ok", "detail": method}
            except urllib.error.HTTPError as e:
                location = e.headers.get("Location") if e.headers else None
                if e.code in REDIRECT_CODES and location:
                    current = urljoin(current, location)
                    redirected = True
                    break
                if e.code in (404, 410):
                    return {"url": url, "status": e.code, "result": "broken", "detail": method}
                if e.code in BLOCKED or e.code >= 500:
                    return {"url": url, "status": e.code, "result": "inconclusive", "detail": method}
                last_exc = f"HTTP {e.code}"  # 405 etc.: tenta GET
            except Exception as e:  # rede, DNS, timeout, SSL
                return {"url": url, "status": None, "result": "error", "detail": f"{type(e).__name__}: {e}"}
        if not redirected:
            break
    else:
        return {"url": url, "status": None, "result": "error", "detail": f"redirecionamentos demais (mais de {MAX_REDIRECTS})"}
    return {"url": url, "status": None, "result": "error", "detail": last_exc}


def check_all(urls: list[str], timeout: float = 10.0, opener: Callable[..., int] | None = None) -> list[dict[str, Any]]:
    return [check_url(u, timeout, opener) for u in urls]
