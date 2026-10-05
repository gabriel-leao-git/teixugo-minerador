# Campos de saída e como provar cada um

Cada campo do produto é `{ "value": …, "label": "verified|estimated|unverified", "source": …, "date": "AAAA-MM-DD", "note": … }`.

- `method` (recomendado em todo campo): como o dado foi obtido: `web_search` (trecho de busca), `web_fetch` (página lida), `browser`, `api`, `user_provided` ou `estimate`. Dado `verified` só por `web_search` gera aviso: abra a página ou rebaixe para `estimated`. Veja `references/acesso-web.md`.
- `verified` **exige** `source` (URL ou onde foi visto) e `date` (dia da consulta).
- `estimated` deve explicar em `note` como foi estimado.
- `unverified` diz no `value` o que não foi possível confirmar.
- Em modo hipótese, todos os campos são `unverified`.
- Use a **mesma métrica e a mesma janela de tempo** em todos os produtos da rodada.

## Texto simples (sem evidência)

| Campo | O que colocar |
|---|---|
| `name` | Nome do produto como o consumidor o encontra (sem marca de terceiros) |
| `pain` | A dor, na linguagem do consumidor |
| `solution_type` | Tipo de solução (luva, rolo, escova…). Varie entre os produtos |

## Campos com evidência

| Campo | Definição | Como obter | Cuidados |
|---|---|---|---|
| `segment` | Segmento de mercado (ex.: pet + limpeza doméstica) | Categoria nos marketplaces, hashtags e lojas concorrentes | Em geral `estimated` |
| `target_audience` | Quem compra: perfil, faixa etária, situação | Comentários dos vídeos, avaliações, públicos dos anúncios | Cite o que viu ("comentários pedem…"); sem estereótipo inventado |
| `effectiveness` | O produto resolve a dor? | **Proxy**: nota média e nº de avaliações do anúncio principal; reclamações recorrentes; vídeos de antes e depois; teste de terceiros | Nunca prometa resultado. Avaliações com todas 5★ no mesmo dia ou de loja de dropshipping não valem como prova. Se só há prova em vídeo do vendedor, é `estimated` |
| `engagement` | Engajamento do post/anúncio líder | Views, curtidas, comentários, compartilhamentos, **na plataforma, na data da consulta** | Informe a métrica ("1,2 mi de views · 96 mil curtidas · TikTok"). Não some plataformas diferentes |
| `top_post` | **URL** do post ou anúncio de maior engajamento | Link de resultado real de busca ou de página aberta; confira que mostra o produto certo | "Maior engajamento" só é `verified` se você comparou métricas. Se só achou o link (comum no TikTok, cujas métricas a leitura automática não alcança), use `estimated` e diga em `note` o critério e o que não leu. Meta Ad Library, em geral, não exibe engajamento de anúncio comercial: use o post orgânico de maior engajamento ou o anúncio com mais tempo no ar |
| `social_networks` | Lista **em ordem** das redes com mais engajamento para o produto | Compare as redes na mesma janela (ex.: últimos 90 dias) | Lista de textos (`["TikTok","Instagram Reels"]`) |
| `search_channel` | Canal com mais busca pelo produto/solução | Google Trends (Web, YouTube, Shopping, Imagens), busca interna de TikTok/marketplaces | É interesse **relativo** (índice 0–100), não volume absoluto. Diga o período e o país |
| `supplier` | Fornecedor candidato | Nome, URL, preço unitário, prazo estimado, avaliações da loja | `verified` só com a página aberta. Sem confirmação de prazo e avaliações, `unverified` |
| `traction_country` | País onde o produto mais performa | Filtro de país nas buscas, idioma dos comentários, país de origem dos anúncios | Em geral `estimated`; diga o critério |
| `supplier_country` | País de origem/envio do fornecedor | Página do fornecedor, local de envio | Diferente de `traction_country`: mantenha os dois |
| `first_seen` | Primeira aparição verificada do produto | Anúncio mais antigo na biblioteca de anúncios, "data de disponibilidade" no marketplace, primeiro vídeo | **Não é a data de lançamento.** Diga a fonte em `source` |
| `comparison` | Como este produto se compara aos outros da rodada | Sua análise: onde ganha, onde perde (tração, margem, efetividade, risco) | `estimated` com `note` ("comparação entre os N produtos desta rodada") |

## Sinais do ranking (`signals`)

Números usados por `rank` para ordenar por tração. Todos relativos aos produtos da mesma rodada.

| Sinal | Significado | Observação |
|---|---|---|
| `engagement` | Interações (ou views, se for a única métrica comum) do post líder | Use a mesma métrica em todos os produtos |
| `search_index` | Índice de busca 0–100 | Compare os termos **no mesmo gráfico** do Google Trends (mesmo período e país) e use a média |
| `social_platforms` | Nº de plataformas com ≥ 3 posts ou anúncios relevantes nos últimos 90 dias | Registre o limiar usado em `limits` |
| `ad_days` | Dias do anúncio ativo mais antigo | Anúncio rodando por meses sugere que paga o tráfego |
| `rating` / `reviews` | Nota (0–5) e nº de avaliações do anúncio principal | Mesmo marketplace para todos, quando possível |
| `advertisers` | Nº de anunciantes distintos com anúncio ativo para o produto | Usado pelo sonar (aceleração, janela e saturação); só se você conseguir contar |
| `creators` | Nº de criadores distintos publicando sobre o produto no período | Usado pelo sonar como indicador antecipado; só se você conseguir contar |

Para o **sonar**, cada produto precisa de um **`id` estável** (kebab-case, igual em todas as leituras), senão mudar o nome faz o produto parecer novo.

`rank_by` escolhe os componentes: `social` (engajamento + plataformas), `search`, `reviews` (nota × confiança pelo volume), `ads` (dias). Se um componente falta em **qualquer** produto, ele sai do cálculo para **todos** e o relatório avisa. A nota é relativa: o melhor da rodada em cada componente recebe 100%.

## Campos opcionais

| Campo | Uso |
|---|---|
| `economics` | `price`, `cost`, `shipping`, `tax`, `fee_pct`, `fee_fixed`, `refund_pct`, `currency`. Só se o usuário pediu margem. Gera lucro, CPA e ROAS de equilíbrio |
| `risks` | Lista de riscos (marca, saturação, qualidade, sazonalidade) |
| `meta.extra_fields` / campos pedidos | Se o usuário pediu algo fora do padrão, acrescente em `risks`, `limits` ou crie uma seção em `next_steps`, e diga no chat onde está |

## Nível do relatório

| Chave | Conteúdo |
|---|---|
| `meta` | `language`, `mode` (`live`/`hypothesis`), `generated_at`, `pain`, `market`, `quantity`, `rank_by`, `request`, `demo` |
| `assumptions` | Padrões que você assumiu |
| `limits` | O que não deu para acessar ou verificar |
| `verdict` | Veredito curto da comparação |
| `products` | Lista ordenada (o primeiro é o melhor) |
| `discarded` | `[{name, reason}]` |
| `next_steps` | Lista de próximos passos |
