"""Leitura de UMA página para verificar fatos (título, descrição, avaliação, preço), sem navegador.

Regras de conduta (não são opcionais):
  * Respeita o robots.txt. Se o site proíbe este programa OU agentes de IA conhecidos
    (Claude-User, ClaudeBot, anthropic-ai), a leitura é recusada: não há opção para contornar.
  * Uma página por chamada, sem paralelismo, sem login, sem tentar burlar bloqueios (403/429/captcha).
  * Identifica-se com um User-Agent próprio.

Páginas que montam o conteúdo por JavaScript (TikTok, Instagram etc.) voltam sem métricas:
nesses casos use outra fonte (API oficial, navegador, dados enviados pelo usuário).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

USER_AGENT = "teixugo-minerador/0.3 (+https://github.com/gabriel-leao-git/teixugo-minerador)"
OWN_TOKEN = "teixugo-minerador"
AI_AGENT_TOKENS = ("Claude-User", "ClaudeBot", "anthropic-ai")
MAX_BYTES = 1_500_000


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.ld: list[str] = []
        self._in: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "title" and not self.title:
            self._in, self._buf = "title", []
        elif tag == "h1" and not self.h1:
            self._in, self._buf = "h1", []
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key and a.get("content") and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "link" and a.get("rel", "").lower() == "canonical":
            self.canonical = a.get("href", "")
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in, self._buf = "ld", []

    def handle_data(self, data: str) -> None:
        if self._in:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._in == "title" and tag == "title":
            self.title = " ".join("".join(self._buf).split())
            self._in = None
        elif self._in == "h1" and tag == "h1":
            self.h1 = " ".join("".join(self._buf).split())
            self._in = None
        elif self._in == "ld" and tag == "script":
            self.ld.append("".join(self._buf))
            self._in = None


def _walk(node: Any) -> list[dict[str, Any]]:
    """Todos os objetos de um JSON-LD, inclusive dentro de @graph e listas."""
    out: list[dict[str, Any]] = []
    if isinstance(node, list):
        for x in node:
            out += _walk(x)
    elif isinstance(node, dict):
        out.append(node)
        for v in node.values():
            if isinstance(v, (list, dict)):
                out += _walk(v)
    return out


def extract_product(ld_blocks: list[str]) -> dict[str, Any] | None:
    """Procura um objeto schema.org Product e devolve nome, marca, preço, moeda e avaliação."""
    for raw in ld_blocks:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for obj in _walk(data):
            t = obj.get("@type")
            types = t if isinstance(t, list) else [t]
            if "Product" not in types:
                continue
            offers = obj.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            offers = offers if isinstance(offers, dict) else {}
            rating = obj.get("aggregateRating") if isinstance(obj.get("aggregateRating"), dict) else {}
            brand = obj.get("brand")
            return {
                "name": obj.get("name"),
                "brand": brand.get("name") if isinstance(brand, dict) else brand,
                "price": offers.get("price") or offers.get("lowPrice"),
                "currency": offers.get("priceCurrency"),
                "rating": rating.get("ratingValue"),
                "reviews": rating.get("reviewCount") or rating.get("ratingCount"),
            }
    return None


def _default_open(req: urllib.request.Request, timeout: float) -> Any:
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 (esquema validado em fetch)


def _read_text(resp: Any, limit: int) -> str:
    raw = resp.read(limit)
    charset = None
    try:
        charset = resp.headers.get_content_charset()
    except Exception:
        pass
    return raw.decode(charset or "utf-8", errors="replace")


def robots_check(url: str, opener: Callable[..., Any], timeout: float) -> tuple[str, str]:
    """('allowed'|'blocked'|'unknown', detalhe). Recusa se o site proíbe este programa ou agentes de IA."""
    p = urlparse(url)
    req = urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt", headers={"User-Agent": USER_AGENT})
    try:
        resp = opener(req, timeout)
        text = _read_text(resp, 500_000)
    except urllib.error.HTTPError as e:
        if 400 <= e.code < 500:
            return "allowed", "sem robots.txt"
        return "unknown", f"robots.txt respondeu HTTP {e.code}"
    except Exception as e:
        return "unknown", f"não foi possível ler o robots.txt ({type(e).__name__})"
    rp = RobotFileParser()
    rp.parse(text.splitlines())
    for agent in (OWN_TOKEN,) + AI_AGENT_TOKENS:
        if not rp.can_fetch(agent, url):
            return "blocked", f"o robots.txt do site proíbe '{agent}' neste caminho"
    return "allowed", ""


def fetch(url: str, timeout: float = 15.0, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    open_ = opener or _default_open
    result: dict[str, Any] = {
        "url": url, "final_url": None, "status": None, "robots": None, "title": None, "description": None,
        "h1": None, "canonical": None, "og": {}, "product": None, "error": None,
    }
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        result["error"] = "use uma URL http(s) completa"
        return result

    state, detail = robots_check(url, open_, timeout)
    result["robots"] = state
    if state == "blocked":
        result["error"] = f"{detail}. Leitura recusada: abra a página manualmente ou use outra fonte."
        return result

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    try:
        resp = open_(req, timeout)
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP {e.code}" + (" (o site bloqueia leitura automática; não contorne)" if e.code in (401, 403, 429, 503) else "")
        return result
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        return result

    result["status"] = getattr(resp, "status", 200)
    try:
        result["final_url"] = resp.geturl()
    except Exception:
        result["final_url"] = url
    page = _Page()
    try:
        page.feed(_read_text(resp, MAX_BYTES))
    except Exception as e:  # HTML malformado demais
        result["error"] = f"HTML ilegível: {e}"
        return result
    og = {k[3:]: v for k, v in page.meta.items() if k.startswith("og:")}
    result.update(
        title=page.title or og.get("title"),
        description=page.meta.get("description") or og.get("description"),
        h1=page.h1 or None,
        canonical=page.canonical or None,
        og=og,
        product=extract_product(page.ld),
    )
    if not (result["title"] or result["product"]):
        result["error"] = "página sem conteúdo legível (provavelmente montada por JavaScript): use outra fonte"
    return result
