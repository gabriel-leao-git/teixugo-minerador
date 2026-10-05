"""Matriz de buscas: gera, de forma repetível, as consultas a fazer em cada plataforma.

Cada linha traz duas formas de buscar o mesmo assunto:
  * `web_search`: texto pronto para a ferramenta de busca na web (usa `site:` para mirar a plataforma);
  * `url`: link de busca nativo da plataforma, para abrir no navegador (vazio quando não existe um público).

Parâmetros do pedido (brief) que mudam as buscas:
  * `radius` (0 a 3): o quão longe do termo semente a busca vai.
        0 = só `pain_terms` (ou o assunto); 1 = + `related_terms` (sinônimos, formas de falar);
        2 = + `adjacent_terms` (dores ou nichos vizinhos); 3 = + os mesmos termos em `analog_markets`
        (países onde o produto já performou).
  * `intents`: para que serve cada consulta: discovery (que soluções existem), proof (funciona?),
        objection (onde falha?), commerce (quem vende e a que preço?).
  * `period_days`: só resultados recentes (acrescenta o operador `after:AAAA-MM-DD` à busca web).
  * `exclude`: termos a excluir (acrescenta `-"termo"` à busca web).
  * `exact`: coloca o termo entre aspas na busca web (mais preciso, menos abrangente).
  * `platforms`: limita onde pesquisar.

Os operadores `after:`, `-` e aspas são do estilo Google e dependem de a ferramenta de busca aceitá-los;
os formatos de URL das plataformas também podem mudar. O texto da consulta continua válido para digitar à mão.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from urllib.parse import quote_plus

from .model import INTENTS, scope_of, slugify

# intenção -> sufixos por idioma. Os sufixos (e não prefixos) funcionam com verbo e com substantivo.
INTENT_MODIFIERS: dict[str, dict[str, list[str]]] = {
    "pt-BR": {
        "discovery": [""],
        "proof": ["funciona mesmo", "antes e depois", "review", "vale a pena"],
        "objection": ["reclamação"],
        "commerce": ["produto", "preço", "comprar"],
    },
    "en": {
        "discovery": [""],
        "proof": ["does it work", "before and after", "review", "worth it"],
        "objection": ["complaints"],
        "commerce": ["product", "price", "buy"],
    },
    "es": {
        "discovery": [""],
        "proof": ["funciona", "antes y después", "reseña", "vale la pena"],
        "objection": ["opiniones"],
        "commerce": ["producto", "precio", "comprar"],
    },
}

# plataforma -> (modelo de URL nativa, domínio para `site:`). {q} = consulta codificada; {geo} = país; {slug} = kebab-case.
PLATFORMS: dict[str, tuple[str, str | None]] = {
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


def _expand(term: str, lang: str, intents: list[str], per_term: int) -> list[tuple[str, str]]:
    """Variações (consulta, intenção) de um termo, na ordem das intenções, no máximo `per_term`."""
    table = INTENT_MODIFIERS.get(lang) or INTENT_MODIFIERS.get(lang.split("-")[0]) or INTENT_MODIFIERS["en"]
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for intent in INTENTS:
        if intent not in intents:
            continue
        for m in table.get(intent, []):
            q = f"{term} {m}".strip()
            if q not in seen:
                seen.add(q)
                out.append((q, intent))
    return out[:per_term]


def _web_search(site: str | None, term: str, query: str, brief: dict[str, Any], today: date) -> str:
    if site is None:
        return ""
    q = query
    if brief.get("exact") and " " in term and query.startswith(term):
        q = f'"{term}"{query[len(term):]}'
    parts = [f"site:{site}" if site else "", q]
    for ex in brief.get("exclude") or []:
        parts.append(f'-"{ex}"' if " " in ex else f"-{ex}")
    if brief.get("period_days"):
        parts.append(f"after:{(today - timedelta(days=int(brief['period_days']))).isoformat()}")
    return " ".join(p for p in parts if p)


def _layers(brief: dict[str, Any], scope: str) -> list[tuple[int, dict[str, list[str]], list[str]]]:
    """[(camada, {idioma: termos}, mercados)] respeitando o raio."""
    markets = [m.upper() for m in brief.get("market", ["BR"])]
    radius = int(brief.get("radius", 1))
    base = brief.get("pain_terms") or {brief.get("language", "pt-BR"): [scope]}
    layers: list[tuple[int, dict[str, list[str]], list[str]]] = [(0, base, markets)]
    if radius >= 1 and brief.get("related_terms"):
        layers.append((1, brief["related_terms"], markets))
    if radius >= 2 and brief.get("adjacent_terms"):
        layers.append((2, brief["adjacent_terms"], markets))
    if radius >= 3 and brief.get("analog_markets"):
        analog = [m.upper() for m in brief["analog_markets"] if m.upper() not in markets]
        if analog:
            layers.append((3, base, analog))
    return layers


def build(brief: dict[str, Any], per_term: int = 7, limit: int = 120, today: date | None = None) -> list[dict[str, Any]]:
    """Gera a lista de consultas (plataforma, idioma, país, texto, intenção, camada, busca web, url) a partir do brief."""
    today = today or date.today()
    scope = brief.get("scope") or scope_of(brief)
    intents = [i for i in (brief.get("intents") or list(INTENTS)) if i in INTENTS] or list(INTENTS)
    allowed = set(brief.get("platforms") or [])
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for layer, terms_by_lang, markets in _layers(brief, scope):
        for lang, terms in terms_by_lang.items():
            for term in terms:
                for query, intent in _expand(term, lang, intents, per_term):
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
                            rows.append(
                                {
                                    "platform": platform,
                                    "language": lang,
                                    "market": market,
                                    "query": query,
                                    "intent": intent,
                                    "radius": layer,
                                    "web_search": _web_search(site, term, query, brief, today),
                                    "url": template.format(q=quote_plus(query), geo=market, slug=slugify(query, 80)) if template else "",
                                }
                            )
                            if len(rows) >= limit:
                                return rows
    return rows


def to_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Plataforma | Idioma | País | Raio | Intenção | Consulta | Busca web | Link |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        link = f"<{r['url']}>" if r["url"] else "—"
        ws = f"`{r['web_search']}`" if r["web_search"] else "—"
        lines.append(
            f"| {r['platform']} | {r['language']} | {r['market']} | {r['radius']} | {r['intent']} | {r['query']} | {ws} | {link} |"
        )
    return "\n".join(lines)


def to_searches(rows: list[dict[str, Any]]) -> list[str]:
    """Só as buscas web prontas, sem repetir, na ordem."""
    out: list[str] = []
    for r in rows:
        if r["web_search"] and r["web_search"] not in out:
            out.append(r["web_search"])
    return out
