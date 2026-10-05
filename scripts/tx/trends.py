"""Importa o CSV exportado do Google Trends ("Interesse ao longo do tempo") e calcula o índice de busca.

Exportar é um passo manual do usuário (botão de download na página do Trends), mas é a forma
estável e legítima de obter o dado. Coloque os termos que quer comparar **no mesmo gráfico**,
com o mesmo período e país: o índice (0-100) só é comparável dentro de um mesmo gráfico.
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any

_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
_SUFFIX = re.compile(r"\s*:\s*\([^)]*\)\s*$")


def _num(cell: str) -> float | None:
    cell = cell.strip()
    if not cell:
        return None
    if cell.startswith("<"):  # "<1" = menos de 1
        return 0.5
    try:
        return float(cell.replace(",", "."))
    except ValueError:
        return None


def parse(text: str) -> dict[str, Any]:
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    head = None
    for i, row in enumerate(rows[:-1]):
        if len(row) >= 2 and rows[i + 1] and _DATE.match(rows[i + 1][0].strip()):
            head = i
            break
    if head is None:
        raise ValueError("não achei a tabela de dados: exporte 'Interesse ao longo do tempo' do Google Trends (CSV)")
    terms = [_SUFFIX.sub("", c).strip() for c in rows[head][1:]]
    series: dict[str, list[tuple[str, float]]] = {t: [] for t in terms}
    for row in rows[head + 1:]:
        if not row or not _DATE.match(row[0].strip()):
            continue
        for term, cell in zip(terms, row[1:]):
            v = _num(cell)
            if v is not None:
                series[term].append((row[0].strip(), v))
    all_dates = sorted({d for pts in series.values() for d, _ in pts})
    out: list[dict[str, Any]] = []
    for term, pts in series.items():
        if not pts:
            continue
        vals = [v for _, v in pts]
        third = max(1, len(vals) // 3)
        first, last = sum(vals[:third]) / third, sum(vals[-third:]) / third
        peak = max(pts, key=lambda x: x[1])
        out.append(
            {
                "term": term,
                "points": len(vals),
                "mean": round(sum(vals) / len(vals), 1),
                "peak": peak[1],
                "peak_date": peak[0],
                "recent": round(last, 1),  # média do último terço do período
                "change_pct": round((last - first) / first * 100.0, 1) if first > 0 else None,  # último terço vs primeiro
                "recent_vs_peak_pct": round(last / peak[1] * 100.0, 1) if peak[1] else None,
            }
        )
    return {"terms": out, "period": [all_dates[0], all_dates[-1]] if all_dates else None}
