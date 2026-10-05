# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [0.2.0] - 2026-10-05

### Adicionado
- Fluxo **dirigido por dor**: o usuário diz a dor e quantos produtos quer; a skill devolve um formato de saída fixo por produto (produto, dor, segmento, público-alvo, efetividade, engajamento, link, redes, canal de busca, fornecedor, países, primeira aparição, comparação) e uma tabela comparativa.
- **Questionário de briefing** com `AskUserQuestion` (caixa de seleção) e versão em texto, para ajudar o usuário a melhorar o pedido (`references/briefing.md`).
- **Scripts** (`scripts/teixugo.py`, somente biblioteca padrão): `validate-brief`, `queries`, `validate`, `rank`, `economics`, `check-links`, `render`, `doctor`.
- **Relatórios** em md, txt, html, docx, xlsx (com fórmulas) e pdf, todos gerados do mesmo `report.json`.
- **Validação de evidência**: dado `verified` exige fonte e data; modo hipótese só aceita `unverified`; link de maior engajamento precisa ser URL.
- **Ranking por tração** reproduzível (redes sociais, busca, avaliações, anúncios) e matriz de buscas por plataforma, idioma e país.
- Testes automatizados e CI (Linux e Windows, Python 3.9 a 3.13).
- Exemplos fictícios em `examples/`.

### Alterado
- Pontuação de 8 critérios substituída por ranking por tração; margem e risco viraram filtro e alerta.
- Os dois templates de relatório foram substituídos por `references/formato-de-saida.md` e pelo renderizador.

## [0.1.0] - 2026-10-04

### Adicionado
- Primeira versão: fluxo de garimpo aberto, fontes de pesquisa, critérios e templates de relatório em PT-BR e EN.
