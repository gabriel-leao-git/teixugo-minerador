# Formato de saída (PT-BR / EN)

Use este modelo quando **não houver Python** (relatório escrito à mão) e como referência do que o `render` produz. Ordem e nomes dos campos são fixos. Exemplo completo e fictício: `examples/report.example.pt-BR.json`.

## Português (pt-BR)

```markdown
# Relatório Teixugo Minerador — {dor}

**Data da consulta:** {AAAA-MM-DD} · **Mercado:** {país} · **Modo:** {dados ao vivo | hipótese}

## Resumo
1. {produto} — {tipo de solução} — Pontuação de tração: {N}/100
2. …
Veredito: {2 frases}

## Premissas e limites
- {padrões assumidos}
- {o que não deu para acessar ou verificar}
_Etiquetas: Verificado = visto na fonte, com data. Estimado = inferência explicada. Não verificado = não foi possível confirmar._

## Produtos
### 1. {Produto}
- **Produto:** …
- **Dor:** …
- **Tipo de solução:** …
- **Segmento:** … {✅|🟡|⚪} _(fonte · data · nota)_
- **Público-alvo:** …
- **Efetividade:** …
- **Engajamento:** … (métrica, plataforma, data)
- **Link (maior engajamento):** {URL aberta e conferida}
- **Redes sociais com maior engajamento:** 1) … 2) …
- **Canal com maior busca:** … (índice relativo, período, país)
- **Fornecedor:** … (URL, preço, prazo)
- **País de maior tração:** …
- **País do fornecedor:** …
- **Primeira aparição verificada:** … (fonte; não é a data de lançamento)
- **Comparação:** … (contra os outros produtos)

## Comparação
| Produto | Tipo de solução | Engajamento | Canal com maior busca | Fornecedor | País de maior tração | Efetividade |
|---|---|---|---|---|---|---|

## Produtos descartados
- {produto} — {motivo}

## Próximos passos
1. …

## Fontes
| Fonte | Data | Etiqueta | Usada em |
|---|---|---|---|

_Este relatório é uma análise de pesquisa e não garante resultados de venda. Confirme leis, tributos e regras de plataforma do seu mercado antes de investir._
```

## English (en)

Same structure, with these labels: **Product, Pain, Solution type, Segment, Target audience, Effectiveness, Engagement, Link (top engagement), Social networks with highest engagement, Top search channel, Supplier, Country with most traction, Supplier country, First verified appearance, Comparison**. Sections: Summary · Assumptions and limits · Products · Comparison · Discarded products · Next steps · Sources. Labels: ✅ Verified · 🟡 Estimated · ⚪ Unverified.

## Regras

- Todo campo (exceto `Produto`, `Dor`, `Tipo de solução`) leva etiqueta, fonte e data.
- O link de maior engajamento é uma URL que você **abriu**. Sem isso: "não verificado" e etiqueta ⚪.
- A seção "Unit economics" só aparece se o usuário pediu margem.
