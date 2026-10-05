# Critérios, ranking e filtros

O **ranking** é por **tração** (o que o usuário pediu: mais ranqueados em redes sociais e buscas). Margem e risco entram como **filtro e alerta**, não como nota principal.

## 1. Critérios eliminatórios (se falhar em qualquer um, descarte e registre em `discarded`)

| # | Critério | Exemplos |
|---|---|---|
| E1 | **Proibido ou regulado sem como cumprir** | Medicamentos, suplementos com alegação de saúde, cosméticos e saneantes sem registro, brinquedos sem certificação, eletrônicos que exigem homologação, armas, nicotina |
| E2 | **Marca registrada, réplica ou propriedade intelectual** | Logo ou personagem licenciado, "inspirado em" marca famosa, design patenteado |
| E3 | **Segurança do consumidor** | Baterias de lítio sem certificação, aquecedores, produtos infantis ou de ingestão sem laudo |
| E4 | **Margem que não fecha** (só se o usuário pediu margem) | Lucro antes de anúncio ≤ 0 |
| E5 | **Logística inviável** | Muito frágil, pesado ou volumoso para o preço, líquido, perecível |
| E6 | **Sem fornecedor confiável** | Nenhum fornecedor com histórico, rastreio ou política de devolução verificável |
| E7 | **Fora do pedido** | Fora da faixa de preço, do tipo de solução ou do mercado que o usuário definiu |

> Leis, tributos e regras de importação mudam e variam por país. **Não assuma** alíquotas nem listas de proibidos de cabeça: verifique a regra vigente do mercado do usuário na data da consulta e cite a fonte. Se não conseguir verificar, marque `unverified` e registre como risco, sem aprovar nem descartar por suposição.

## 2. Ranking por tração (`rank`)

`python scripts/teixugo.py rank REPORT.json --write` calcula uma nota **0–100 relativa aos candidatos da rodada**: o melhor em cada componente recebe 100% daquele componente.

| Componente (`rank_by`) | Peso | Entrada (`signals`) |
|---|---|---|
| `social` | 40 | `engagement` (70%) e `social_platforms` (30%) |
| `search` | 30 | `search_index` |
| `reviews` | 20 | `rating` (0–5) × confiança pelo volume (`reviews`; ~10 mil avaliações = confiança total) |
| `ads` | 10 | `ad_days` (anúncio ativo mais antigo) |

- Só entram os componentes escolhidos em `rank_by` (padrão: `social` + `search`). Os pesos são renormalizados.
- Componente sem dado em **qualquer** produto sai para **todos** (a comparação continua justa) e o relatório avisa.
- A **confiança** é alta com 3 ou mais componentes, média com 2, baixa com 1 ou nenhum.
- A nota **não** mede qualidade nem lucratividade do produto: mede tração relativa. Um 100 no exemplo não significa "excelente", só "líder desta rodada".
- Empate: mantém a ordem original.

### Ranking do sonar

No `kind: "sonar"` o ranking é por **aceleração** (crescimento semanal entre duas leituras, nota absoluta 0–100) e, no desempate, pela **janela** (muita atenção, poucos anunciantes). Fórmulas, limites e salvaguardas em `references/sonar-e-historico.md`. A nota de tração acima continua útil como visão de "quem já é grande"; a aceleração mostra "quem está subindo".

## 3. Unit economics (opcional, só se o usuário pediu margem)

```
custo_total        = custo_produto + frete_fornecedor + impostos_de_importacao (se houver)
taxas              = preco * taxa_% / 100 + taxa_fixa
reserva_reembolso  = preco * reembolso_% / 100
lucro_antes_de_ads = preco - custo_total - taxas - reserva_reembolso
CPA_equilibrio     = lucro_antes_de_ads
ROAS_equilibrio    = preco / lucro_antes_de_ads
margem_%           = lucro_antes_de_ads / preco * 100
```

- `python scripts/teixugo.py economics --price 59.9 --cost 8 --shipping 6 --tax 12 --fee-pct 4.5 --fee-fixed 1 --refund-pct 5`
- Mostra dois cenários: preço base e preço 15% menor (concorrência forçando queda).
- Use as taxas **reais** do gateway e da plataforma do usuário; se não souber, marque como premissa.
- Heurística (não regra): preço de venda em torno de 3× o custo total costuma deixar espaço para anúncio.

## 4. Sinais de alerta (viram `risks` ou ressalva)

- Só um vídeo viral como evidência, sem anúncio rodando nem busca consistente.
- Dezenas de anunciantes com o mesmo criativo e preço em queda (saturação).
- Fornecedor com poucas avaliações ou prazo vago.
- O consumidor acha o mesmo item por menos em marketplace local.
- Reclamações recorrentes de qualidade no produto original.
- Dependência de alegação que não dá para comprovar ("emagrece", "cura").
- Forte sazonalidade sem plano para a entressafra.
- Mais da metade dos dados do produto `unverified`: **não o coloque no topo sem ressalva explícita**.
