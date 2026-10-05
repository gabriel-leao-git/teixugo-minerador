# Briefing: entender o pedido e perguntar só o que falta

## 1. O que extrair do pedido

| Campo (`brief.json`) | O que é | Padrão se faltar |
|---|---|---|
| `kind` | Tipo de busca: `pain` (por dor), `niche` (por nicho) ou `sonar` (o que está acelerando) | `pain`; `niche` se só o nicho foi informado |
| `pain` | A dor que os produtos devem resolver. **Obrigatório em `pain`** | Sem padrão: pergunte |
| `niche` | O nicho (ex.: "pet", "organização de casa"). **Obrigatório em `niche`**; no `sonar`, `pain` ou `niche` | Sem padrão |
| `platforms` | Limita onde pesquisar: `tiktok`, `youtube`, `instagram`, `pinterest`, `reddit`, `google`, `google_trends`, `meta_ad_library`, `mercado_livre`, `amazon`, `shopee`, `aliexpress` | Todas |
| `quantity` | Quantos produtos entregar (1 a 10) | 3 |
| `market` | Países onde vender (códigos: `["BR"]`) | `["BR"]` |
| `language` | Idioma do relatório (`pt-BR` ou `en`) | O idioma do pedido |
| `rank_by` | O que define "mais ranqueado": `social`, `search`, `reviews`, `ads` | `["social","search"]` |
| `solution_variety` | `different` (tipos de solução distintos), `same`, `any` | `different` |
| `output_formats` | `md`, `txt`, `html`, `docx`, `xlsx`, `pdf` | `["md"]` |
| `include_economics` | Incluir margem, CPA e ROAS | `false` |
| `price_range` | `{min, max, currency}` de preço de venda | Sem filtro |
| `extra_fields` | Campos além do formato padrão que o usuário pediu | Nenhum |
| `pain_terms` | Termos de busca por idioma (você gera, não pergunta) | Texto da dor |

**Leitura do pedido, por exemplo:** *"Quero que você busque 3 produtos que resolvam a mesma dor, a dor é remover pelo de cachorro. Traga os 3 mais ranqueados em redes sociais, canais de busca, países, segmento, público-alvo, fornecedor, país, efetividade e o link do anúncio/postagem com maior engajamento."*

| Trecho | Vira |
|---|---|
| "3 produtos" | `quantity: 3` |
| "a mesma dor … remover pelo de cachorro" | `pain` (todos os produtos resolvem a mesma dor, com soluções concorrentes) |
| "mais ranqueados em redes sociais, canais de busca" | `rank_by: ["social","search"]` |
| "países" e "país" | **dois** campos: país de maior tração e país do fornecedor |
| "segmento, público-alvo, fornecedor, efetividade" | campos do formato padrão |
| "link do anúncio/postagem com maior engajamento" | campo `top_post` |
| (nada sobre formato de arquivo) | pergunte, ou `md` |

Palavras que mudam o que você faz: "barato", "premium" (faixa de preço); "só nacional" (modelo logístico); "que não seja de marca" (filtro); "para TikTok Shop" (plataforma de venda); "mais recentes" (janela de tempo menor).

## 2. Quando perguntar

- **Pedido completo** (dor + o suficiente para os padrões servirem): não pergunte. Responda com "Entendi assim:" e 3 a 5 linhas, e siga. O usuário corrige se precisar.
- **Falta a dor:** pergunte em texto simples, em uma frase ("Qual dor ou problema os produtos devem resolver?"). Dor é texto livre, não cabe em múltipla escolha.
- **Faltam decisões estruturais** (formato do arquivo, mercado, quantos): use o questionário abaixo.
- **Pedido ambíguo** (ex.: "acha um produto bom"): faça só a pergunta da dor e use o questionário para o resto.

Regras: no máximo **2 rodadas**; só pergunte o que muda o resultado; sempre deixe o padrão marcado como recomendado; o que ficar sem resposta vira premissa registrada no relatório.

## 3. Questionário com `AskUserQuestion` (caixa de seleção)

A ferramenta aceita de 1 a 4 perguntas por chamada, 2 a 4 opções por pergunta, e o usuário sempre pode digitar "Outro". Use-a quando estiver disponível (Claude Code). Os rótulos abaixo vão em `options[].label`; o texto curto em `header` (até 12 caracteres).

**Rodada 1** (uma chamada, 4 perguntas):

| header | question | options (recomendada primeiro) | multiSelect |
|---|---|---|---|
| Tipo | O que você quer fazer? | Produtos para uma dor (Recomendado) · Produtos de um nicho · Sonar: o que está acelerando | não |
| Quantidade | Quantos produtos devo trazer? | 3 (Recomendado) · 5 · 1 · 10 | não |
| Mercado | Em qual mercado você vai vender? | Brasil (Recomendado) · Estados Unidos · Portugal / Europa | não |
| Formato | Em qual formato quer o relatório? | PDF · Excel (.xlsx) · Word (.docx) · Markdown / texto | **sim** |

**Rodada 2** (só se fizer diferença, 2 a 4 perguntas):

| header | question | options | multiSelect |
|---|---|---|---|
| Ranking | O que define "mais ranqueado"? | Redes sociais (Recomendado) · Buscas (Recomendado) · Avaliações e efetividade · Anúncios ativos | **sim** |
| Plataformas | Onde devo pesquisar? | Todas (Recomendado) · TikTok e YouTube · Marketplaces · Redes sociais | não |
| Variedade | Os produtos devem ser de tipos diferentes? | Sim, tipos diferentes (Recomendado) · Podem ser variações do mesmo tipo | não |
| Margem | Incluir custo, margem e ROAS de equilíbrio? | Não, só pesquisa (Recomendado) · Sim, com cenários de preço | não |

Faixa de preço e logística (dropshipping internacional, fornecedor nacional ou estoque próprio) só entram se o usuário mencionar; senão, use os padrões. A dor ou o nicho continua sendo pergunta em texto livre.

Se a ferramenta devolver "Outro" com texto, use o texto. Traduza as respostas para `brief.json`.

## 4. Questionário em texto (quando não há `AskUserQuestion`)

Envie **uma** mensagem curta e aceite "ok" para tudo:

```
Para eu cavar no lugar certo, confirme (responda "ok" para aceitar os padrões):
1. Dor ou nicho: ______  (obrigatório). Quer o sonar (o que está acelerando)? (padrão: não)
2. Quantos produtos? (padrão: 3)
3. Mercado? (padrão: Brasil)
4. Formato do relatório? PDF / Excel / Word / .txt / .md (padrão: .md)
5. Ranking por? redes sociais, buscas, avaliações, anúncios (padrão: redes sociais + buscas)
6. Algo mais? faixa de preço, tipo de solução, o que evitar (opcional)
```

## 5. Ajudando o usuário a pedir melhor

Quando o pedido vier vago, sugira o modelo abaixo em uma linha, sem bronca:

```
Dor: <o problema> · Quantidade: <N> · Mercado: <país> · Ranking por: <redes/buscas/avaliações> · Formato: <PDF/Excel/...> · Evitar: <opcional>
```

| Pedido fraco | Pedido forte |
|---|---|
| "acha um produto bom de pet" | "3 produtos que resolvam pelo de cachorro no sofá, para o Brasil, em PDF" |
| "o que está bombando?" | "os 5 produtos mais ranqueados no TikTok para a dor de cozinha pequena, mercado BR" |
| "produto barato" | "produtos de venda entre R$ 60 e R$ 200 para a dor X" |

Se o usuário disser que não sabe a dor, ofereça o garimpo aberto: 3 a 5 dores com demanda forte no mercado dele e uma pergunta para escolher.

## 6. Gerando `pain_terms`

Para cada idioma do mercado, 2 a 4 termos. Misture:
- a **forma de verbo** ("remover pelo de cachorro") e a de **substantivo** ("removedor de pelo de cachorro");
- o **jeito que o consumidor fala** ("tirar pelo do sofá", "pelo grudado na roupa");
- o **tipo de solução**, quando já for conhecido ("luva para tirar pelo").

Mercado fora do Brasil: use o idioma local (`es`, `en`) e confirme a variante regional.

## 7. Salvar e validar

Grave `teixugo-relatorios/brief.json` e rode `python scripts/teixugo.py validate-brief teixugo-relatorios/brief.json`. Exemplo completo em `examples/brief.example.json`; `python scripts/teixugo.py brief-template` imprime um modelo.
