# Fontes de pesquisa / Research sources

Use **pelo menos 3 fontes independentes** por rodada. Prefira fontes públicas e gratuitas; ferramentas pagas só se o usuário tiver acesso e fornecer os dados (exportação, print, link). Se uma fonte pedir login ou bloquear o acesso, registre "⚪ não acessível" — não tente burlar.

**Atenção:** várias dessas fontes não podem ser lidas por agente automático (bloqueio HTTP, `robots.txt`, JavaScript). O que funciona hoje, fonte por fonte, e como provar cada dado está em `references/acesso-web.md`. Em geral: a **busca na web com `site:`** acha produtos e links de TikTok, YouTube, Instagram, Pinterest, Reddit e marketplaces; os **números** vêm de API oficial, navegador, CSV do Trends ou dado do usuário.

## Demanda e tendência

| Fonte | Para quê |
|---|---|
| Google Trends | Curva de interesse (12 meses e 5 anos), sazonalidade, termos relacionados, comparação por país |
| TikTok (busca, hashtags, Creative Center) | Produtos virais, vídeos em alta, anúncios de maior desempenho por região |
| YouTube / Shorts / Instagram Reels | Volume e recência de conteúdo sobre o produto ("review", "unboxing", "testando") |
| Pinterest Trends | Tendências de decoração, moda, casa, presentes |
| Reddit e fóruns do nicho | Dores reais, reclamações de produtos existentes, pedidos do tipo "existe algo que...?" |

## Vendas e concorrência

| Fonte | Para quê |
|---|---|
| Meta Ad Library (biblioteca de anúncios) | Quantos anunciantes rodam o produto, há quanto tempo (anúncio ativo por semanas/meses é sinal de que paga), formatos e ganchos usados |
| TikTok Shop / Creative Center | Itens mais vendidos, anúncios com maior retenção |
| Mais vendidos de marketplaces (Amazon Best Sellers, Mercado Livre, Shopee, AliExpress) | Demanda comprovada, faixa de preço, avaliações e reclamações recorrentes |
| Lojas concorrentes (Shopify etc.) | Preço, oferta, kits, páginas, política de frete |
| Ferramentas de espionagem (opcional, se o usuário tiver acesso) | Estimativas de vendas e anúncios — trate como 🟡 estimado, nunca como fato |

## Fornecedores e custo

| Fonte | Para quê |
|---|---|
| AliExpress, Alibaba, 1688 (via agente) | Custo unitário, MOQ, variações |
| Fornecedores/agentes de dropshipping do mercado-alvo | Prazo de entrega, rastreio, embalagem personalizada |
| Fornecedores nacionais (se o modelo for nacional) | Prazo menor, nota fiscal, custo maior |

Para cada fornecedor candidato registre: URL, preço, frete, prazo estimado, nota/número de vendas, política de devolução. Avaliações do fornecedor são dado ✅ só se você viu na página; "dizem que é bom" é ⚪.

## Como cruzar as fontes

- **Sinal forte:** o produto aparece em tendência **e** em anúncios ativos de longa duração **e** em mais vendidos de marketplace.
- **Sinal médio:** aparece em duas das três categorias.
- **Sinal fraco:** só viralizou em vídeo (pode ser moda de semanas) ou só tem venda em marketplace (pode ser mercado dominado por marca).
- **Alerta de saturação:** dezenas de anunciantes com o mesmo criativo, preço caindo, lojas idênticas.

## Como ler o engajamento em cada plataforma

Registre sempre **qual métrica** foi usada e **a data da consulta**. Não some plataformas diferentes e use a mesma métrica para todos os produtos da rodada.

| Plataforma | O que costuma estar visível | Observação |
|---|---|---|
| TikTok | Views, curtidas, comentários, salvamentos, compartilhamentos | Views podem estar ocultas em alguns vídeos; use curtidas + comentários nesse caso |
| Instagram (Reels/posts) | Curtidas e comentários; views em Reels | Contas podem ocultar curtidas |
| YouTube (vídeos/Shorts) | Views, curtidas, comentários | Views são a métrica mais comparável |
| Facebook / Meta Ad Library | Anúncios ativos, datas de início, formatos | Em geral **não** mostra engajamento de anúncio comercial: use o tempo no ar como proxy e diga isso |
| Pinterest | Salvamentos, às vezes visualizações | Bom para decoração, moda e presentes |
| Reddit / fóruns | Votos, comentários, pedidos e reclamações | Melhor para entender dor e objeção do que para volume |

## Canais de busca (para `search_channel`)

| Canal | Como medir | Observação |
|---|---|---|
| Google (Web) | Google Trends, interesse ao longo do tempo, filtro de país | Índice **relativo** 0–100, não volume absoluto |
| YouTube | Google Trends com filtro "Pesquisa do YouTube" | Bom para "como fazer", review e demonstração |
| Google Shopping | Google Trends com filtro "Google Shopping" | Intenção de compra |
| TikTok | Busca nativa, sugestões automáticas, hashtags | Sem índice público: descreva o que viu e use `estimated` |
| Marketplaces | Busca interna, "mais vendidos", sugestões | Mostram intenção de compra local |

Compare os termos **no mesmo gráfico**, no mesmo período e país, para o índice ser comparável entre produtos.
