"""Renderizadores de texto puro: Markdown, TXT e HTML (autocontido, sem dependências)."""
from __future__ import annotations

import html
import textwrap
from typing import Any

EMOJI = {"verified": "✅", "estimated": "🟡", "unverified": "⚪"}
COLOR = {"verified": "#1a7f37", "estimated": "#9a6700", "unverified": "#6e7781"}


def _md_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def to_md(blocks: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for b in blocks:
        t = b["t"]
        if t == "title":
            out += [f"# {b['text']}", ""]
        elif t == "banner":
            out += [f"> ⚠️ **{b['text']}**", ""]
        elif t == "meta":
            out += ["  \n".join(f"**{k}:** {v}" for k, v in b["items"]), ""]
        elif t == "h2":
            out += [f"## {b['text']}", ""]
        elif t == "h3":
            out += [f"### {b['text']}", ""]
        elif t == "p":
            out += [b["text"], ""]
        elif t == "bullets":
            out += [f"- {x}" for x in b["items"]] + [""]
        elif t == "ol":
            out += [f"{i}. {x}" for i, x in enumerate(b["items"], 1)] + [""]
        elif t == "note":
            out += [f"_{b['text']}_", ""]
        elif t == "field":
            value = f"[{b['value']}]({b['url']})" if b.get("url") else b["value"]
            line = f"- **{b['label']}:** {value}"
            if b.get("tag"):
                line += f" {EMOJI[b['tag']]}"
            if b.get("src"):
                line += f" _({b['src']})_"
            out.append(line)
        elif t == "table":
            out.append("| " + " | ".join(_md_cell(h) for h in b["headers"]) + " |")
            out.append("|" + "|".join("---" for _ in b["headers"]) + "|")
            for r in b["rows"]:
                out.append("| " + " | ".join(_md_cell(c) for c in r) + " |")
            out.append("")
    text = "\n".join(out)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.rstrip() + "\n"


def to_txt(blocks: list[dict[str, Any]]) -> str:
    out: list[str] = []
    prev_field = False
    for b in blocks:
        t = b["t"]
        if t != "field" and prev_field:
            out.append("")
        prev_field = t == "field"
        if t == "title":
            out += [b["text"].upper(), "=" * len(b["text"]), ""]
        elif t == "banner":
            out += [f"!!! {b['text']} !!!", ""]
        elif t == "meta":
            out += [f"{k}: {v}" for k, v in b["items"]] + [""]
        elif t == "h2":
            out += ["", b["text"].upper(), "-" * len(b["text"]), ""]
        elif t == "h3":
            out += [b["text"], "~" * len(b["text"])]
        elif t == "p":
            out += [textwrap.fill(b["text"], 100), ""]
        elif t == "bullets":
            out += [f"  * {x}" for x in b["items"]] + [""]
        elif t == "ol":
            out += [f"  {i}) {x}" for i, x in enumerate(b["items"], 1)] + [""]
        elif t == "note":
            out += [textwrap.fill(b["text"], 100), ""]
        elif t == "field":
            line = f"{b['label']}: {b['value']}"
            if b.get("tag"):
                line += f" [{b['tagtext'].upper()}]"
            if b.get("src"):
                line += f" ({b['src']})"
            out.append(line)
        elif t == "table":
            out.append(" | ".join(b["headers"]))
            out.append("-" * 40)
            for r in b["rows"]:
                out.append(" | ".join(str(c).replace("\n", " ") for c in r))
            out.append("")
    text = "\n".join(out)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.rstrip() + "\n"


CSS = """
:root{--bg:#fff;--fg:#1f2328;--muted:#656d76;--line:#d0d7de;--card:#f6f8fa;--warn:#fff8c5}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8d96a0;--line:#30363d;--card:#161b22;--warn:#3b2e00}}
*{box-sizing:border-box}body{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto}h1{font-size:1.7rem}h2{margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
h3{margin-top:1.4rem}.banner{background:var(--warn);border:1px solid var(--line);padding:10px 14px;border-radius:8px;font-weight:600}
.meta{color:var(--muted)}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 16px;margin:10px 0}
.f{margin:6px 0}.f b{font-weight:600}.tag{display:inline-block;padding:0 8px;border-radius:999px;font-size:.75rem;
color:#fff;margin-left:6px;vertical-align:1px}.src{color:var(--muted);font-size:.82rem}
table{border-collapse:collapse;width:100%;margin:10px 0;display:block;overflow-x:auto}th,td{border:1px solid var(--line);
padding:6px 10px;text-align:left;vertical-align:top;font-size:.88rem}th{background:var(--card)}
.note{color:var(--muted);font-size:.85rem}a{color:#0969da;word-break:break-all}
@media print{body{padding:0}.card{break-inside:avoid}}
"""


def to_html(blocks: list[dict[str, Any]], lang: str = "pt-BR") -> str:
    e = html.escape
    out: list[str] = []
    in_card = False

    def close_card() -> None:
        nonlocal in_card
        if in_card:
            out.append("</div>")
            in_card = False

    title = next((b["text"] for b in blocks if b["t"] == "title"), "Teixugo Minerador")
    for b in blocks:
        t = b["t"]
        if t != "field":
            close_card()
        if t == "title":
            out.append(f"<h1>{e(b['text'])}</h1>")
        elif t == "banner":
            out.append(f"<p class='banner'>⚠ {e(b['text'])}</p>")
        elif t == "meta":
            out.append("<p class='meta'>" + " · ".join(f"<b>{e(k)}:</b> {e(str(v))}" for k, v in b["items"]) + "</p>")
        elif t == "h2":
            out.append(f"<h2>{e(b['text'])}</h2>")
        elif t == "h3":
            out.append(f"<h3>{e(b['text'])}</h3>")
        elif t == "p":
            out.append(f"<p>{e(b['text'])}</p>")
        elif t == "bullets":
            out.append("<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in b["items"]) + "</ul>")
        elif t == "ol":
            out.append("<ol>" + "".join(f"<li>{e(str(x))}</li>" for x in b["items"]) + "</ol>")
        elif t == "note":
            out.append(f"<p class='note'>{e(b['text'])}</p>")
        elif t == "field":
            if not in_card:
                out.append("<div class='card'>")
                in_card = True
            value = f"<a href='{e(b['url'])}' rel='noopener noreferrer'>{e(b['value'])}</a>" if b.get("url") else e(str(b["value"]))
            tag = f"<span class='tag' style='background:{COLOR[b['tag']]}'>{e(b['tagtext'])}</span>" if b.get("tag") else ""
            src = f" <span class='src'>({e(b['src'])})</span>" if b.get("src") else ""
            out.append(f"<div class='f'><b>{e(b['label'])}:</b> {value}{tag}{src}</div>")
        elif t == "table":
            head = "".join(f"<th>{e(h)}</th>" for h in b["headers"])
            rows = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in b["rows"])
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
    close_card()
    body = "\n".join(out)
    return (
        f"<!doctype html>\n<html lang='{e(lang)}'>\n<head>\n<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>\n"
        f"<title>{e(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<main>\n{body}\n</main>\n</body>\n</html>\n"
    )
