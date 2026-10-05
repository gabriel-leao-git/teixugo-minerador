"""Sondas: triagem barata de muitos candidatos antes da verificação cara.

Uma sonda é uma olhada rápida e padronizada em UM candidato: uma ou duas buscas na web (primeira página de
resultados) e a contagem do que apareceu. Em vez de verificar a fundo 20 candidatos, sonda-se todos e
verifica-se a fundo só os que passam. As contagens são **de resultados encontrados**, não métricas de
plataforma: servem para ordenar a fila, não para provar nada (a prova vem depois, na verificação).

Contagens (cada uma de 0 a CAP, a partir da primeira página de resultados):
  social_hits     posts ou vídeos distintos sobre o candidato em redes sociais
  market_hits     anúncios distintos do candidato em marketplaces
  recent_hits     resultados do período recente (ex.: últimos 90 dias)
  ads_hits        anunciantes distintos vistos
  complaint_hits  resultados com reclamação ou "não funciona" (evidência NEGATIVA)

Nota 0-100 = 100 * (0,30 social + 0,25 mercado + 0,25 recência + 0,10 anúncios) - penalidade de reclamações
(até PENALTY_MAX). Pesos e limiares são heurísticas ajustáveis, não verdades.
"""
from __future__ import annotations

from typing import Any

CAP = 10
WEIGHTS = {"social_hits": 0.30, "market_hits": 0.25, "recent_hits": 0.25, "ads_hits": 0.10}
PENALTY_MAX = 25.0
VERIFY_AT = 60.0  # nota para entrar na verificação a fundo
WATCH_AT = 35.0  # nota para ficar em observação
HIT_KEYS = tuple(WEIGHTS) + ("complaint_hits",)


def score(hits: dict[str, Any]) -> dict[str, Any]:
    """Nota de uma sonda. Contagens ausentes valem 0 e entram em `missing`."""
    missing = [k for k in HIT_KEYS if hits.get(k) is None]
    vals = {k: max(0, min(CAP, int(hits.get(k) or 0))) for k in HIT_KEYS}
    base = 100.0 * sum(WEIGHTS[k] * vals[k] / CAP for k in WEIGHTS)
    penalty = PENALTY_MAX * vals["complaint_hits"] / CAP
    total = round(max(0.0, base - penalty), 1)
    return {"score": total, "penalty": round(penalty, 1), "missing": missing}


def verdict(total: float, th: dict[str, float] | None = None) -> str:
    t = {"verify": VERIFY_AT, "watch": WATCH_AT, **(th or {})}
    if total >= t["verify"]:
        return "verify"
    if total >= t["watch"]:
        return "watch"
    return "drop"


def rank(candidates: list[dict[str, Any]], th: dict[str, float] | None = None) -> list[dict[str, Any]]:
    """Ordena candidatos {id, name, probe: {...contagens...}} pela nota da sonda, com o veredito de cada um."""
    out: list[dict[str, Any]] = []
    for c in candidates:
        s = score(c.get("probe") or {})
        out.append(
            {
                "id": c.get("id") or c.get("name"),
                "name": c.get("name"),
                "score": s["score"],
                "penalty": s["penalty"],
                "missing": s["missing"],
                "verdict": verdict(s["score"], th),
                "confidence": "low" if len(s["missing"]) >= 3 else "medium" if s["missing"] else "high",
            }
        )
    return sorted(out, key=lambda x: (-x["score"], str(x["name"])))


def validate_candidates(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, list) or not data:
        return ["candidates: lista não vazia de {id, name, probe}"]
    seen: set[str] = set()
    for i, c in enumerate(data):
        path = f"candidates[{i}]"
        if not isinstance(c, dict) or not str(c.get("name", "")).strip():
            errors.append(f"{path}: precisa de name")
            continue
        key = str(c.get("id") or c["name"]).casefold()
        if key in seen:
            errors.append(f"{path}: candidato duplicado ({key})")
        seen.add(key)
        probe = c.get("probe")
        if not isinstance(probe, dict):
            errors.append(f"{path}.probe: objeto com as contagens")
            continue
        for k, v in probe.items():
            if k not in HIT_KEYS:
                errors.append(f"{path}.probe.{k}: contagem desconhecida (use {', '.join(HIT_KEYS)})")
            elif isinstance(v, bool) or not isinstance(v, int) or v < 0:
                errors.append(f"{path}.probe.{k}: inteiro >= 0")
    return errors
