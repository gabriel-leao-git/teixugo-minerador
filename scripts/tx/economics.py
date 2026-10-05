"""Unit economics: lucro antes de anúncio, CPA e ROAS de equilíbrio.

Percentuais entram na escala 0-100. Tudo na mesma moeda.
"""
from __future__ import annotations

from typing import Any


def compute(
    price: float,
    cost: float,
    shipping: float = 0.0,
    tax: float = 0.0,
    fee_pct: float = 0.0,
    fee_fixed: float = 0.0,
    refund_pct: float = 0.0,
) -> dict[str, Any]:
    if price <= 0:
        raise ValueError("price deve ser maior que 0")
    total_cost = cost + shipping + tax
    fees = price * fee_pct / 100.0 + fee_fixed
    refund = price * refund_pct / 100.0
    profit = price - total_cost - fees - refund
    viable = profit > 0
    return {
        "price": round(price, 2),
        "total_cost": round(total_cost, 2),
        "fees": round(fees, 2),
        "refund_reserve": round(refund, 2),
        "profit_before_ads": round(profit, 2),
        "margin_pct": round(profit / price * 100.0, 1),
        "cpa_breakeven": round(profit, 2) if viable else 0.0,
        "roas_breakeven": round(price / profit, 2) if viable else None,
        "viable": viable,
    }


def from_inputs(inputs: dict[str, Any], price_scale: float = 1.0) -> dict[str, Any]:
    """Calcula a partir do dicionário `economics` do relatório (opcionalmente com preço reduzido)."""
    return compute(
        price=float(inputs["price"]) * price_scale,
        cost=float(inputs["cost"]),
        shipping=float(inputs.get("shipping", 0.0)),
        tax=float(inputs.get("tax", 0.0)),
        fee_pct=float(inputs.get("fee_pct", 0.0)),
        fee_fixed=float(inputs.get("fee_fixed", 0.0)),
        refund_pct=float(inputs.get("refund_pct", 0.0)),
    )


def scenarios(inputs: dict[str, Any], drop_pct: float = 15.0) -> dict[str, dict[str, Any]]:
    """Cenário base e cenário com o preço reduzido (concorrência forçando queda)."""
    return {
        "base": from_inputs(inputs),
        "drop": from_inputs(inputs, price_scale=1 - drop_pct / 100.0),
    }
