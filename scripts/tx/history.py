"""Histórico de retratos e sonar: mede ACELERAÇÃO (quanto cresceu desde a leitura anterior).

Ninguém prevê viral. O que dá para medir é velocidade: quando engajamento, busca, avaliações, criadores e
número de anunciantes crescem rápido entre duas leituras. Por isso o sonar precisa de histórico:
a primeira leitura é só a linha de base.

Convenções:
  * Crescimento é convertido para o equivalente SEMANAL composto, para leituras com intervalos
    diferentes ficarem comparáveis.
  * Bases pequenas (ex.: de 10 para 40 views) são ignoradas, porque inflam o percentual.
  * A nota de aceleração (0-100) é ABSOLUTA: GROWTH_CAP % semanais em um componente dão a nota
    máxima daquele componente. Não depende dos outros produtos.
  * A "janela" (0-100) é RELATIVA e compara atenção com concorrência dentro da mesma leitura.
  * "Persistência": quantos dias seguidos (entre leituras consecutivas) o produto acelerou. Um pico de
    um dia não é tendência; crescimento mantido por 14 dias ou mais (SUSTAIN_DAYS) é um sinal mais firme.
  * "Saturação": faixa pelo número de anunciantes ativos. As faixas vêm de heurísticas de mercado
    (poucos anunciantes = demanda validada e janela aberta; dezenas = janela fechando) e NÃO são
    verdades: confira no seu nicho.
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from .model import is_date, scope_of, slugify

WEIGHTS = {"social": 40.0, "search": 30.0, "reviews": 20.0, "ads": 10.0, "creators": 20.0}
SIGNAL_OF = {"social": "engagement", "search": "search_index", "reviews": "reviews", "ads": "advertisers", "creators": "creators"}
MIN_BASE = {"engagement": 1000.0, "search_index": 5.0, "reviews": 20.0, "advertisers": 3.0, "creators": 5.0}
GROWTH_CAP = 100.0  # % semanal que dá a nota máxima de um componente
SUSTAIN_DAYS = 14  # dias de aceleração contínua para considerar a tendência sustentada
DEFAULT_THRESHOLDS: dict[str, Any] = {
    "min_growth": 20.0,  # % semanal para um componente contar como "acelerando"
    "min_score": 40.0,  # nota de aceleração (0-100) exigida para o nível forte
    "min_days": 2,  # intervalo mínimo entre leituras
    "sustain_days": SUSTAIN_DAYS,  # dias de aceleração contínua para marcar "sustentada"
    "alert_on_new": True,  # avisar quando surge produto novo
    "alert_on_moderate": False,  # avisar também no nível moderado (mais sensível, mais ruído)
}
LEVEL_RANK = {"strong": 3, "moderate": 2, "none": 1, "baseline": 0}
# limite superior (inclusive) de anunciantes por faixa; None = sem limite
SATURATION_BANDS = ((2, "initial"), (10, "healthy"), (49, "warm"), (None, "saturated"))


def saturation(advertisers: float | None) -> str | None:
    """Faixa de saturação pelo número de anunciantes ativos (None quando não há o dado)."""
    if advertisers is None:
        return None
    for top, name in SATURATION_BANDS:
        if top is None or advertisers <= top:
            return name
    return None


def product_key(p: dict[str, Any]) -> str:
    """Chave estável do produto entre leituras: `id` se existir, senão o nome em kebab-case."""
    return str(p.get("id") or slugify(str(p["name"]), 60))


def make_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    meta = report["meta"]
    return {
        "taken_at": meta["generated_at"],
        "scope": scope_of(meta),
        "market": meta.get("market"),
        "products": {
            product_key(p): {
                "name": p["name"],
                "solution_type": p.get("solution_type", ""),
                "signals": dict(p.get("signals") or {}),
            }
            for p in report["products"]
        },
    }


def load(path: str) -> dict[str, Any]:
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        data.setdefault("snapshots", [])
        return data
    return {"snapshots": []}


def save(path: str, hist: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(hist, ensure_ascii=False, indent=2) + "\n")


def add_snapshot(hist: dict[str, Any], snap: dict[str, Any]) -> dict[str, Any]:
    """Acrescenta o retrato; uma nova leitura no mesmo dia substitui a anterior."""
    snaps = [s for s in hist["snapshots"] if s["taken_at"] != snap["taken_at"]]
    snaps.append(snap)
    hist["snapshots"] = sorted(snaps, key=lambda s: s["taken_at"])
    return hist


def previous(hist: dict[str, Any], taken_at: str) -> dict[str, Any] | None:
    """O retrato mais recente anterior à data informada."""
    older = [s for s in hist["snapshots"] if s["taken_at"] < taken_at]
    return older[-1] if older else None


def before(hist: dict[str, Any], taken_at: str) -> list[dict[str, Any]]:
    """Todos os retratos anteriores à data, do mais antigo ao mais recente."""
    return sorted((s for s in hist["snapshots"] if s["taken_at"] < taken_at), key=lambda s: s["taken_at"])


def weekly_growth(old: float | None, new: float | None, days: int, min_base: float, min_days: int = 2) -> float | None:
    """Crescimento semanal composto, em %. None quando não dá para medir com segurança."""
    if old is None or new is None or days < min_days or old < min_base or old <= 0:
        return None
    return round(((new / old) ** (7.0 / days) - 1.0) * 100.0, 1)


def window_scores(signals: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    """Janela de oportunidade (relativa): muita atenção e poucos anunciantes. Precisa dos dois sinais."""
    ok = {k: s for k, s in signals.items() if s.get("engagement") is not None and s.get("advertisers") is not None}
    out: dict[str, float | None] = {k: None for k in signals}
    if not ok:
        return out
    max_e = max(s["engagement"] for s in ok.values())
    max_a = max(s["advertisers"] for s in ok.values())
    for k, s in ok.items():
        attention = s["engagement"] / max_e if max_e else 0.0
        competition = s["advertisers"] / max_a if max_a else 0.0
        out[k] = round(100.0 * attention * (1.0 - competition), 1)
    return out


def _growth(old_sig: dict[str, Any], new_sig: dict[str, Any], days: int, th: dict[str, Any]) -> dict[str, float | None]:
    return {
        comp: weekly_growth(old_sig.get(sig), new_sig.get(sig), days, MIN_BASE[sig], th["min_days"])
        for comp, sig in SIGNAL_OF.items()
    }


def _accelerating(growth: dict[str, float | None], th: dict[str, Any]) -> list[str]:
    return [c for c, g in growth.items() if g is not None and g >= th["min_growth"]]


def _level(score: float | None, accelerating: list[str], th: dict[str, Any]) -> str:
    """forte = nota mínima e ao menos 2 componentes acelerando; moderado = ao menos 1 componente acelerando."""
    if score is None or not accelerating:
        return "none"
    if score >= th["min_score"] and len(accelerating) >= 2:
        return "strong"
    return "moderate"


def _persistence(key: str, chain: list[dict[str, Any]], th: dict[str, Any]) -> tuple[int, int]:
    """(leituras consecutivas acelerando, dias desde o início da sequência). `chain` vai do mais antigo ao atual."""
    streak = 0
    start = chain[-1]["taken_at"]
    for i in range(len(chain) - 1, 0, -1):
        newer, older = chain[i], chain[i - 1]
        a, b = older["products"].get(key), newer["products"].get(key)
        if a is None or b is None:
            break
        days = (date.fromisoformat(newer["taken_at"]) - date.fromisoformat(older["taken_at"])).days
        if not _accelerating(_growth(a["signals"], b["signals"], days, th), th):
            break
        streak += 1
        start = older["taken_at"]
    span = (date.fromisoformat(chain[-1]["taken_at"]) - date.fromisoformat(start)).days if streak else 0
    return streak, span


def compare(
    prev: dict[str, Any] | None,
    cur: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
    older: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compara a leitura atual com a anterior. Sem leitura anterior, devolve a linha de base.

    `older`: leituras ainda mais antigas que `prev` (do mais antigo ao mais recente), usadas só para medir a persistência.
    """
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    window = window_scores({k: v["signals"] for k, v in cur["products"].items()})
    base: dict[str, Any] = {
        "baseline": prev is None,
        "taken_at": cur["taken_at"],
        "compared_to": prev["taken_at"] if prev else None,
        "days": None,
        "thresholds": th,
        "items": {},
        "new": [],
        "gone": [],
    }

    def item(name: str, key: str, **extra: Any) -> dict[str, Any]:
        sat = saturation(cur["products"][key]["signals"].get("advertisers"))
        return {"name": name, "level": "none", "acceleration": None, "growth": {}, "accelerating": [], "window": window[key],
                "saturation": sat, "streak": 0, "sustained_days": 0, "sustained": False, **extra}

    if prev is None:
        base["items"] = {k: item(v["name"], k, level="baseline") for k, v in cur["products"].items()}
        return base

    days = (date.fromisoformat(cur["taken_at"]) - date.fromisoformat(prev["taken_at"])).days
    base["days"] = days
    chain = list(older or []) + [prev, cur]
    for key, c in cur["products"].items():
        p = prev["products"].get(key)
        if p is None:
            base["new"].append({"key": key, "name": c["name"]})
            base["items"][key] = item(c["name"], key)
            continue
        growth = _growth(p["signals"], c["signals"], days, th)
        used = {comp: g for comp, g in growth.items() if g is not None}
        total_w = sum(WEIGHTS[x] for x in used)
        score = (
            round(sum(WEIGHTS[x] * min(max(g, 0.0), GROWTH_CAP) / GROWTH_CAP for x, g in used.items()) / total_w * 100.0, 1)
            if total_w
            else None
        )
        accelerating = _accelerating(growth, th)
        streak, span = _persistence(key, chain, th)
        base["items"][key] = item(
            c["name"], key,
            level=_level(score, accelerating, th), acceleration=score, growth=growth, accelerating=accelerating,
            streak=streak, sustained_days=span, sustained=bool(streak and span >= th["sustain_days"]),
        )
    base["gone"] = [{"key": k, "name": v["name"]} for k, v in prev["products"].items() if k not in cur["products"]]
    return base


def has_alert(comparison: dict[str, Any]) -> bool:
    """Alerta quando algum produto acelera forte; moderado e produto novo só se configurado."""
    if comparison["baseline"]:
        return False
    th = comparison["thresholds"]
    levels = {i["level"] for i in comparison["items"].values()}
    if "strong" in levels or (th.get("alert_on_moderate") and "moderate" in levels):
        return True
    return bool(th.get("alert_on_new") and comparison["new"])


SONAR_KEYS = ("level", "acceleration", "growth", "accelerating", "window", "saturation", "streak", "sustained_days", "sustained")


def apply_to_report(report: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    """Grava `sonar` em cada produto e `radar` no relatório; no tipo sonar, reordena por aceleração e janela."""
    for p in report["products"]:
        found = comparison["items"].get(product_key(p))
        if found:
            p["sonar"] = {k: found[k] for k in SONAR_KEYS}
    report["radar"] = {
        "baseline": comparison["baseline"],
        "taken_at": comparison["taken_at"],
        "compared_to": comparison["compared_to"],
        "days": comparison["days"],
        "new": [n["name"] for n in comparison["new"]],
        "gone": [g["name"] for g in comparison["gone"]],
    }
    if report["meta"].get("kind") == "sonar":
        def order(p: dict[str, Any]) -> tuple[float, float]:
            s = p.get("sonar", {})
            return (-(s.get("acceleration") if s.get("acceleration") is not None else -1.0),
                    -(s.get("window") if s.get("window") is not None else -1.0))

        report["products"] = sorted(report["products"], key=order)
    return report


def validate_date(value: str) -> bool:
    return is_date(value)
