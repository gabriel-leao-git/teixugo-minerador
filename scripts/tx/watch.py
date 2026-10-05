"""Vigilâncias (watch): pedidos que rodam de tempos em tempos e só avisam quando algo muda.

Estrutura da pasta de dados (padrão `teixugo-watch/`):

    watchlist.json            quais vigilâncias existem, limites e canais de aviso
    history/<id>.json         retratos de cada leitura
    alerts/<id>-<data>.md     resumo de cada leitura, pronto para e-mail, agenda ou notificação

O agendamento em si (cron, rotina na nuvem) e o envio (e-mail, agenda) ficam FORA deste módulo:
ele só registra, compara e escreve o resumo. O código de saída 10 do comando `watch update`
significa "há alerta".
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from typing import Any

from . import history
from .model import is_date, scope_of, slugify

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
CHANNELS = ("email", "calendar", "push")
EXIT_ALERT = 10

T = {
    "pt-BR": {
        "title": "Sonar — {scope} ({date})",
        "compared": "Comparado com a leitura de {prev} ({days} dias).",
        "baseline": "Primeira leitura: linha de base registrada. A aceleração aparece a partir da próxima leitura (intervalo recomendado: 3 a 7 dias).",
        "accel": "Em aceleração",
        "new": "Novos no radar",
        "gone": "Não apareceram nesta leitura",
        "none": "Nenhum produto passou dos limites desta vez.",
        "levels": {"strong": "forte", "moderate": "moderada"},
        "score": "aceleração",
        "window": "janela",
        "wk": "/sem",
        "comp": {"social": "engajamento", "search": "busca", "reviews": "avaliações", "ads": "anunciantes"},
        "caveat": "Aceleração não é previsão: é crescimento medido entre duas leituras. Confira os links no relatório antes de agir.",
    },
    "en": {
        "title": "Sonar — {scope} ({date})",
        "compared": "Compared with the {prev} reading ({days} days).",
        "baseline": "First reading: baseline recorded. Acceleration shows up from the next reading (recommended gap: 3 to 7 days).",
        "accel": "Accelerating",
        "new": "New on the radar",
        "gone": "Did not show up in this reading",
        "none": "No product crossed the thresholds this time.",
        "levels": {"strong": "strong", "moderate": "moderate"},
        "score": "acceleration",
        "window": "window",
        "wk": "/wk",
        "comp": {"social": "engagement", "search": "search", "reviews": "reviews", "ads": "advertisers"},
        "caveat": "Acceleration is not a forecast: it is growth measured between two readings. Check the report links before acting.",
    },
}


def _paths(store: str) -> dict[str, str]:
    return {
        "watchlist": os.path.join(store, "watchlist.json"),
        "history": os.path.join(store, "history"),
        "alerts": os.path.join(store, "alerts"),
    }


def _load_watchlist(store: str) -> dict[str, Any]:
    path = _paths(store)["watchlist"]
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        data.setdefault("watches", {})
        return data
    return {"watches": {}}


def _save_watchlist(store: str, data: dict[str, Any]) -> None:
    os.makedirs(store, exist_ok=True)
    with open(_paths(store)["watchlist"], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def add(
    store: str,
    wid: str,
    brief: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
    channels: list[str] | None = None,
    schedule: str | None = None,
) -> dict[str, Any]:
    if not ID_RE.match(wid):
        raise ValueError("id da vigilância: kebab-case (letras minúsculas, números e hífens)")
    bad = [c for c in (channels or []) if c not in CHANNELS]
    if bad:
        raise ValueError(f"canais desconhecidos: {', '.join(bad)}. Use: {', '.join(CHANNELS)}")
    data = _load_watchlist(store)
    if wid in data["watches"]:
        raise ValueError(f"já existe uma vigilância com o id '{wid}'")
    entry = {
        "brief": brief,
        "thresholds": {**history.DEFAULT_THRESHOLDS, **(thresholds or {})},
        "channels": channels or ["email"],
        "schedule": schedule or "a cada 3 a 7 dias",
        "created": date.today().isoformat(),
    }
    data["watches"][wid] = entry
    _save_watchlist(store, data)
    return entry


def list_watches(store: str) -> dict[str, Any]:
    return _load_watchlist(store)["watches"]


def get(store: str, wid: str) -> dict[str, Any]:
    watches = _load_watchlist(store)["watches"]
    if wid not in watches:
        raise KeyError(f"vigilância '{wid}' não existe. Crie com: watch add {wid} BRIEF.json")
    return watches[wid]


def build_digest(wid: str, entry: dict[str, Any], comparison: dict[str, Any], report: dict[str, Any]) -> str:
    lang = report["meta"].get("language", "pt-BR")
    s = T.get(lang, T["pt-BR"])
    lines = [f"# {s['title'].format(scope=scope_of(report['meta']), date=comparison['taken_at'])}", ""]
    if comparison["baseline"]:
        lines += [s["baseline"], ""]
    else:
        lines += [s["compared"].format(prev=comparison["compared_to"], days=comparison["days"]), ""]
        movers = sorted(
            (i for i in comparison["items"].values() if i["level"] in ("strong", "moderate")),
            key=lambda i: (-history.LEVEL_RANK[i["level"]], -(i["acceleration"] or 0)),
        )
        if movers:
            lines += [f"## {s['accel']}", ""]
            for i in movers:
                parts = [f"{s['comp'][c]} {g:+.0f}%{s['wk']}" for c, g in i["growth"].items() if g is not None]
                extra = f" · {s['window']} {i['window']}" if i["window"] is not None else ""
                lines.append(f"- **{i['name']}** — {s['levels'][i['level']]} — {s['score']} {i['acceleration']}/100 · {' · '.join(parts)}{extra}")
            lines.append("")
        if comparison["new"]:
            lines += [f"## {s['new']}", ""] + [f"- {n['name']}" for n in comparison["new"]] + [""]
        if comparison["gone"]:
            lines += [f"## {s['gone']}", ""] + [f"- {g['name']}" for g in comparison["gone"]] + [""]
        if not movers and not comparison["new"]:
            lines += [s["none"], ""]
    lines += [f"_{s['caveat']}_", ""]
    return "\n".join(lines)


def update(store: str, wid: str, report: dict[str, Any], taken_at: str | None = None) -> dict[str, Any]:
    """Registra a leitura, compara com a anterior e escreve o resumo. Modifica `report` (campos sonar e radar)."""
    entry = get(store, wid)
    if taken_at:
        if not is_date(taken_at):
            raise ValueError("data: use AAAA-MM-DD")
        report["meta"]["generated_at"] = taken_at
    paths = _paths(store)
    hist_path = os.path.join(paths["history"], f"{wid}.json")
    hist = history.load(hist_path)
    snap = history.make_snapshot(report)
    comparison = history.compare(history.previous(hist, snap["taken_at"]), snap, entry["thresholds"])
    history.save(hist_path, history.add_snapshot(hist, snap))
    history.apply_to_report(report, comparison)
    digest = build_digest(wid, entry, comparison, report)
    os.makedirs(paths["alerts"], exist_ok=True)
    digest_path = os.path.join(paths["alerts"], f"{wid}-{snap['taken_at']}.md")
    with open(digest_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(digest)
    return {"comparison": comparison, "alert": history.has_alert(comparison), "digest": digest, "digest_path": digest_path}


def routine_prompt(wid: str, entry: dict[str, Any], store: str) -> str:
    """Texto pronto para criar uma rotina agendada (ex.: com /schedule) que roda este radar."""
    brief = json.dumps(entry["brief"], ensure_ascii=False)
    chans = ", ".join(entry["channels"])
    return (
        f"Rotina Teixugo — vigilância '{wid}' ({entry['schedule']})\n\n"
        "1. Use a skill teixugo-minerador no tipo de busca 'sonar' com este pedido (não pergunte nada, use os padrões):\n"
        f"   {brief}\n"
        "2. Pesquise na web de verdade (busca com site:, leitura de páginas). Preencha os sinais de cada produto: "
        "engagement, search_index, reviews, advertisers. Defina um `id` estável (kebab-case) para cada produto, "
        "o mesmo em todas as leituras. Salve em teixugo-watch/runs/" + wid + "-AAAA-MM-DD.json (AAAA-MM-DD = hoje).\n"
        f"3. Rode: python scripts/teixugo.py watch update {wid} <arquivo do passo 2> --store {store}\n"
        f"4. Se o código de saída for {EXIT_ALERT} (há alerta): envie o resumo de {store}/alerts/{wid}-<data>.md pelos canais "
        f"configurados ({chans}), usando os conectores disponíveis (e-mail, Google Calendar) ou notificação. "
        "Se um conector não estiver autorizado, diga qual faltou e não invente o envio.\n"
        "5. Se o código for 0, não envie nada.\n"
        f"6. Grave a pasta {store}/ no repositório da rotina (commit) para o histórico persistir entre execuções.\n\n"
        "Regras: nunca invente dado ou link; marque o que não conseguiu verificar; "
        "respeite o robots.txt e não contorne bloqueios."
    )


def slug_for(scope: str) -> str:
    """Sugestão de id de vigilância a partir do assunto."""
    return slugify(scope, 40)
