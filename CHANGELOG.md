# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [0.3.0] - 2026-10-05

### Adicionado
- **Pesquisa real na web** como regra: o modo hipótese virou último recurso. Nova `references/acesso-web.md` com a escada de acesso (busca com `site:`, leitura de página, navegador, API oficial, dado do usuário), o que foi testado em cada fonte e as regras de conduta.
- **Busca web pronta**: `queries` devolve, para cada plataforma, o texto de busca com `site:` (`--format searches` imprime só eles). Novo campo `platforms` para limitar onde pesquisar e suporte a Instagram só por busca web.
- **Tipos de busca** no pedido (`kind`): `pain`, `niche` e `sonar`.
- **Sonar**: histórico de leituras, aceleração semanal composta por componente (engajamento, busca, avaliações, anunciantes), janela de oportunidade, produtos novos e que sumiram. Comando `watch` (`add`, `update`, `list`, `routine`) com resumo em Markdown e **código de saída 10** quando há alerta; `watch routine` gera o texto da rotina agendada (e-mail, agenda, notificação via conectores autorizados).
- **Coletores de dados reais**: `fetch` (uma página, com dados estruturados de produto), `youtube` (API oficial, chave por variável de ambiente) e `trends-import` (CSV do Google Trends).
- Campo `method` por dado (`web_search`, `web_fetch`, `browser`, `api`, `user_provided`, `estimate`), `id` estável por produto e sinal `advertisers`.
- Novos avisos de validação: dado `verified` só por trecho de busca; link `verified` com engajamento `unverified`.

### Segurança e conduta
- `fetch` **respeita o `robots.txt`**, inclusive proibições a agentes de IA (Claude-User, ClaudeBot, anthropic-ai), e não tem opção para contornar. Bloqueios HTTP (401/403/429/503) viram "não" e são registrados em `limits`.

### Alterado
- O link de "maior engajamento" não precisa mais ter sido aberto (várias plataformas não permitem), mas só é `verified` se houve comparação de métricas.
- A rodada 1 do questionário passou a perguntar o tipo de busca.

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
