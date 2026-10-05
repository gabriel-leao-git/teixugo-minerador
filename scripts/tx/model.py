"""Modelo de dados e validação do pedido (brief) e do relatório (report).

Somente biblioteca padrão. As funções de validação devolvem listas de mensagens
(erros bloqueiam a geração do relatório; avisos não).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any

LABELS = ("verified", "estimated", "unverified")
LANGS = ("pt-BR", "en")
MODES = ("live", "hypothesis")
FORMATS = ("md", "txt", "html", "docx", "xlsx", "pdf")
RANK_COMPONENTS = ("social", "search", "reviews", "ads")
VARIETY = ("different", "same", "any")

TEXT_KEYS = ("name", "pain", "solution_type")
# Campos com evidência, na ordem de exibição do formato de saída.
FIELD_KEYS = (
    "segment",
    "target_audience",
    "effectiveness",
    "engagement",
    "top_post",
    "social_networks",
    "search_channel",
    "supplier",
    "traction_country",
    "supplier_country",
    "first_seen",
    "comparison",
)
SIGNAL_KEYS = ("engagement", "search_index", "social_platforms", "ad_days", "rating", "reviews")
ECON_KEYS = ("price", "cost", "shipping", "tax", "fee_pct", "fee_fixed", "refund_pct")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://\S+$")

BRIEF_DEFAULTS: dict[str, Any] = {
    "language": "pt-BR",
    "quantity": 3,
    "market": ["BR"],
    "rank_by": ["social", "search"],
    "output_formats": ["md"],
    "solution_variety": "different",
    "include_economics": False,
}


def is_date(value: Any) -> bool:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def slugify(text: str, limit: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:limit].strip("-") or "relatorio"


def fmt_value(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value)


# --------------------------------------------------------------------------- brief


def validate_brief(brief: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    """Valida o pedido estruturado e devolve (erros, avisos, brief com padrões aplicados)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(brief, dict):
        return ["o brief deve ser um objeto JSON"], warnings, {}

    out: dict[str, Any] = {**BRIEF_DEFAULTS, **{k: v for k, v in brief.items() if v is not None}}

    if not isinstance(out.get("pain"), str) or not out["pain"].strip():
        errors.append("pain: obrigatório (a dor que os produtos devem resolver)")
    if out["language"] not in LANGS:
        errors.append(f"language: use um de {LANGS}")
    q = out["quantity"]
    if not isinstance(q, int) or isinstance(q, bool) or not 1 <= q <= 10:
        errors.append("quantity: inteiro entre 1 e 10")
    if not isinstance(out["market"], list) or not out["market"] or not all(isinstance(m, str) and m.strip() for m in out["market"]):
        errors.append("market: lista não vazia de países (ex.: ['BR'])")
    rb = out["rank_by"]
    if not isinstance(rb, list) or not rb or any(r not in RANK_COMPONENTS for r in rb):
        errors.append(f"rank_by: lista com itens de {RANK_COMPONENTS}")
    fm = out["output_formats"]
    if not isinstance(fm, list) or not fm or any(f not in FORMATS for f in fm):
        errors.append(f"output_formats: lista com itens de {FORMATS}")
    if out["solution_variety"] not in VARIETY:
        errors.append(f"solution_variety: use um de {VARIETY}")
    if not isinstance(out["include_economics"], bool):
        errors.append("include_economics: true ou false")

    pt = out.get("pain_terms")
    if pt is not None:
        if not isinstance(pt, dict) or not all(isinstance(v, list) and v and all(isinstance(t, str) and t.strip() for t in v) for v in pt.values()):
            errors.append("pain_terms: objeto {idioma: [termos]} com listas não vazias")
    else:
        warnings.append("pain_terms ausente: a matriz de buscas usará apenas o texto da dor")

    pr = out.get("price_range")
    if pr is not None:
        if not (isinstance(pr, dict) and is_number(pr.get("min")) and is_number(pr.get("max")) and pr["min"] <= pr["max"]):
            errors.append("price_range: {min, max, currency} com min <= max")
    for key in ("extra_fields",):
        if key in out and not (isinstance(out[key], list) and all(isinstance(x, str) for x in out[key])):
            errors.append(f"{key}: lista de textos")
    return errors, warnings, out


# --------------------------------------------------------------------------- report


def _check_field(path: str, f: Any, mode: str, errors: list[str], warnings: list[str], url_value: bool = False) -> None:
    if not isinstance(f, dict):
        errors.append(f"{path}: deve ser um objeto com value/label")
        return
    v = f.get("value")
    ok_value = (isinstance(v, str) and v.strip()) or (
        isinstance(v, list) and v and all(isinstance(x, str) and x.strip() for x in v)
    )
    if not ok_value:
        errors.append(f"{path}.value: obrigatório (texto ou lista de textos não vazios)")
    label = f.get("label")
    if label not in LABELS:
        errors.append(f"{path}.label: use um de {LABELS}")
        return
    if f.get("date") not in (None, "") and not is_date(f.get("date")):
        errors.append(f"{path}.date: use AAAA-MM-DD")
    if label == "verified":
        if not str(f.get("source", "")).strip():
            errors.append(f"{path}: dado 'verified' exige 'source' (onde foi visto)")
        if not is_date(f.get("date")):
            errors.append(f"{path}: dado 'verified' exige 'date' (AAAA-MM-DD da consulta)")
    elif label == "estimated" and not (str(f.get("note", "")).strip() or str(f.get("source", "")).strip()):
        warnings.append(f"{path}: dado 'estimated' deveria explicar em 'note' como foi estimado")
    if mode == "hypothesis" and label != "unverified":
        errors.append(f"{path}: no modo 'hypothesis' todo dado deve ser 'unverified'")
    if url_value and label in ("verified", "estimated") and ok_value and isinstance(v, str) and not URL_RE.match(v):
        errors.append(f"{path}.value: deve ser uma URL http(s) quando 'verified' ou 'estimated'")


def validate_report(report: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(report, dict):
        return ["o relatório deve ser um objeto JSON"], warnings

    meta = report.get("meta")
    if not isinstance(meta, dict):
        return ["meta: obrigatório"], warnings
    if meta.get("language") not in LANGS:
        errors.append(f"meta.language: use um de {LANGS}")
    if meta.get("mode") not in MODES:
        errors.append(f"meta.mode: use um de {MODES}")
    if not is_date(meta.get("generated_at")):
        errors.append("meta.generated_at: use AAAA-MM-DD")
    if not isinstance(meta.get("pain"), str) or not meta["pain"].strip():
        errors.append("meta.pain: obrigatório")
    mode = meta.get("mode")

    products = report.get("products")
    if not isinstance(products, list) or not products:
        errors.append("products: lista não vazia")
        return errors, warnings

    q = meta.get("quantity")
    if isinstance(q, int) and q != len(products):
        warnings.append(f"meta.quantity={q}, mas o relatório tem {len(products)} produto(s)")

    names: set[str] = set()
    types: set[str] = set()
    for i, p in enumerate(products):
        path = f"products[{i}]"
        if not isinstance(p, dict):
            errors.append(f"{path}: deve ser um objeto")
            continue
        for key in TEXT_KEYS:
            if not isinstance(p.get(key), str) or not p[key].strip():
                errors.append(f"{path}.{key}: obrigatório")
        name = str(p.get("name", "")).strip().casefold()
        if name in names:
            errors.append(f"{path}.name: produto duplicado")
        names.add(name)
        types.add(str(p.get("solution_type", "")).strip().casefold())
        for key in FIELD_KEYS:
            if key not in p:
                errors.append(f"{path}.{key}: campo obrigatório ausente")
            else:
                _check_field(f"{path}.{key}", p[key], mode, errors, warnings, url_value=(key == "top_post"))
        sig = p.get("signals")
        if sig is not None:
            if not isinstance(sig, dict):
                errors.append(f"{path}.signals: deve ser um objeto")
            else:
                for k, v in sig.items():
                    if k not in SIGNAL_KEYS:
                        warnings.append(f"{path}.signals.{k}: sinal desconhecido (ignorado)")
                    elif not is_number(v) or v < 0:
                        errors.append(f"{path}.signals.{k}: número >= 0")
                if is_number(sig.get("rating")) and sig["rating"] > 5:
                    errors.append(f"{path}.signals.rating: máximo 5")
        econ = p.get("economics")
        if econ is not None:
            if not isinstance(econ, dict):
                errors.append(f"{path}.economics: deve ser um objeto")
            else:
                for k in ECON_KEYS:
                    if k in econ and (not is_number(econ[k]) or econ[k] < 0):
                        errors.append(f"{path}.economics.{k}: número >= 0")
                if not is_number(econ.get("price")) or econ.get("price", 0) <= 0:
                    errors.append(f"{path}.economics.price: obrigatório e maior que 0")
                if not is_number(econ.get("cost")):
                    errors.append(f"{path}.economics.cost: obrigatório")
                note = econ.get("label")
                if note is not None and note not in LABELS:
                    errors.append(f"{path}.economics.label: use um de {LABELS}")
    if len(products) >= 2 and len(types) == 1 and meta.get("solution_variety") != "any":
        warnings.append("todos os produtos têm o mesmo solution_type; o recomendado é variar o tipo de solução")

    for i, d in enumerate(report.get("discarded") or []):
        if not (isinstance(d, dict) and str(d.get("name", "")).strip() and str(d.get("reason", "")).strip()):
            errors.append(f"discarded[{i}]: precisa de name e reason")
    return errors, warnings
