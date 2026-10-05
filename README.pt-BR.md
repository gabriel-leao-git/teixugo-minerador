# 🦡 Teixugo Minerador

> 🇺🇸 [Read in English](README.md)

Uma skill do [Claude](https://claude.com) que **minera produtos para dropshipping pesquisando de verdade na web**. Você dá uma dor ("remover pelo de cachorro"), um nicho, ou pede o **sonar** (o que está acelerando). Ela acha candidatos, ranqueia por tração e entrega um relatório comparativo com prova, fornecedor, países e o link do post de maior engajamento.

## Instalação

```bash
npx github:gabriel-leao-git/teixugo-minerador
```

Copia a skill para `~/.claude/skills/teixugo-minerador` (todos os seus projetos). Precisa de Node 16+.

| Comando | O que faz |
|---|---|
| `npx github:gabriel-leao-git/teixugo-minerador --project` | Instala só no projeto atual (`./.claude/skills`) |
| `npx github:gabriel-leao-git/teixugo-minerador --dest <pasta>` | Instala em `<pasta>/teixugo-minerador` (pasta de skills de outro agente) |
| `npx github:gabriel-leao-git/teixugo-minerador --dry-run` | Mostra o que seria feito, sem alterar nada |
| `npx github:gabriel-leao-git/teixugo-minerador` (de novo) | Atualiza. Só os arquivos da skill são trocados; seus relatórios e vigilâncias ficam |
| `npx github:gabriel-leao-git/teixugo-minerador --uninstall` | Remove a skill (arquivos seus são mantidos) |

Sem Node: `git clone https://github.com/gabriel-leao-git/teixugo-minerador.git ~/.claude/skills/teixugo-minerador`.

Para gerar Word, Excel e PDF, instale as bibliotecas opcionais (Markdown, texto e HTML não precisam de nada): `pip install -r requirements-optional.txt`.

## O que você recebe, por produto

Produto · Dor · Segmento · Público-alvo · Efetividade · Engajamento · **Link do post/anúncio de maior engajamento** · Redes sociais em ordem · Canal com maior busca · Fornecedor · País de maior tração · País do fornecedor · Primeira aparição verificada · Comparação. Mais uma tabela lado a lado e um veredito.

O relatório sai em **PDF, Word (.docx), Excel (.xlsx), .txt, .md ou .html**, todos gerados dos mesmos dados, então os números nunca divergem entre formatos.

## Três jeitos de pedir

| Tipo | Exemplo |
|---|---|
| **Dor** | `Quero 3 produtos que resolvam a mesma dor: remover pelo de cachorro. Ranqueie por redes sociais e busca. Em PDF.` |
| **Nicho** | `Vá à caça de 5 produtos de organização de casa para o mercado brasileiro. Relatório em Excel.` |
| **Sonar** | `Sonar: o que está acelerando em produtos pet no Brasil?` (mede o crescimento entre duas leituras) |

Se o pedido estiver incompleto, a skill faz algumas perguntas rápidas (caixa de seleção no Claude Code, texto nos demais) e mostra como escrever um pedido mais forte da próxima vez.

## Ela pesquisa a web de verdade e diz o que não conseguiu ler

- A **busca na web com `site:`** acha produtos e links reais no TikTok, YouTube, Instagram, Pinterest, Reddit e marketplaces. Os **números** vêm da melhor fonte disponível: leitura de página, API oficial do YouTube (`YOUTUBE_API_KEY`), o CSV do Google Trends que você exporta, uma ferramenta de navegador ou dados que você fornece.
- Todo campo é **verificado** (fonte + data + como foi obtido), **estimado** (com o raciocínio) ou **não verificado**. Um script recusa um campo "verificado" sem fonte e data.
- **Ela respeita as restrições dos sites.** `robots.txt` (inclusive regras contra agentes de IA), HTTP 403/429/503, captcha e login contam como "não": a skill não contorna. Várias plataformas grandes bloqueiam leitura automática, então ela recorre a outras fontes e registra a limitação no relatório. Veja [references/acesso-web.md](references/acesso-web.md) para o que funcionou e o que não.
- Interesse de busca é **relativo** (estilo Google Trends), "primeira aparição verificada" **não** é a data de lançamento, e aceleração **não** é previsão. Nenhuma promessa de resultado.

## Sonar e alertas

O sonar compara leituras ao longo do tempo: engajamento, busca, avaliações e número de anunciantes. A primeira leitura é a linha de base; a aceleração aparece da segunda em diante (3 a 7 dias de intervalo é um bom ritmo).

```bash
python scripts/teixugo.py watch add pets brief.json --channels email,calendar
python scripts/teixugo.py watch update pets report.json      # código de saída 10 = alerta
python scripts/teixugo.py watch routine pets                 # texto para uma rotina agendada
```

O agendamento e o envio (rotinas na nuvem, Gmail, Google Calendar) usam os conectores que o seu ambiente autorizou; a skill nunca finge que enviou. Detalhes em [references/sonar-e-historico.md](references/sonar-e-historico.md).

## Scripts

Python 3.9+, só biblioteca padrão. Use o caminho da pasta da skill e rode a partir da sua pasta de trabalho:

| Comando | O que faz |
|---|---|
| `teixugo.py doctor` | Mostra quais formatos estão disponíveis |
| `validate-brief BRIEF.json` | Valida o pedido estruturado e aplica os padrões |
| `queries BRIEF.json [--format searches]` | Matriz de buscas; `searches` imprime os textos prontos para a busca na web |
| `fetch URL` | Lê uma página (título, preço, nota); recusa se o `robots.txt` proíbe |
| `youtube "consulta"` | Views, curtidas e comentários pela API oficial |
| `trends-import ARQUIVO.csv` | Índice de busca a partir do CSV exportado do Google Trends |
| `rank REPORT.json --write` | Ordena os produtos por tração |
| `economics --price 59.9 --cost 8 …` | Lucro, CPA e ROAS de equilíbrio |
| `validate REPORT.json` | Confere etiquetas, fontes, datas, métodos e campos obrigatórios |
| `check-links REPORT.json` | Confirma que os links existem |
| `render REPORT.json --format pdf,xlsx` | Gera md, txt, html, docx, xlsx ou pdf |
| `watch add / update / list / routine` | Histórico e alertas do sonar |

Experimente com o exemplo fictício: `python scripts/teixugo.py render examples/report.example.pt-BR.json --format md,html`.

## Estrutura

```text
teixugo-minerador/
├── SKILL.md              # fluxo e regras que o Claude segue
├── references/           # briefing, campos e evidências, acesso à web, estratégia de busca, sonar, critérios, saída
├── scripts/              # teixugo.py (CLI) e tx/ (módulos)
├── examples/             # brief e relatório fictícios
├── bin/install.js        # o instalador do npx
├── tests/                # testes (unittest)
└── .github/workflows/    # CI (Linux + Windows, Python 3.9 e 3.13)
```

## Limites

A qualidade depende do que o ambiente alcança: com busca na web e leitura de páginas ela verifica o que dá; sem isso, só sugere hipóteses para você validar. Ferramentas pagas de espionagem são opcionais e nunca obrigatórias. Leis, tributos e regras de plataforma mudam de país para país: confirme antes de investir. É uma ferramenta de pesquisa, não consultoria financeira.

## Contribuir e licença

Veja [CONTRIBUTING.md](CONTRIBUTING.md) e [CHANGELOG.md](CHANGELOG.md). Licença [MIT](LICENSE).
