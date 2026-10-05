"""Checagem de links do relatório: garante que nenhum link foi inventado.

Resultados possíveis por URL:
  ok            - respondeu 2xx/3xx
  broken        - 404/410 (a página não existe)
  inconclusive  - o site bloqueia robôs (401/403/429/999) ou deu erro de servidor; abra manualmente
  error         - falha de rede/DNS/timeout
"""
from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any, Callable

from .model import FIELD_KEYS, URL_RE

USER_AGENT = "Mozilla/5.0 (compatible; teixugo-minerador/0.2; +https://github.com/gabriel-leao-git/teixugo-minerador)"
BLOCKED = {401, 403, 429, 999}


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


def _default_open(req: urllib.request.Request, timeout: float) -> int:
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (esquema validado por URL_RE)
        return resp.status


def check_url(url: str, timeout: float = 10.0, opener: Callable[..., int] | None = None) -> dict[str, Any]:
    open_ = opener or _default_open
    last_exc: str = ""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            status = open_(req, timeout)
            return {"url": url, "status": status, "result": "ok", "detail": method}
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return {"url": url, "status": e.code, "result": "broken", "detail": method}
            if e.code in BLOCKED or e.code >= 500:
                return {"url": url, "status": e.code, "result": "inconclusive", "detail": method}
            last_exc = f"HTTP {e.code}"  # 405 etc.: tenta GET
        except Exception as e:  # rede, DNS, timeout, SSL
            last_exc = f"{type(e).__name__}: {e}"
            break
    return {"url": url, "status": None, "result": "error", "detail": last_exc}


def check_all(urls: list[str], timeout: float = 10.0, opener: Callable[..., int] | None = None) -> list[dict[str, Any]]:
    return [check_url(u, timeout, opener) for u in urls]
