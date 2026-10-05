"""Ranking por tração (redes sociais + busca + avaliações + longevidade dos anúncios).

A nota é RELATIVA aos candidatos da mesma rodada: o melhor em cada componente recebe 100%
daquele componente. Não é uma medida absoluta de qualidade do produto. Um componente que
falta em qualquer produto é descartado para todos, para a comparação continuar justa.
"""
from __future__ import annotations

import math
from typing import Any

# peso de cada componente, escolhido por `rank_by`
WEIGHTS = {"social": 40.0, "search": 30.0, "reviews": 20.0, "ads": 10.0}


def _component_values(signals: dict[str, Any]) -> dict[str, float | None]:
    eng = signals.get("engagement")
    plat = signals.get("social_platforms")
    social: float | None
    if eng is None and plat is None:
        social = None
    else:
        social = (eng or 0.0) + 0.0  # engajamento absoluto; as plataformas entram como bônus abaixo
    rating = signals.get("rating")
    reviews = signals.get("reviews")
    rev: float | None = None
    if rating is not None and reviews is not None:
        confidence = min(1.0, math.log10(reviews + 1) / 4.0)  # ~10 mil avaliações = confiança total
        rev = (rating / 5.0) * confidence
    return {
        "social": social,
        "search": signals.get("search_index"),
        "reviews": rev,
        "ads": signals.get("ad_days"),
    }


def rank(products: list[dict[str, Any]], rank_by: list[str] | None = None) -> dict[str, Any]:
    """Devolve {"order": [índices], "scores": [...], "used": [...], "dropped": [...], "confidence": str}."""
    wanted = [c for c in (rank_by or ["social", "search"]) if c in WEIGHTS]
    comps = [_component_values(p.get("signals") or {}) for p in products]
    plats = [(p.get("signals") or {}).get("social_platforms") for p in products]

    used: list[str] = []
    dropped: list[str] = []
    for c in wanted:
        (used if all(v[c] is not None for v in comps) else dropped).append(c)

    total_w = sum(WEIGHTS[c] for c in used)
    scores: list[dict[str, Any]] = []
    for i, v in enumerate(comps):
        parts: dict[str, float] = {}
        for c in used:
            peak = max(x[c] for x in comps)  # type: ignore[type-var]
            ratio = (v[c] / peak) if peak else 0.0  # type: ignore[operator]
            if c == "social" and all(p is not None for p in plats):
                pmax = max(plats) or 1  # type: ignore[type-var]
                ratio = 0.7 * ratio + 0.3 * (plats[i] / pmax)  # type: ignore[operator]
            parts[c] = round(ratio * 100.0, 1)
        total = sum(parts[c] * WEIGHTS[c] for c in used) / total_w if total_w else 0.0
        scores.append({"score": round(total, 1), "components": parts})

    order = sorted(range(len(products)), key=lambda i: (-scores[i]["score"], i))
    confidence = "high" if len(used) >= 3 else "medium" if len(used) == 2 else "low"
    return {"order": order, "scores": scores, "used": used, "dropped": dropped, "confidence": confidence}


def apply(report: dict[str, Any], rank_by: list[str] | None = None) -> dict[str, Any]:
    """Grava `traction_score`, `score_components` em cada produto e reordena a lista."""
    products = report["products"]
    result = rank(products, rank_by or report.get("meta", {}).get("rank_by"))
    for i, p in enumerate(products):
        p["traction_score"] = result["scores"][i]["score"]
        p["score_components"] = result["scores"][i]["components"]
    report["products"] = [products[i] for i in result["order"]]
    report.setdefault("meta", {})["rank_used"] = result["used"]
    report["meta"]["rank_dropped"] = result["dropped"]
    report["meta"]["rank_confidence"] = result["confidence"]
    return report
