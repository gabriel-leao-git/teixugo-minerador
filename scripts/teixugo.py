#!/usr/bin/env python3
"""Teixugo Minerador - linha de comando.

Comandos:
  doctor                       confere Python e bibliotecas opcionais
  brief-template               imprime um brief (pedido estruturado) de exemplo
  validate-brief  BRIEF.json   valida o pedido e mostra o que será usado (padrões aplicados)
  queries         BRIEF.json   gera a matriz de buscas (plataforma x idioma x país)
  validate        REPORT.json  valida o relatório (etiquetas, fontes, datas, links)
  rank            REPORT.json  ordena os produtos por tração (--write grava no arquivo)
  economics                    calcula lucro, CPA e ROAS de equilíbrio
  check-links     REPORT.json  verifica se os links do relatório existem
  render          REPORT.json  gera md/txt/html/docx/xlsx/pdf a partir do mesmo JSON

Somente biblioteca padrão, exceto docx/xlsx/pdf (opcionais, veja requirements-optional.txt).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tx import __version__, blocks, economics, links, model, office, queries, render, score  # noqa: E402

BRIEF_TEMPLATE: dict[str, Any] = {
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
    print(_dump(rows) if a.format == "json" else queries.to_markdown(rows))
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
    stem = f"{model.slugify(meta['pain'])}-{meta['generated_at']}"
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
    s.add_argument("--format", choices=("md", "json"), default="md")
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
