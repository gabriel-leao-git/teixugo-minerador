"""Converte o relatório (JSON) numa lista de blocos neutros de formato.

Todos os renderizadores (md, txt, html, docx, pdf) consomem os mesmos blocos, então o
conteúdo e os números são idênticos em qualquer formato.

Tipos de bloco (dict com a chave "t"):
  title, banner, meta(items), h2, h3, p, bullets(items), ol(items), field, table(headers, rows), note
"""
from __future__ import annotations

from typing import Any

from . import economics
from .model import FIELD_KEYS, URL_RE, fmt_value, scope_of

STR: dict[str, dict[str, Any]] = {
    "pt-BR": {
        "title": "Relatório Teixugo Minerador — {pain}",
        "demo": "EXEMPLO FICTÍCIO — dados de demonstração. Não use para decidir nada.",
        "hypothesis": "MODO HIPÓTESE — sem acesso a dados ao vivo. Nada abaixo foi verificado: use como lista de pontos a validar.",
        "date": "Data da consulta",
        "market": "Mercado",
        "mode": "Modo",
        "modes": {"live": "dados ao vivo", "hypothesis": "hipótese"},
        "request": "Pedido",
        "summary": "Resumo",
        "assumptions": "Premissas e limites",
        "products": "Produtos",
        "comparison": "Comparação",
        "economics": "Unit economics",
        "discarded": "Produtos descartados",
        "sources": "Fontes",
        "next": "Próximos passos",
        "legend": "Etiquetas: Verificado = visto na fonte, com data. Estimado = inferência explicada. Não verificado = não foi possível confirmar.",
        "disclaimer": "Este relatório é uma análise de pesquisa e não garante resultados de venda. Confirme leis, tributos e regras de plataforma do seu mercado antes de investir.",
        "risks": "Riscos",
        "score": "Pontuação de tração",
        "score_note": "relativa aos candidatos desta rodada",
        "confidence": "confiança",
        "conf": {"high": "alta", "medium": "média", "low": "baixa"},
        "dropped": "Componentes sem dado para todos os produtos (fora do cálculo)",
        "tags": {"verified": "Verificado", "estimated": "Estimado", "unverified": "Não verificado"},
        "fields": {
            "name": "Produto",
            "pain": "Dor",
            "solution_type": "Tipo de solução",
            "segment": "Segmento",
            "target_audience": "Público-alvo",
            "effectiveness": "Efetividade",
            "engagement": "Engajamento",
            "top_post": "Link (maior engajamento)",
            "social_networks": "Redes sociais com maior engajamento",
            "search_channel": "Canal com maior busca",
            "supplier": "Fornecedor",
            "traction_country": "País de maior tração",
            "supplier_country": "País do fornecedor",
            "first_seen": "Primeira aparição verificada",
            "comparison": "Comparação",
        },
        "cmp_headers": ["Produto", "Tipo de solução", "Engajamento", "Canal com maior busca", "Fornecedor", "País de maior tração", "Efetividade"],
        "econ": {
            "price": "Preço de venda",
            "cost": "Custo do produto + frete + impostos",
            "fees": "Taxas (gateway + plataforma)",
            "refund": "Reserva de reembolso",
            "profit": "Lucro antes de anúncio",
            "margin": "Margem",
            "cpa": "CPA de equilíbrio",
            "roas": "ROAS de equilíbrio",
            "base": "Cenário base",
            "drop": "Preço −{n}%",
            "none": "não fecha",
        },
        "src_cols": ["Fonte", "Data", "Etiqueta", "Usada em"],
        "verdict": "Veredito",
        "via": "via",
        "methods": {
            "web_search": "busca web", "web_fetch": "leitura de página", "browser": "navegador",
            "api": "API oficial", "user_provided": "dado do usuário", "estimate": "estimativa",
        },
        "sonar": "Sonar: aceleração desde a leitura anterior",
        "sonar_cols": ["Produto", "Nível", "Aceleração (0–100)", "Engajamento", "Busca", "Avaliações", "Anunciantes", "Criadores", "Persistência", "Saturação", "Janela (0–100)"],
        "sat": {"initial": "inicial (0–2 anunciantes)", "healthy": "saudável (3–10)", "warm": "aquecida (11–49)", "saturated": "saturada (50+)"},
        "persist_yes": "sustentada ({n} dias)",
        "persist_n": "{n} leitura(s)",
        "levels": {"strong": "forte", "moderate": "moderada", "none": "sem aceleração", "baseline": "linha de base"},
        "sonar_baseline": "Primeira leitura: linha de base registrada. A aceleração aparece a partir da próxima leitura (intervalo recomendado: 3 a 7 dias).",
        "sonar_compared": "Crescimento semanal equivalente, comparando {prev} com {cur} ({days} dias). Bases pequenas são ignoradas.",
        "sonar_new": "Novos no radar",
        "sonar_gone": "Não apareceram nesta leitura",
        "sonar_note": "Aceleração não é previsão: é crescimento medido entre duas leituras. A janela compara atenção com número de anunciantes nesta leitura (é relativa).",
    },
    "en": {
        "title": "Teixugo Minerador Report — {pain}",
        "demo": "FICTIONAL EXAMPLE — demonstration data. Do not use it to decide anything.",
        "hypothesis": "HYPOTHESIS MODE — no live data access. Nothing below was verified: use it as a list of points to validate.",
        "date": "Research date",
        "market": "Market",
        "mode": "Mode",
        "modes": {"live": "live data", "hypothesis": "hypothesis"},
        "request": "Request",
        "summary": "Summary",
        "assumptions": "Assumptions and limits",
        "products": "Products",
        "comparison": "Comparison",
        "economics": "Unit economics",
        "discarded": "Discarded products",
        "sources": "Sources",
        "next": "Next steps",
        "legend": "Labels: Verified = seen at the source, with date. Estimated = explained inference. Unverified = could not be confirmed.",
        "disclaimer": "This report is research analysis and does not guarantee sales results. Check the laws, taxes and platform rules of your market before investing.",
        "risks": "Risks",
        "score": "Traction score",
        "score_note": "relative to this run's candidates",
        "confidence": "confidence",
        "conf": {"high": "high", "medium": "medium", "low": "low"},
        "dropped": "Components with no data for every product (left out of the calculation)",
        "tags": {"verified": "Verified", "estimated": "Estimated", "unverified": "Unverified"},
        "fields": {
            "name": "Product",
            "pain": "Pain",
            "solution_type": "Solution type",
            "segment": "Segment",
            "target_audience": "Target audience",
            "effectiveness": "Effectiveness",
            "engagement": "Engagement",
            "top_post": "Link (top engagement)",
            "social_networks": "Social networks with highest engagement",
            "search_channel": "Top search channel",
            "supplier": "Supplier",
            "traction_country": "Country with most traction",
            "supplier_country": "Supplier country",
            "first_seen": "First verified appearance",
            "comparison": "Comparison",
        },
        "cmp_headers": ["Product", "Solution type", "Engagement", "Top search channel", "Supplier", "Country with most traction", "Effectiveness"],
        "econ": {
            "price": "Selling price",
            "cost": "Product cost + shipping + taxes",
            "fees": "Fees (gateway + platform)",
            "refund": "Refund reserve",
            "profit": "Profit before ads",
            "margin": "Margin",
            "cpa": "Break-even CPA",
            "roas": "Break-even ROAS",
            "base": "Base case",
            "drop": "Price −{n}%",
            "none": "does not break even",
        },
        "src_cols": ["Source", "Date", "Label", "Used in"],
        "verdict": "Verdict",
        "via": "via",
        "methods": {
            "web_search": "web search", "web_fetch": "page read", "browser": "browser",
            "api": "official API", "user_provided": "user-provided", "estimate": "estimate",
        },
        "sonar": "Sonar: acceleration since the previous reading",
        "sonar_cols": ["Product", "Level", "Acceleration (0–100)", "Engagement", "Search", "Reviews", "Advertisers", "Creators", "Persistence", "Saturation", "Window (0–100)"],
        "sat": {"initial": "early (0–2 advertisers)", "healthy": "healthy (3–10)", "warm": "warm (11–49)", "saturated": "saturated (50+)"},
        "persist_yes": "sustained ({n} days)",
        "persist_n": "{n} reading(s)",
        "levels": {"strong": "strong", "moderate": "moderate", "none": "no acceleration", "baseline": "baseline"},
        "sonar_baseline": "First reading: baseline recorded. Acceleration shows up from the next reading (recommended gap: 3 to 7 days).",
        "sonar_compared": "Weekly-equivalent growth, comparing {prev} with {cur} ({days} days). Small bases are ignored.",
        "sonar_new": "New on the radar",
        "sonar_gone": "Did not show up in this reading",
        "sonar_note": "Acceleration is not a forecast: it is growth measured between two readings. The window compares attention with the number of advertisers in this reading (it is relative).",
    },
}

# ordem dos campos no formato de saída (os 3 primeiros são texto simples, sem evidência)
PLAIN_KEYS = ("name", "pain", "solution_type")


def strings(lang: str) -> dict[str, Any]:
    return STR.get(lang, STR["pt-BR"])


def src_text(f: dict[str, Any], S: dict[str, Any] | None = None) -> str:
    parts = [str(x) for x in (f.get("source"), f.get("date"), f.get("note")) if x]
    method = f.get("method")
    if method:
        parts.append(f"{S['via']} {S['methods'].get(method, method)}" if S else f"via {method}")
    return " · ".join(parts)


def evidence_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    """Uma linha por (produto, campo): valor, etiqueta, fonte, data e nota. Usado no Excel."""
    S = strings(report["meta"]["language"])
    rows = []
    for p in report["products"]:
        for key in FIELD_KEYS:
            f = p[key]
            rows.append(
                {
                    "product": p["name"],
                    "field": S["fields"][key],
                    "value": fmt_value(f["value"]),
                    "label": f["label"],
                    "tag": S["tags"][f["label"]],
                    "source": str(f.get("source", "")),
                    "date": str(f.get("date", "")),
                    "note": str(f.get("note", "")),
                    "method": S["methods"].get(f.get("method"), "") if f.get("method") else "",
                }
            )
    return rows


def collect_sources(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Fontes únicas (fonte + data + etiqueta) e onde cada uma foi usada."""
    found: dict[tuple[str, str, str], list[str]] = {}
    for p in report["products"]:
        for key in FIELD_KEYS:
            f = p[key]
            src = str(f.get("source", "")).strip()
            if not src:
                continue
            k = (src, str(f.get("date", "")), f["label"])
            where = f"{p['name']} / {key}"
            found.setdefault(k, []).append(where)
    for s in report.get("sources") or []:
        if isinstance(s, dict) and s.get("url"):
            k = (str(s["url"]), str(s.get("date", "")), str(s.get("label", "verified")))
            found.setdefault(k, [])
    return [{"source": k[0], "date": k[1], "label": k[2], "used_in": v} for k, v in found.items()]


def _field(label: str, f: dict[str, Any], S: dict[str, Any], key: str = "") -> dict[str, Any]:
    value = f["value"]
    if key == "social_networks" and isinstance(value, list):
        text = "; ".join(f"{i}) {x}" for i, x in enumerate(value, 1))
    else:
        text = fmt_value(value)
    return {
        "t": "field",
        "label": label,
        "value": text,
        "url": text if URL_RE.match(text) else None,
        "tag": f["label"],
        "tagtext": S["tags"][f["label"]],
        "src": src_text(f, S),
    }


def _sonar_blocks(report: dict[str, Any], S: dict[str, Any]) -> list[dict[str, Any]]:
    radar = report.get("radar")
    products = report["products"]
    if not radar and not any("sonar" in p for p in products):
        return []
    B: list[dict[str, Any]] = [{"t": "h2", "text": S["sonar"]}]
    if radar and radar.get("baseline"):
        B.append({"t": "p", "text": S["sonar_baseline"]})
    elif radar:
        B.append({"t": "p", "text": S["sonar_compared"].format(prev=radar["compared_to"], cur=radar["taken_at"], days=radar["days"])})

    def cell(g: dict[str, Any], comp: str) -> str:
        v = g.get(comp)
        return f"{v:+.0f}%" if v is not None else "—"

    rows = []
    for p in products:
        s = p.get("sonar")
        if not s:
            continue
        g = s.get("growth") or {}
        if s.get("sustained"):
            persist = S["persist_yes"].format(n=s.get("sustained_days", 0))
        elif s.get("streak"):
            persist = S["persist_n"].format(n=s["streak"])
        else:
            persist = "—"
        rows.append(
            [
                p["name"],
                S["levels"].get(s["level"], s["level"]),
                "—" if s.get("acceleration") is None else str(s["acceleration"]),
                cell(g, "social"), cell(g, "search"), cell(g, "reviews"), cell(g, "ads"), cell(g, "creators"),
                persist,
                S["sat"].get(s.get("saturation"), "—"),
                "—" if s.get("window") is None else str(s["window"]),
            ]
        )
    if rows:
        B.append({"t": "table", "headers": list(S["sonar_cols"]), "rows": rows})
    if radar and radar.get("new"):
        B += [{"t": "p", "text": S["sonar_new"] + ":"}, {"t": "bullets", "items": list(radar["new"])}]
    if radar and radar.get("gone"):
        B += [{"t": "p", "text": S["sonar_gone"] + ":"}, {"t": "bullets", "items": list(radar["gone"])}]
    B.append({"t": "note", "text": S["sonar_note"]})
    return B


def build_blocks(report: dict[str, Any]) -> list[dict[str, Any]]:
    meta = report["meta"]
    S = strings(meta["language"])
    B: list[dict[str, Any]] = [{"t": "title", "text": S["title"].format(pain=scope_of(meta))}]
    if meta.get("demo"):
        B.append({"t": "banner", "text": S["demo"]})
    if meta.get("mode") == "hypothesis":
        B.append({"t": "banner", "text": S["hypothesis"]})

    market = meta.get("market")
    items = [(S["date"], meta["generated_at"])]
    if market:
        items.append((S["market"], ", ".join(market) if isinstance(market, list) else str(market)))
    items.append((S["mode"], S["modes"][meta["mode"]]))
    if meta.get("request"):
        items.append((S["request"], str(meta["request"])))
    B.append({"t": "meta", "items": items})

    products = report["products"]

    # 1. Resumo
    B.append({"t": "h2", "text": S["summary"]})
    top = []
    for p in products:
        line = f"{p['name']} — {p['solution_type']}"
        if "traction_score" in p:
            line += f" — {S['score']}: {p['traction_score']}/100"
        top.append(line)
    B.append({"t": "ol", "items": top})
    if report.get("verdict"):
        B.append({"t": "p", "text": f"{S['verdict']}: {report['verdict']}"})

    # 2. Premissas e limites
    B.append({"t": "h2", "text": S["assumptions"]})
    lim = list(report.get("assumptions") or []) + list(report.get("limits") or [])
    if meta.get("rank_used"):
        used = ", ".join(meta["rank_used"])
        line = f"{S['score']} ({S['score_note']}): {used}; {S['confidence']} {S['conf'].get(meta.get('rank_confidence', 'low'), '')}"
        lim.append(line)
        if meta.get("rank_dropped"):
            lim.append(f"{S['dropped']}: {', '.join(meta['rank_dropped'])}")
    if lim:
        B.append({"t": "bullets", "items": lim})
    B.append({"t": "note", "text": S["legend"]})

    # 3. Produtos
    B.append({"t": "h2", "text": S["products"]})
    for i, p in enumerate(products, 1):
        B.append({"t": "h3", "text": f"{i}. {p['name']}"})
        if "traction_score" in p:
            conf = S["conf"].get(meta.get("rank_confidence", ""), "")
            extra = f" ({S['confidence']}: {conf})" if conf else ""
            B.append({"t": "p", "text": f"{S['score']}: {p['traction_score']}/100{extra}"})
        for key in PLAIN_KEYS:
            B.append({"t": "field", "label": S["fields"][key], "value": p[key], "url": None, "tag": None, "tagtext": "", "src": ""})
        for key in FIELD_KEYS:
            B.append(_field(S["fields"][key], p[key], S, key))
        if p.get("risks"):
            B.append({"t": "field", "label": S["risks"], "value": "; ".join(str(r) for r in p["risks"]), "url": None, "tag": None, "tagtext": "", "src": ""})

    # 4. Comparação lado a lado (montada dos próprios campos)
    B.append({"t": "h2", "text": S["comparison"]})
    headers = list(S["cmp_headers"])
    show_score = any("traction_score" in p for p in products)
    if show_score:
        headers.append(S["score"])
    rows = []
    for p in products:
        row = [
            p["name"],
            p["solution_type"],
            fmt_value(p["engagement"]["value"]),
            fmt_value(p["search_channel"]["value"]),
            fmt_value(p["supplier"]["value"]),
            fmt_value(p["traction_country"]["value"]),
            fmt_value(p["effectiveness"]["value"]),
        ]
        if show_score:
            row.append(str(p.get("traction_score", "")))
        rows.append(row)
    B.append({"t": "table", "headers": headers, "rows": rows})
    for p in products:
        B.append({"t": "p", "text": f"{p['name']}: {fmt_value(p['comparison']['value'])}"})

    B += _sonar_blocks(report, S)

    # 5. Unit economics (só se algum produto trouxe `economics`)
    with_econ = [p for p in products if isinstance(p.get("economics"), dict)]
    if with_econ:
        E = S["econ"]
        B.append({"t": "h2", "text": S["economics"]})
        drop_pct = float(report.get("meta", {}).get("price_drop_pct", 15))
        for p in with_econ:
            sc = economics.scenarios(p["economics"], drop_pct)
            cur = p["economics"].get("currency")
            B.append({"t": "h3", "text": f"{p['name']} ({cur})" if cur else p["name"]})

            def cell(sce: dict[str, Any], k: str) -> str:
                return f"{sce[k]:.2f}"

            def roas(sce: dict[str, Any]) -> str:
                return f"{sce['roas_breakeven']:.2f}" if sce["roas_breakeven"] is not None else E["none"]

            tbl_rows = [
                [E["price"], cell(sc["base"], "price"), cell(sc["drop"], "price")],
                [E["cost"], cell(sc["base"], "total_cost"), cell(sc["drop"], "total_cost")],
                [E["fees"], cell(sc["base"], "fees"), cell(sc["drop"], "fees")],
                [E["refund"], cell(sc["base"], "refund_reserve"), cell(sc["drop"], "refund_reserve")],
                [E["profit"], cell(sc["base"], "profit_before_ads"), cell(sc["drop"], "profit_before_ads")],
                [E["margin"], f"{sc['base']['margin_pct']}%", f"{sc['drop']['margin_pct']}%"],
                [E["cpa"], cell(sc["base"], "cpa_breakeven"), cell(sc["drop"], "cpa_breakeven")],
                [E["roas"], roas(sc["base"]), roas(sc["drop"])],
            ]
            B.append(
                {
                    "t": "table",
                    "headers": ["", E["base"], E["drop"].format(n=f"{drop_pct:g}")],
                    "rows": tbl_rows,
                }
            )

    # 6. Descartados
    if report.get("discarded"):
        B.append({"t": "h2", "text": S["discarded"]})
        B.append({"t": "bullets", "items": [f"{d['name']} — {d['reason']}" for d in report["discarded"]]})

    # 7. Próximos passos
    if report.get("next_steps"):
        B.append({"t": "h2", "text": S["next"]})
        B.append({"t": "bullets", "items": [str(x) for x in report["next_steps"]]})

    # 8. Fontes
    srcs = collect_sources(report)
    if srcs:
        B.append({"t": "h2", "text": S["sources"]})
        B.append(
            {
                "t": "table",
                "headers": list(S["src_cols"]),
                "rows": [[s["source"], s["date"], S["tags"].get(s["label"], s["label"]), "; ".join(s["used_in"])] for s in srcs],
            }
        )

    B.append({"t": "note", "text": S["disclaimer"]})
    return B
