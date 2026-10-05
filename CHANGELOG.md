# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento semântico.

## [0.4.0] - 2026-10-05

### Adicionado
- **Agentes** (`agents/`): `teixugo-scout` (descoberta em paralelo), `teixugo-verifier` (verificação por candidato) e `teixugo-redteam` (revisão adversária). Os que leem a web só têm busca e leitura de página (privilégio mínimo, imposto por teste); só o agente principal escreve arquivos e roda scripts. Comandos `plan` (divide a descoberta em lotes) e `merge` (junta os resultados; vence a evidência mais forte e conflitos viram aviso). Guia em `references/agentes.md`.
- **Plugin do Claude Code** (`.claude-plugin/plugin.json` e `marketplace.json`, validados com `claude plugin validate --strict`): `/plugin marketplace add gabriel-leao-git/teixugo-minerador`.
- **Instalador** passa a instalar os agentes (`~/.claude/agents` ou `.claude/agents`), sem sobrescrever agente seu com o mesmo nome; novas opções `--agents-dest` e `--no-agents`; a desinstalação remove só o que ele colocou.
- **Segurança**: `references/seguranca.md` e `SECURITY.md`; `netguard` (recusa rede interna, esquemas estranhos e redirecionamento para IP privado; redirecionamentos conferidos salto a salto, com `robots.txt` de cada host); `safety` e comando `scan` (detecção de injeção de prompt e de segredo em URL), usados também no `validate` e no `fetch`.
- **Sondas** (`probe`): triagem barata de candidatos antes da verificação a fundo, com nota, veredito e confiança.
- **Parâmetros de busca**: `radius` (0 a 3: termo semente, relacionados, adjacentes, mercados análogos), `period_days` (`after:`), `exclude` (`-termo`), `intents` (discovery, proof, objection, commerce), `exact` (aspas). Cada consulta traz `intent` e `radius`. Guia em `references/sondas-e-raio.md`.
- **Sonar**: persistência (aceleração por 14 dias ou mais = "sustentada", `--sustain-days`), faixas de saturação por número de anunciantes e o sinal `creators` como indicador antecipado.
- **Avaliações** (`evals/`, formato do `claude plugin eval`): pedido vago, recusa de contornar `robots.txt`, injeção em página colada e modo sem web.
- `post-date`: data aproximada de vídeos do TikTok deduzida do ID (estimativa), porque a busca na web testada **ignorou o operador `after:`** e devolveu vídeos de 2022 a 2024 para um filtro de 2026; o `validate` avisa `top_post` do TikTok com mais de 365 dias.
- `ROADMAP.md`: o que a skill faz hoje e o que ainda pode melhorar.

### Alterado
- `SKILL.md`: princípio de que a web é dado e não instrução, checklist de progresso, seção de uso de agentes e fases de sondas e raio.
- `fetch` segue redirecionamentos manualmente e devolve `warnings` quando a página parece uma injeção.

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
