"""Matriz de buscas: gera, de forma repetível, as consultas a fazer em cada plataforma.

Os links de busca seguem o formato público de cada site e podem mudar; se um deles falhar,
o texto da consulta continua válido para digitar manualmente.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from .model import slugify

# Modificadores que ajudam a achar produto, prova de efetividade e reclamações (para medir efetividade).
MODIFIERS: dict[str, list[str]] = {
    "pt-BR": ["", "funciona mesmo", "antes e depois", "review", "vale a pena", "reclamação", "produto"],
    "en": ["", "does it work", "before and after", "review", "worth it", "complaints", "product"],
    "es": ["", "funciona", "antes y después", "reseña", "vale la pena", "opiniones", "producto"],
}

# {q} = consulta já codificada para URL; {geo} = código do país; {slug} = consulta em kebab-case.
PLATFORMS: dict[str, str] = {
    "google": "https://www.google.com/search?q={q}",
    "youtube": "https://www.youtube.com/results?search_query={q}",
    "tiktok": "https://www.tiktok.com/search?q={q}",
    "pinterest": "https://www.pinterest.com/search/pins/?q={q}",
    "reddit": "https://www.reddit.com/search/?q={q}",
    "google_trends": "https://trends.google.com/trends/explore?q={q}&geo={geo}",
    "meta_ad_library": (
        "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
        "&country={geo}&q={q}&search_type=keyword_unordered"
    ),
}

MARKETPLACES: dict[str, dict[str, str]] = {
    "BR": {
        "mercado_livre": "https://lista.mercadolivre.com.br/{slug}",
        "amazon": "https://www.amazon.com.br/s?k={q}",
        "shopee": "https://shopee.com.br/search?keyword={q}",
    },
    "US": {"amazon": "https://www.amazon.com/s?k={q}"},
}
DEFAULT_MARKETPLACE = {"aliexpress": "https://www.aliexpress.com/wholesale?SearchText={q}"}


def _expand(term: str, lang: str, per_term: int) -> list[str]:
    mods = MODIFIERS.get(lang) or MODIFIERS.get(lang.split("-")[0]) or [""]
    out: list[str] = []
    for m in mods[:per_term]:
        q = f"{term} {m}".strip()  # sufixo: funciona com verbo ("remover pelo") e com substantivo ("removedor de pelo")
        if q not in out:
            out.append(q)
    return out


def build(brief: dict[str, Any], per_term: int = 7, limit: int = 120) -> list[dict[str, str]]:
    """Gera a lista de consultas (plataforma, idioma, país, texto, url) a partir do brief."""
    markets = [m.upper() for m in brief.get("market", ["BR"])]
    pain_terms = brief.get("pain_terms") or {brief.get("language", "pt-BR"): [brief["pain"]]}
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for lang, terms in pain_terms.items():
        for term in terms:
            for query in _expand(term, lang, per_term):
                for market in markets:
                    targets = dict(PLATFORMS)
                    targets.update(MARKETPLACES.get(market, DEFAULT_MARKETPLACE))
                    for platform, template in targets.items():
                        # Trends e Ad Library só valem com o termo-base e uma consulta curta
                        if platform in ("google_trends", "meta_ad_library") and query != term:
                            continue
                        key = (platform, query, market)
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append(
                            {
                                "platform": platform,
                                "language": lang,
                                "market": market,
                                "query": query,
                                "url": template.format(q=quote_plus(query), geo=market, slug=slugify(query, 80)),
                            }
                        )
                        if len(rows) >= limit:
                            return rows
    return rows


def to_markdown(rows: list[dict[str, str]]) -> str:
    lines = ["| Plataforma | Idioma | País | Consulta | Link |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['platform']} | {r['language']} | {r['market']} | {r['query']} | <{r['url']}> |")
    return "\n".join(lines)
