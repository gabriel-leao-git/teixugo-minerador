"""Matriz de buscas: gera, de forma repetível, as consultas a fazer em cada plataforma.

Cada linha traz duas formas de buscar o mesmo assunto:
  * `web_search`: texto pronto para a ferramenta de busca na web (usa `site:` para mirar a plataforma);
  * `url`: link de busca nativo da plataforma, para abrir no navegador (vazio quando não existe um público).

Os formatos de URL podem mudar; se um deles falhar, o texto da consulta continua válido.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from .model import scope_of, slugify

# Sufixos que ajudam a achar produto, prova de efetividade e reclamações (para medir efetividade).
MODIFIERS: dict[str, list[str]] = {
    "pt-BR": ["", "funciona mesmo", "antes e depois", "review", "vale a pena", "reclamação", "produto"],
    "en": ["", "does it work", "before and after", "review", "worth it", "complaints", "product"],
    "es": ["", "funciona", "antes y después", "reseña", "vale la pena", "opiniones", "producto"],
}

# plataforma -> (modelo de URL nativa, domínio para `site:`). {q} = consulta codificada; {geo} = país; {slug} = kebab-case.
PLATFORMS: dict[str, tuple[str, str]] = {
    "google": ("https://www.google.com/search?q={q}", ""),  # busca web simples, sem `site:`
    "youtube": ("https://www.youtube.com/results?search_query={q}", "youtube.com"),
    "tiktok": ("https://www.tiktok.com/search?q={q}", "tiktok.com"),
    "instagram": ("", "instagram.com"),  # a busca nativa exige login: só pela busca web
    "pinterest": ("https://www.pinterest.com/search/pins/?q={q}", "pinterest.com"),
    "reddit": ("https://www.reddit.com/search/?q={q}", "reddit.com"),
    "google_trends": ("https://trends.google.com/trends/explore?q={q}&geo={geo}", None),
    "meta_ad_library": (
        "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
        "&country={geo}&q={q}&search_type=keyword_unordered",
        None,
    ),
}

# Só valem com o termo-base (consulta curta); não têm equivalente em busca web.
BASE_ONLY = ("google_trends", "meta_ad_library")

MARKETPLACES: dict[str, dict[str, tuple[str, str]]] = {
    "BR": {
        "mercado_livre": ("https://lista.mercadolivre.com.br/{slug}", "mercadolivre.com.br"),
        "amazon": ("https://www.amazon.com.br/s?k={q}", "amazon.com.br"),
        "shopee": ("https://shopee.com.br/search?keyword={q}", "shopee.com.br"),
    },
    "US": {"amazon": ("https://www.amazon.com/s?k={q}", "amazon.com")},
}
DEFAULT_MARKETPLACE = {"aliexpress": ("https://www.aliexpress.com/wholesale?SearchText={q}", "aliexpress.com")}


def _expand(term: str, lang: str, per_term: int) -> list[str]:
    mods = MODIFIERS.get(lang) or MODIFIERS.get(lang.split("-")[0]) or [""]
    out: list[str] = []
    for m in mods[:per_term]:
        q = f"{term} {m}".strip()  # sufixo: funciona com verbo ("remover pelo") e com substantivo ("removedor de pelo")
        if q not in out:
            out.append(q)
    return out


def build(brief: dict[str, Any], per_term: int = 7, limit: int = 120) -> list[dict[str, str]]:
    """Gera a lista de consultas (plataforma, idioma, país, texto, busca web, url) a partir do brief."""
    markets = [m.upper() for m in brief.get("market", ["BR"])]
    scope = brief.get("scope") or scope_of(brief)
    pain_terms = brief.get("pain_terms") or {brief.get("language", "pt-BR"): [scope]}
    allowed = set(brief.get("platforms") or [])
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for lang, terms in pain_terms.items():
        for term in terms:
            for query in _expand(term, lang, per_term):
                for market in markets:
                    targets = dict(PLATFORMS)
                    targets.update(MARKETPLACES.get(market, DEFAULT_MARKETPLACE))
                    for platform, (template, site) in targets.items():
                        if allowed and platform not in allowed:
                            continue
                        if platform in BASE_ONLY and query != term:
                            continue
                        key = (platform, query, market)
                        if key in seen:
                            continue
                        seen.add(key)
                        if site is None:
                            web_search = ""
                        elif site:
                            web_search = f"site:{site} {query}"
                        else:
                            web_search = query
                        rows.append(
                            {
                                "platform": platform,
                                "language": lang,
                                "market": market,
                                "query": query,
                                "web_search": web_search,
                                "url": template.format(q=quote_plus(query), geo=market, slug=slugify(query, 80)) if template else "",
                            }
                        )
                        if len(rows) >= limit:
                            return rows
    return rows


def to_markdown(rows: list[dict[str, str]]) -> str:
    lines = ["| Plataforma | Idioma | País | Consulta | Busca web | Link |", "|---|---|---|---|---|---|"]
    for r in rows:
        link = f"<{r['url']}>" if r["url"] else "—"
        ws = f"`{r['web_search']}`" if r["web_search"] else "—"
        lines.append(f"| {r['platform']} | {r['language']} | {r['market']} | {r['query']} | {ws} | {link} |")
    return "\n".join(lines)


def to_searches(rows: list[dict[str, str]]) -> list[str]:
    """Só as buscas web prontas, sem repetir, na ordem."""
    out: list[str] = []
    for r in rows:
        if r["web_search"] and r["web_search"] not in out:
            out.append(r["web_search"])
    return out
