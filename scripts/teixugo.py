#!/usr/bin/env python3
"""Teixugo Minerador - linha de comando.

Pedido e busca:
  doctor                       confere Python e bibliotecas opcionais
  brief-template               imprime um brief (pedido estruturado) de exemplo
  validate-brief  BRIEF.json   valida o pedido e mostra o que será usado (padrões aplicados)
  queries         BRIEF.json   matriz de buscas (plataforma x idioma x país), com texto pronto para busca web

Coleta de dados reais:
  fetch           URL          lê UMA página (título, avaliação, preço); respeita o robots.txt
  youtube         CONSULTA     vídeos e estatísticas pela API oficial (variável YOUTUBE_API_KEY)
  trends-import   ARQUIVO.csv  índice de busca a partir do CSV exportado do Google Trends

Relatório:
  validate        REPORT.json  valida o relatório (etiquetas, fontes, datas, métodos)
  rank            REPORT.json  ordena os produtos por tração (--write grava no arquivo)
  economics                    calcula lucro, CPA e ROAS de equilíbrio
  check-links     REPORT.json  verifica se os links do relatório existem
  render          REPORT.json  gera md/txt/html/docx/xlsx/pdf a partir do mesmo JSON

Sonar (histórico e alertas):
  watch add       ID BRIEF     cria uma vigilância
  watch update    ID REPORT    registra a leitura, mede aceleração e escreve o resumo (saída 10 = alerta)
  watch list | routine ID      lista as vigilâncias | gera o texto de uma rotina agendada

Somente biblioteca padrão, exceto docx/xlsx/pdf (opcionais, veja requirements-optional.txt).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tx import (  # noqa: E402
    __version__, blocks, economics, history, links, model, office, queries, render, score, trends, watch, webfetch, youtube,
)

EXIT_ALERT = watch.EXIT_ALERT

BRIEF_TEMPLATE: dict[str, Any] = {
    "kind": "pain",
    "language": "pt-BR",
    "pain": "remover pelo de cachorro",
    "quantity": 3,
    "market": ["BR"],
    "pain_terms": {
        "pt-BR": ["remover pelo de cachorro", "tirar pelo de cachorro do sofá"],
        "en": ["remove dog hair", "dog hair remover for furniture"],
    },
    "rank_by": ["social", "search"],
    "solution_variety": "different",
    "price_range": {"min": 20, "max": 80, "currency": "USD"},
    "include_economics": False,
    "output_formats": ["pdf"],
}


def _load(path: str) -> Any:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit(f"erro: arquivo não encontrado: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"erro: JSON inválido em {path}: {exc}")


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _report_issues(errors: list[str], warnings: list[str]) -> None:
    for w in warnings:
        print(f"aviso: {w}")
    for e in errors:
        print(f"ERRO:  {e}")


# --------------------------------------------------------------------------- comandos


def cmd_doctor(_: argparse.Namespace) -> int:
    print(f"teixugo-minerador {__version__} · Python {sys.version.split()[0]}")
    ok = sys.version_info >= (3, 9)
    print(f"  [{'ok' if ok else 'FALHA'}] Python >= 3.9")
    print("  [ok] md, txt, html (sem dependências)")
    for mod, pkg, fmt in (("docx", "python-docx", "docx"), ("openpyxl", "openpyxl", "xlsx"), ("reportlab", "reportlab", "pdf")):
        try:
            __import__(mod)
            print(f"  [ok] .{fmt} ({pkg})")
        except ImportError:
            print(f"  [--] .{fmt}: falta '{pkg}' -> pip install {pkg}")
    return 0 if ok else 1


def cmd_brief_template(_: argparse.Namespace) -> int:
    print(_dump(BRIEF_TEMPLATE))
    return 0


def cmd_validate_brief(a: argparse.Namespace) -> int:
    errors, warnings, normalized = model.validate_brief(_load(a.brief))
    _report_issues(errors, warnings)
    if errors:
        return 2
    print(_dump(normalized))
    return 0


def cmd_queries(a: argparse.Namespace) -> int:
    errors, warnings, brief = model.validate_brief(_load(a.brief))
    _report_issues(errors, warnings)
    if errors:
        return 2
    rows = queries.build(brief, per_term=a.per_term, limit=a.limit)
    if a.format == "json":
        print(_dump(rows))
    elif a.format == "searches":
        print("\n".join(queries.to_searches(rows)))
    else:
        print(queries.to_markdown(rows))
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    errors, warnings = model.validate_report(_load(a.report))
    _report_issues(errors, warnings)
    if errors:
        print(f"\n{len(errors)} erro(s), {len(warnings)} aviso(s): corrija antes de gerar o relatório.")
        return 2
    print(f"ok: relatório válido ({len(warnings)} aviso(s)).")
    return 0


def cmd_rank(a: argparse.Namespace) -> int:
    report = _load(a.report)
    errors, warnings = model.validate_report(report)
    _report_issues(errors, warnings)
    if errors:
        return 2
    by = a.by.split(",") if a.by else None
    score.apply(report, by)
    m = report["meta"]
    print(f"componentes usados: {', '.join(m['rank_used']) or '-'} · fora: {', '.join(m['rank_dropped']) or '-'} · confiança: {m['rank_confidence']}")
    for i, p in enumerate(report["products"], 1):
        print(f"{i}. {p['name']}: {p['traction_score']}/100  {p['score_components']}")
    if a.write:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(_dump(report) + "\n")
        print(f"gravado em {a.report}")
    return 0


def cmd_economics(a: argparse.Namespace) -> int:
    inputs = {
        "price": a.price, "cost": a.cost, "shipping": a.shipping, "tax": a.tax,
        "fee_pct": a.fee_pct, "fee_fixed": a.fee_fixed, "refund_pct": a.refund_pct,
    }
    try:
        res = economics.scenarios(inputs, a.drop)
    except ValueError as exc:
        print(f"erro: {exc}")
        return 2
    print(_dump(res))
    return 0


def cmd_check_links(a: argparse.Namespace) -> int:
    report = _load(a.report)
    if report.get("meta", {}).get("demo"):
        print("relatório de demonstração: links fictícios, nada a verificar.")
        return 0
    urls = links.collect_urls(report)
    if not urls:
        print("nenhum link encontrado.")
        return 0
    results = links.check_all(urls, a.timeout)
    bad = 0
    for r in results:
        print(f"[{r['result']:<12}] {r['status'] or '-':<4} {r['url']}")
        bad += r["result"] in ("broken", "error")
    inconclusive = sum(r["result"] == "inconclusive" for r in results)
    print(f"\n{len(results)} link(s): {len(results) - bad - inconclusive} ok, {bad} com problema, {inconclusive} inconclusivo(s) (site bloqueia robôs: abra à mão).")
    return 1 if (bad and a.strict) else 0


def cmd_render(a: argparse.Namespace) -> int:
    report = _load(a.report)
    errors, warnings = model.validate_report(report)
    _report_issues(errors, warnings)
    if errors:
        print("\nrelatório inválido: nada foi gerado. Corrija os erros acima.")
        return 2

    fmts = [f.strip().lower() for f in a.format.split(",") if f.strip()]
    bad = [f for f in fmts if f not in model.FORMATS]
    if bad:
        print(f"erro: formato(s) desconhecido(s): {', '.join(bad)}. Use: {', '.join(model.FORMATS)}")
        return 2

    meta = report["meta"]
    os.makedirs(a.out, exist_ok=True)
    stem = f"{model.slugify(model.scope_of(meta))}-{meta['generated_at']}"
    bl = blocks.build_blocks(report)
    status = 0
    for fmt in fmts:
        path = os.path.join(a.out, f"{stem}.{fmt}")
        try:
            if fmt == "md":
                _write(path, render.to_md(bl))
            elif fmt == "txt":
                _write(path, render.to_txt(bl))
            elif fmt == "html":
                _write(path, render.to_html(bl, meta["language"]))
            elif fmt == "docx":
                office.to_docx(bl, path)
            elif fmt == "xlsx":
                office.to_xlsx(report, path)
            elif fmt == "pdf":
                office.to_pdf(bl, path)
        except office.MissingDependency as exc:
            print(f"[pulado] .{fmt}: {exc}")
            status = 3
            continue
        print(f"[ok] {os.path.abspath(path)} ({os.path.getsize(path)} bytes)")
    return status


def cmd_fetch(a: argparse.Namespace) -> int:
    res = webfetch.fetch(a.url, a.timeout)
    print(_dump(res))
    return 1 if res["error"] else 0


def cmd_youtube(a: argparse.Namespace) -> int:
    try:
        videos = youtube.search_videos(
            a.query, os.environ.get("YOUTUBE_API_KEY", ""), region=a.region, language=a.lang,
            days=a.days or None, max_results=a.max,
        )
    except youtube.YouTubeError as exc:
        print(f"erro: {exc}")
        return 2
    print(_dump({"videos": videos, "evidence": youtube.as_evidence(videos)}))
    return 0


def cmd_trends_import(a: argparse.Namespace) -> int:
    try:
        with open(a.file, encoding="utf-8-sig") as fh:
            print(_dump(trends.parse(fh.read())))
    except (OSError, ValueError) as exc:
        print(f"erro: {exc}")
        return 2
    return 0


def cmd_watch_add(a: argparse.Namespace) -> int:
    errors, warnings, brief = model.validate_brief(_load(a.brief))
    _report_issues(errors, warnings)
    if errors:
        return 2
    th = {
        "min_growth": a.min_growth, "min_score": a.min_score, "min_days": a.min_days,
        "alert_on_new": not a.no_alert_on_new, "alert_on_moderate": a.alert_on_moderate,
    }
    channels = [c.strip() for c in a.channels.split(",") if c.strip()]
    try:
        entry = watch.add(a.store, a.id, brief, th, channels, a.schedule)
    except ValueError as exc:
        print(f"erro: {exc}")
        return 2
    print(f"vigilância '{a.id}' criada em {a.store}/watchlist.json")
    print(_dump({k: entry[k] for k in ("thresholds", "channels", "schedule")}))
    print(f"\nPróximos passos: rode a skill no tipo 'sonar', salve o relatório e execute:\n  python scripts/teixugo.py watch update {a.id} REPORT.json --store {a.store}")
    return 0


def cmd_watch_list(a: argparse.Namespace) -> int:
    watches = watch.list_watches(a.store)
    if not watches:
        print("nenhuma vigilância criada ainda.")
        return 0
    for wid, e in watches.items():
        print(f"{wid}: {model.scope_of(e['brief'])} · canais: {', '.join(e['channels'])} · {e['schedule']}")
    return 0


def cmd_watch_update(a: argparse.Namespace) -> int:
    report = _load(a.report)
    errors, warnings = model.validate_report(report)
    _report_issues(errors, warnings)
    if errors:
        print("\nrelatório inválido: nada foi registrado.")
        return 2
    try:
        res = watch.update(a.store, a.id, report, a.date)
    except (KeyError, ValueError) as exc:
        print(f"erro: {exc.args[0] if exc.args else exc}")
        return 2
    if not a.no_write_report:
        with open(a.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(_dump(report) + "\n")
    print(res["digest"])
    print(f"resumo gravado em {res['digest_path']}")
    if res["alert"]:
        print(f"ALERTA: há movimento acima dos limites (código de saída {EXIT_ALERT}).")
        return EXIT_ALERT
    print("sem alerta.")
    return 0


def cmd_watch_routine(a: argparse.Namespace) -> int:
    try:
        entry = watch.get(a.store, a.id)
    except KeyError as exc:
        print(f"erro: {exc.args[0]}")
        return 2
    print(watch.routine_prompt(a.id, entry, a.store))
    return 0


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="teixugo", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"teixugo-minerador {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="confere Python e bibliotecas opcionais").set_defaults(fn=cmd_doctor)
    sub.add_parser("brief-template", help="imprime um brief de exemplo").set_defaults(fn=cmd_brief_template)

    s = sub.add_parser("validate-brief", help="valida o pedido estruturado")
    s.add_argument("brief")
    s.set_defaults(fn=cmd_validate_brief)

    s = sub.add_parser("queries", help="gera a matriz de buscas")
    s.add_argument("brief")
    s.add_argument("--format", choices=("md", "json", "searches"), default="md",
                   help="searches = só os textos prontos para a busca web, um por linha")
    s.add_argument("--per-term", type=int, default=7, help="variações por termo (padrão 7)")
    s.add_argument("--limit", type=int, default=120, help="máximo de consultas (padrão 120)")
    s.set_defaults(fn=cmd_queries)

    s = sub.add_parser("validate", help="valida o relatório")
    s.add_argument("report")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("rank", help="ordena por tração")
    s.add_argument("report")
    s.add_argument("--by", help="componentes: social,search,reviews,ads (padrão: meta.rank_by ou social,search)")
    s.add_argument("--write", action="store_true", help="grava a ordem e as notas no arquivo")
    s.set_defaults(fn=cmd_rank)

    s = sub.add_parser("economics", help="lucro, CPA e ROAS de equilíbrio")
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--cost", type=float, required=True)
    s.add_argument("--shipping", type=float, default=0.0)
    s.add_argument("--tax", type=float, default=0.0)
    s.add_argument("--fee-pct", type=float, default=0.0, help="taxa do gateway/plataforma em %%")
    s.add_argument("--fee-fixed", type=float, default=0.0)
    s.add_argument("--refund-pct", type=float, default=0.0, help="reserva de reembolso em %%")
    s.add_argument("--drop", type=float, default=15.0, help="queda de preço do 2º cenário em %% (padrão 15)")
    s.set_defaults(fn=cmd_economics)

    s = sub.add_parser("check-links", help="verifica os links do relatório")
    s.add_argument("report")
    s.add_argument("--timeout", type=float, default=10.0)
    s.add_argument("--strict", action="store_true", help="sai com código 1 se houver link quebrado")
    s.set_defaults(fn=cmd_check_links)

    s = sub.add_parser("fetch", help="lê uma página (respeita o robots.txt)")
    s.add_argument("url")
    s.add_argument("--timeout", type=float, default=15.0)
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("youtube", help="vídeos e estatísticas pela API oficial (YOUTUBE_API_KEY)")
    s.add_argument("query")
    s.add_argument("--region", default="BR", help="código do país (padrão BR)")
    s.add_argument("--lang", default=None, help="idioma de relevância, ex.: pt")
    s.add_argument("--days", type=int, default=90, help="só vídeos dos últimos N dias (0 = sem filtro)")
    s.add_argument("--max", type=int, default=10)
    s.set_defaults(fn=cmd_youtube)

    s = sub.add_parser("trends-import", help="índice de busca a partir do CSV do Google Trends")
    s.add_argument("file")
    s.set_defaults(fn=cmd_trends_import)

    w = sub.add_parser("watch", help="vigilâncias do sonar (histórico e alertas)")
    wsub = w.add_subparsers(dest="wcmd", required=True)

    s = wsub.add_parser("add", help="cria uma vigilância")
    s.add_argument("id")
    s.add_argument("brief")
    s.add_argument("--store", default="teixugo-watch")
    s.add_argument("--min-growth", type=float, default=history.DEFAULT_THRESHOLDS["min_growth"], help="%% semanais para um componente contar como acelerando")
    s.add_argument("--min-score", type=float, default=history.DEFAULT_THRESHOLDS["min_score"], help="aceleração mínima (0-100) para alerta forte")
    s.add_argument("--min-days", type=int, default=history.DEFAULT_THRESHOLDS["min_days"], help="intervalo mínimo entre leituras, em dias")
    s.add_argument("--no-alert-on-new", action="store_true", help="não alertar só porque surgiu produto novo")
    s.add_argument("--alert-on-moderate", action="store_true", help="alertar também no nível moderado (mais sensível, mais ruído)")
    s.add_argument("--channels", default="email", help="email,calendar,push")
    s.add_argument("--schedule", default=None, help="texto livre, ex.: 'toda segunda, 8h'")
    s.set_defaults(fn=cmd_watch_add)

    s = wsub.add_parser("list", help="lista as vigilâncias")
    s.add_argument("--store", default="teixugo-watch")
    s.set_defaults(fn=cmd_watch_list)

    s = wsub.add_parser("update", help="registra a leitura e mede a aceleração (saída 10 = alerta)")
    s.add_argument("id")
    s.add_argument("report")
    s.add_argument("--store", default="teixugo-watch")
    s.add_argument("--date", default=None, help="AAAA-MM-DD (padrão: meta.generated_at do relatório)")
    s.add_argument("--no-write-report", action="store_true", help="não grava sonar/radar de volta no relatório")
    s.set_defaults(fn=cmd_watch_update)

    s = wsub.add_parser("routine", help="texto pronto para criar a rotina agendada")
    s.add_argument("id")
    s.add_argument("--store", default="teixugo-watch")
    s.set_defaults(fn=cmd_watch_routine)

    s = sub.add_parser("render", help="gera os arquivos do relatório")
    s.add_argument("report")
    s.add_argument("--format", default="md", help=f"um ou mais, separados por vírgula: {','.join(model.FORMATS)}")
    s.add_argument("--out", default="teixugo-relatorios", help="pasta de saída (padrão: ./teixugo-relatorios)")
    s.set_defaults(fn=cmd_render)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
