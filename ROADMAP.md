# Capacidades e roadmap

Estado em **v0.4.0**. O que a skill já faz, o que ela ainda não faz bem e o que vem a seguir. Itens marcados com 🧪 existem mas **não foram testados contra serviços reais** (só com respostas simuladas).

## O que a skill faz hoje

### Pedir e entender
- Três tipos de busca: **dor**, **nicho** e **sonar** (o que está acelerando).
- Questionário de briefing em caixa de seleção (`AskUserQuestion`) ou em texto, que também ensina o usuário a pedir melhor.
- Parâmetros de busca: **raio** (0 a 3), **período** (`after:`), **exclusões** (`-termo`), **intenções** (descoberta, prova, objeção, comércio), **aspas**, **plataformas** e **mercados**.
- Português e inglês, do pedido ao relatório.

### Pesquisar de verdade
- Matriz de buscas por plataforma, idioma, país e camada do raio, com o texto pronto para a **busca na web** (`site:tiktok.com …`).
- Descoberta de produtos e links **reais** em TikTok, YouTube, Instagram, Pinterest, Reddit e marketplaces pela busca na web.
- Leitura de página (`fetch`): título, descrição, preço e nota por dados estruturados; avisa quando a página parece uma tentativa de injeção.
- 🧪 YouTube pela API oficial (views, curtidas e comentários reais) e importação do CSV do Google Trends (`trends-import`).
- **Sondas**: triagem barata de muitos candidatos antes da verificação a fundo.

### Provar o que diz
- Todo dado tem **etiqueta** (verificado, estimado, não verificado), **fonte**, **data** e **método** de obtenção. Um validador recusa "verificado" sem fonte e data.
- Link de "maior engajamento" nunca inventado; só "verificado" se houve comparação de métricas.
- Checagem de links (`check-links`) e avisos de dado fraco (por exemplo, "verificado" só por trecho de busca).

### Vários agentes
- **Descoberta em paralelo** (`teixugo-scout`), **verificação por candidato** (`teixugo-verifier`) e **revisão adversária** (`teixugo-redteam`).
- `plan` divide o trabalho; `merge` junta os resultados, mantém a evidência mais forte e registra conflitos.
- Privilégio separado: quem lê a web só tem busca e leitura de página (imposto por teste).

### Sonar, histórico e alertas
- Retratos de cada leitura, **aceleração semanal** por componente (engajamento, busca, avaliações, anunciantes, criadores), **janela de oportunidade**, **persistência** (14 dias) e **faixas de saturação**.
- `watch` com código de saída 10 para alerta e resumo em Markdown; `watch routine` gera o texto de uma rotina agendada. 🧪 O envio por e-mail, agenda ou notificação depende de conectores autorizados e **não foi testado**.

### Relatórios
- **PDF, Word, Excel (com fórmulas), HTML, .txt e .md**, todos do mesmo JSON, em português e inglês.
- Unit economics opcional: lucro, CPA e ROAS de equilíbrio com cenário de preço menor.

### Segurança
- A web é **dado, nunca instrução**: detecção de injeção de prompt, privilégio separado e revisão.
- Respeita o `robots.txt` (inclusive proibições a agentes de IA) e **não contorna** bloqueios.
- Proteção de rede: recusa localhost, IPs privados e esquemas estranhos, e confere cada redirecionamento.
- Chaves só por variável de ambiente; avisos para URL com segredo.

### Instalação e qualidade
- `npx github:gabriel-leao-git/teixugo-minerador`, plugin do Claude Code (`/plugin marketplace add …`) e `git clone`.
- 220+ testes automatizados, CI em Linux e Windows (Python 3.9 e 3.13), avaliações no formato `claude plugin eval`.

## O que ainda pode melhorar

### Limites que vêm de fora (a skill respeita, não resolve)
| Limite | Efeito | Caminho |
|---|---|---|
| TikTok, Mercado Livre, Amazon, Meta Ad Library e Trends bloqueiam leitura automática | Os números de engajamento nem sempre são verificáveis | API oficial, CSV, navegador do usuário, modo assistido |
| A busca na web devolve trechos, não métricas | Descoberta boa, prova fraca | Escada de acesso e etiquetas honestas |
| A busca testada **ignorou o `after:`** (voltaram vídeos de 2022 a 2024 para um filtro de 2026) | Resultado antigo parece atual | Conferir a data de cada resultado; `post-date` para TikTok; YouTube pela API filtra de verdade |
| O Google Trends só dá índice relativo | "Canal com maior busca" não é volume | Dizer isso no relatório; comparar termos no mesmo gráfico |
| Sonar precisa de histórico | A primeira leitura é só linha de base | Rotinas agendadas com memória persistente |

### Melhorias planejadas (por ordem de valor)
1. **Modo assistido guiado** (`evidence-sheet`): gerar uma planilha ou formulário com os links a abrir e deixar o usuário colar views, curtidas e comentários, que voltam como `user_provided` (resolve de forma legítima a maior limitação).
2. **Formulário HTML offline** para o briefing: um "pop-up" real fora do Claude Code, que gera o pedido pronto para colar.
3. **Rotina agendada de ponta a ponta**: testar e documentar o envio por Gmail e Google Calendar, e a persistência do histórico no repositório da rotina.
4. **Região e clima**: o produto funciona em clima seco, úmido, frio ou tropical? Cruzar atributos do produto com clima, renda, moradia e formas de pagamento.
5. **Transportadoras**: reputação e tempo de mercado com fatos, fonte e data (Reclame Aqui, Consumidor.gov.br, avaliações), sem opinião.
6. **Produto digital**: infoproduto, PLR e ebook, com licença, comissão e plataforma no lugar de fornecedor e frete.
7. **Esquecidos e lacuna entre países**: produtos que foram sensação e sumiram (com o motivo de terem sumido) e produtos que estouraram lá fora e ainda não chegaram aqui.
8. **Avaliações automáticas**: rodar `claude plugin eval` no CI (hoje as avaliações existem, mas não foram executadas) e testar com Haiku, Sonnet e Opus.
9. **Exemplos em inglês** e um relatório de demonstração para vídeos.
10. **Dependências do CI**: atualizar as ações que rodam em Node 20 (descontinuado).

### Riscos e cuidados em aberto
- As heurísticas de saturação e persistência vêm de guias do setor, não de validação própria: ajustáveis, mas a conferir por nicho.
- A detecção de injeção por padrões não pega tudo; a defesa principal é o privilégio separado.
- A proteção contra SSRF tem o limite conhecido de DNS rebinding.
- Afirmações sobre empresas (transportadoras, fornecedores) exigem fato, fonte e data para evitar difamação.
