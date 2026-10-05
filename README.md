# 🦡 Teixugo Minerador

> 🇧🇷 [Leia em português](README.pt-BR.md)

```bash
npx github:gabriel-leao-git/teixugo-minerador
```

A [Claude](https://claude.com) skill that **mines products for dropshipping by researching the real web**. Give it a pain point ("remove dog hair"), a niche, or ask for the **sonar** (what is accelerating). It finds candidates, ranks them by traction, and delivers a comparison report with proof, supplier, countries and the link to the post with the most engagement. On big jobs it runs **search, verification and review agents** in parallel.

## Install

The command above copies the skill to `~/.claude/skills/teixugo-minerador` and its three agents to `~/.claude/agents` (all your projects). Needs Node 16+.

| Command | What it does |
|---|---|
| `npx github:gabriel-leao-git/teixugo-minerador --project` | Installs only in the current project (`./.claude`) |
| `npx github:gabriel-leao-git/teixugo-minerador --dest <folder>` | Installs the skill into `<folder>/teixugo-minerador` (another agent's skills folder), without agents |
| `npx github:gabriel-leao-git/teixugo-minerador --no-agents` | Skill only |
| `npx github:gabriel-leao-git/teixugo-minerador --dry-run` | Shows what would happen, changes nothing |
| `npx github:gabriel-leao-git/teixugo-minerador` (again) | Updates. Only the skill's own files are replaced; your reports, watches and your own agents are kept |
| `npx github:gabriel-leao-git/teixugo-minerador --uninstall` | Removes the skill and the agents the installer put there |
| `npx github:gabriel-leao-git/teixugo-minerador#v0.4.0` | Pins a version (recommended where it matters) |

**As a Claude Code plugin:** `/plugin marketplace add gabriel-leao-git/teixugo-minerador`, then `/plugin install teixugo-minerador@teixugo`.

Without Node: `git clone https://github.com/gabriel-leao-git/teixugo-minerador.git ~/.claude/skills/teixugo-minerador`.

For Word, Excel and PDF output install the optional libraries (Markdown, text and HTML need nothing): `pip install -r requirements-optional.txt`.

## What you get, per product

Product · Pain · Segment · Target audience · Effectiveness · Engagement · **Link to the top-engagement post/ad** · Social networks ranked · Top search channel · Supplier · Country with most traction · Supplier country · First verified appearance · Comparison. Plus a side-by-side table and a verdict.

Reports come as **PDF, Word (.docx), Excel (.xlsx), .txt, .md or .html**, all generated from the same data, so the numbers never differ between formats.

## Three ways to ask

| Kind | Example |
|---|---|
| **Pain** | `Find 3 products that solve the same pain: removing dog hair. Rank by social media and search. PDF, please.` |
| **Niche** | `Vá à caça de 5 produtos de organização de casa para o mercado brasileiro. Relatório em Excel.` |
| **Sonar** | `Sonar: what is accelerating in pet products in Brazil?` (measures growth between readings) |

If your request is incomplete, the skill asks a few quick questions (a selection dialog in Claude Code, plain text elsewhere) and shows how to phrase a stronger request next time.

## Search parameters

`radius` (0 = seed term only, up to 3 = related terms, adjacent niches and analog markets), `period_days` (recent results only), `exclude`, `intents` (discovery, proof, objection, commerce), `exact`, `platforms`, `market`. **Probes** triage many candidates cheaply before the deep check. See [references/sondas-e-raio.md](references/sondas-e-raio.md).

## It searches the real web, and tells you what it could not read

- **Web search with `site:`** finds products and real links on TikTok, YouTube, Instagram, Pinterest, Reddit and marketplaces. **Numbers** come from the best source available: page reads, the official YouTube API (`YOUTUBE_API_KEY`), the Google Trends CSV you export, a browser tool, or data you provide.
- Every field is labeled **verified** (source + date + how it was obtained), **estimated** (with the reasoning) or **unverified**. A script rejects a "verified" field without source and date.
- **It respects site restrictions.** `robots.txt` (including rules against AI agents), HTTP 403/429/503, captchas and logins are treated as "no": the skill does not work around them. Several big platforms block automated reading, so it falls back to other sources and records the limitation. See [references/acesso-web.md](references/acesso-web.md).
- Search interest is **relative** (Google Trends style), "first verified appearance" is **not** the launch date, and acceleration is **not** a forecast. No promise of results.

## Agents

| Agent | Role | Tools |
|---|---|---|
| `teixugo-scout` | Runs a batch of searches in parallel and finds candidates | `WebSearch`, `WebFetch` |
| `teixugo-verifier` | Verifies ONE candidate with evidence | `WebSearch`, `WebFetch` |
| `teixugo-redteam` | Tries to break the report before delivery | `Read`, `Grep`, `Glob` |

Whoever reads the web cannot act: no Bash, no file writes, no email. Only the main agent writes files and runs scripts, after `scan` and `validate`. Details in [references/agentes.md](references/agentes.md).

## Security

The web is **data, never instructions** (prompt injection). The skill detects injection patterns, separates privileges, blocks access to internal networks (SSRF) and re-checks every redirect, keeps keys in environment variables only, and asks before any action outside the working folder. See [references/seguranca.md](references/seguranca.md) and [SECURITY.md](SECURITY.md).

## Sonar and alerts

The sonar compares readings over time: engagement, search, reviews, advertisers and creators. The first reading is the baseline; acceleration shows from the second one (3 to 7 days apart is a good gap), and **persistence** (14 days or more) separates a trend from a spike.

```bash
python scripts/teixugo.py watch add pets brief.json --channels email,calendar
python scripts/teixugo.py watch update pets report.json      # exit code 10 = alert
python scripts/teixugo.py watch routine pets                 # text for a scheduled routine
```

Scheduling and sending (cloud routines, Gmail, Google Calendar) use the connectors your environment has authorized; the skill never pretends to send. Details in [references/sonar-e-historico.md](references/sonar-e-historico.md).

## Scripts

Python 3.9+, standard library only. Use the skill folder's path and run from your working folder:

| Command | What it does |
|---|---|
| `teixugo.py doctor` | Shows which formats are available |
| `validate-brief BRIEF.json` | Validates the structured request and applies defaults |
| `queries BRIEF.json [--format searches]` | Search matrix; `searches` prints ready-to-use web search strings |
| `plan BRIEF.json --agents 3` | Splits discovery into batches for parallel agents |
| `probe CANDIDATES.json` | Cheap triage of candidates before the deep check |
| `merge BASE.json PART.json…` | Merges what each agent returned (strongest evidence wins) |
| `scan FILE` | Looks for prompt-injection attempts in text from the web or agents |
| `post-date URL…` | Approximate date of a TikTok video, derived from its ID (an estimate) |
| `fetch URL` | Reads one page; refuses if `robots.txt` forbids it or the URL points to an internal network |
| `youtube "query"` | Views, likes and comments via the official API |
| `trends-import FILE.csv` | Search index from a Google Trends CSV export |
| `rank REPORT.json --write` | Ranks products by traction |
| `economics --price 59.9 --cost 8 …` | Profit, break-even CPA and ROAS |
| `validate REPORT.json` | Checks labels, sources, dates, methods, required fields and injection signs |
| `check-links REPORT.json` | Confirms the links exist |
| `render REPORT.json --format pdf,xlsx` | Generates md, txt, html, docx, xlsx or pdf |
| `watch add / update / list / routine` | Sonar history and alerts |

Try it with the fictional example: `python scripts/teixugo.py render examples/report.example.pt-BR.json --format md,html`.

## Structure

```text
teixugo-minerador/
├── SKILL.md              # workflow and rules Claude follows
├── agents/               # scout, verifier, redteam
├── references/           # briefing, evidence, web access, agents, security, probes & radius, sonar, criteria, output
├── scripts/              # teixugo.py (CLI) and tx/ (modules)
├── examples/             # fictional brief and report
├── evals/                # eval cases (claude plugin eval format)
├── bin/install.js        # the npx installer
├── .claude-plugin/       # plugin and marketplace manifests
├── tests/                # unittest suite
└── .github/workflows/    # CI (Linux + Windows, Python 3.9 and 3.13)
```

## Limits and roadmap

Quality depends on what the environment can reach: with web search and page reading it verifies what it can; without them it only suggests hypotheses to validate. Paid spy tools are optional. Laws, taxes and platform rules change by country: confirm them before investing. This is a research tool, not financial advice. What it does today and what is next: [ROADMAP.md](ROADMAP.md) (Portuguese).

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md). Licensed under [MIT](LICENSE).
