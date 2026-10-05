# 🦡 Teixugo Minerador

> 🇺🇸 [Read in English](README.md)

Uma skill do [Claude](https://claude.com) que **minera produtos vencedores para dropshipping a partir de uma dor**. Você diz a dor ("remover pelo de cachorro") e quantos produtos quer; ela pesquisa redes sociais, canais de busca, fornecedores e avaliações, ranqueia os candidatos por tração e entrega um relatório comparativo com prova.

## O que você recebe, por produto

Produto · Dor · Segmento · Público-alvo · Efetividade · Engajamento · **Link do post/anúncio de maior engajamento** · Redes sociais em ordem · Canal com maior busca · Fornecedor · País de maior tração · País do fornecedor · Primeira aparição verificada · Comparação. Mais uma tabela lado a lado e um veredito.

O relatório sai em **PDF, Word (.docx), Excel (.xlsx), .txt, .md ou .html**, todos gerados dos mesmos dados, então os números nunca divergem entre formatos.

## Regras de honestidade (a razão de existir da skill)

- Todo campo é **verificado** (fonte + data), **estimado** (com o raciocínio) ou **não verificado**. Um script recusa um campo "verificado" sem fonte e data.
- O link de maior engajamento tem de ser uma página que a skill realmente abriu. O `check-links` confere os links.
- Sem acesso à web ela roda em **modo hipótese**: tudo marcado como não verificado, e ela avisa logo no começo.
- Interesse de busca é **relativo** (estilo Google Trends), não volume absoluto; "primeira aparição verificada" **não** é a data de lançamento. O relatório diz isso.
- Nenhuma promessa de resultado.

## Como pedir

```
Quero que você busque 3 produtos que resolvam a mesma dor: remover pelo de cachorro. Ranqueie por redes sociais e busca.
Traga fornecedor, país, efetividade e o link do post com maior engajamento. Em PDF.
```

```
Vá à caça de 5 produtos para a dor "cozinha pequena" no mercado brasileiro. Relatório em Excel.
```

Palavras que acionam: *minerar, garimpar, escavar, vá à caça, comece a escavar, encontre* · *mine, dig, find winning products*.

Se o pedido estiver incompleto, a skill faz algumas perguntas rápidas (caixa de seleção no Claude Code, texto nos demais) e mostra como escrever um pedido mais forte da próxima vez.

## Instalação

**Claude Code** (todos os seus projetos):

```bash
git clone https://github.com/gabriel-leao-git/teixugo-minerador.git ~/.claude/skills/teixugo-minerador
```

**Claude Code** (um projeto só): clone em `<projeto>/.claude/skills/teixugo-minerador`.

O nome da pasta precisa ser igual ao `name` do `SKILL.md`, e o `SKILL.md` precisa ficar na raiz dela. Em outros apps do Claude que aceitam skills, envie a pasta compactada em zip seguindo as instruções do app.

Para gerar Word, Excel e PDF, instale as bibliotecas opcionais (Markdown, texto e HTML não precisam de nada):

```bash
pip install -r requirements-optional.txt
```

## Scripts

Python 3.9+, só biblioteca padrão. Rode a partir da pasta da skill:

| Comando | O que faz |
|---|---|
| `python scripts/teixugo.py doctor` | Mostra quais formatos estão disponíveis |
| `… validate-brief BRIEF.json` | Valida o pedido estruturado e aplica os padrões |
| `… queries BRIEF.json` | Monta a matriz de buscas (plataforma × idioma × país) |
| `… rank REPORT.json --write` | Ordena por tração (redes sociais, busca, avaliações, anúncios) |
| `… economics --price 59.9 --cost 8 …` | Lucro, CPA e ROAS de equilíbrio |
| `… validate REPORT.json` | Confere etiquetas, fontes, datas e campos obrigatórios |
| `… check-links REPORT.json` | Confirma que os links existem |
| `… render REPORT.json --format pdf,xlsx` | Gera md, txt, html, docx, xlsx ou pdf |

Experimente com o exemplo fictício: `python scripts/teixugo.py render examples/report.example.pt-BR.json --format md,html`.

## Estrutura

```
teixugo-minerador/
├── SKILL.md              # fluxo e regras que o Claude segue
├── references/           # briefing, campos e evidências, estratégia de busca, fontes, critérios, saída
├── scripts/              # teixugo.py (CLI) e tx/ (módulos)
├── examples/             # brief e relatório fictícios
├── tests/                # testes (unittest)
└── .github/workflows/    # CI (Linux + Windows, Python 3.9 e 3.13)
```

## Limites

A qualidade depende do que o ambiente alcança: com busca na web e leitura de páginas ela verifica os dados; sem isso, só sugere hipóteses para você validar. Algumas plataformas bloqueiam robôs ou exigem login, e a skill não contorna isso: registra a limitação no relatório. Ferramentas pagas de espionagem são opcionais. Leis, tributos e regras de plataforma mudam de país para país: confirme antes de investir. É uma ferramenta de pesquisa, não consultoria financeira.

## Contribuir e licença

Veja [CONTRIBUTING.md](CONTRIBUTING.md) e [CHANGELOG.md](CHANGELOG.md). Licença [MIT](LICENSE).
