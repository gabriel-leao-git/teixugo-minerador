# 🦡 Teixugo Minerador

> 🇧🇷 [Leia em português](README.pt-BR.md)

A [Claude](https://claude.com) skill that **mines winning products for dropshipping from a pain point**. You say the pain ("remove dog hair") and how many products you want; it researches social media, search channels, suppliers and reviews, ranks the candidates by traction, and delivers a comparison report with proof.

## What you get, per product

Product · Pain · Segment · Target audience · Effectiveness · Engagement · **Link to the top-engagement post/ad** · Social networks ranked · Top search channel · Supplier · Country with most traction · Supplier country · First verified appearance · Comparison. Plus a side-by-side table and a verdict.

Reports come as **PDF, Word (.docx), Excel (.xlsx), .txt, .md or .html**, all generated from the same data, so the numbers never differ between formats.

## Honesty rules (the reason this skill exists)

- Every field is labeled **verified** (source + date), **estimated** (with the reasoning) or **unverified**. A script rejects a "verified" field without source and date.
- The top-engagement link must be a page the skill actually opened. `check-links` verifies the links.
- Without web access it runs in **hypothesis mode**: everything is marked unverified, and it says so up front.
- Search interest is **relative** (Google Trends style), not absolute volume; "first verified appearance" is **not** the launch date. The report says so.
- No promise of results.

## Ask it like this

```
Find 3 products that solve the same pain: removing dog hair. Rank by social media and search.
I want the supplier, country, effectiveness and the link of the post with the most engagement. PDF, please.
```

```
Vá à caça de 5 produtos para a dor "cozinha pequena" no mercado brasileiro. Relatório em Excel.
```

Trigger words: *mine, dig, find winning products, dropshipping product research* · *minerar, garimpar, escavar, vá à caça, comece a escavar, encontre*.

If your request is incomplete, the skill asks a few quick questions (a selection dialog in Claude Code, plain text elsewhere) and shows how to phrase a stronger request next time.

## Install

**Claude Code** (all your projects):

```bash
git clone https://github.com/gabriel-leao-git/teixugo-minerador.git ~/.claude/skills/teixugo-minerador
```

**Claude Code** (one project): clone into `<project>/.claude/skills/teixugo-minerador`.

The folder name must match the `name` in `SKILL.md`, and `SKILL.md` must be at its root. Other Claude apps that accept skills: upload the folder as a zip, following the app's skill instructions.

For Word, Excel and PDF output install the optional libraries (Markdown, text and HTML need nothing):

```bash
pip install -r requirements-optional.txt
```

## Scripts

Python 3.9+, standard library only. Run from the skill folder:

| Command | What it does |
|---|---|
| `python scripts/teixugo.py doctor` | Shows which formats are available |
| `… validate-brief BRIEF.json` | Validates the structured request and applies defaults |
| `… queries BRIEF.json` | Builds the search matrix (platform × language × country) |
| `… rank REPORT.json --write` | Ranks products by traction (social, search, reviews, ads) |
| `… economics --price 59.9 --cost 8 …` | Profit, break-even CPA and ROAS |
| `… validate REPORT.json` | Checks labels, sources, dates and required fields |
| `… check-links REPORT.json` | Confirms the links exist |
| `… render REPORT.json --format pdf,xlsx` | Generates md, txt, html, docx, xlsx or pdf |

Try it with the fictional example: `python scripts/teixugo.py render examples/report.example.pt-BR.json --format md,html`.

## Structure

```
teixugo-minerador/
├── SKILL.md              # workflow and rules Claude follows
├── references/           # briefing, fields & evidence, search strategy, sources, criteria, output
├── scripts/              # teixugo.py (CLI) and tx/ (modules)
├── examples/             # fictional brief and report
├── tests/                # unittest suite
└── .github/workflows/    # CI (Linux + Windows, Python 3.9 and 3.13)
```

## Limits

Quality depends on what the environment can reach: with web search and page fetching it verifies data; without them it only suggests hypotheses to validate. Some platforms block bots or require login, and the skill does not work around that: it records the limitation in the report. Paid spy tools are optional. Laws, taxes and platform rules change by country: confirm them before investing. This is a research tool, not financial advice.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md). Licensed under [MIT](LICENSE).
