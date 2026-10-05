# Sondas, raio e parâmetros de busca

## Contents

- Parâmetros do pedido
- Raio: o quão longe da semente a busca vai
- Sondas: triagem barata antes da verificação cara
- Operadores de busca
- Exemplo completo

## Parâmetros do pedido

Campos do `brief.json` que mudam as buscas (todos opcionais; validados por `validate-brief`):

| Campo | Valores | Padrão | Efeito |
|---|---|---|---|
| `radius` | 0 a 3 | 1 | Quão longe do termo semente pesquisar (veja abaixo) |
| `pain_terms` | `{idioma: [termos]}` | o assunto | Camada 0: termos semente |
| `related_terms` | `{idioma: [termos]}` | nenhum | Camada 1: sinônimos e jeitos de falar a mesma coisa |
| `adjacent_terms` | `{idioma: [termos]}` | nenhum | Camada 2: dores ou nichos vizinhos |
| `analog_markets` | `["US", ...]` | nenhum | Camada 3: países onde o produto já performou |
| `period_days` | 1 a 3650 | sem filtro | Só resultados recentes: acrescenta `after:AAAA-MM-DD` à busca web |
| `exclude` | `["termo", ...]` | nenhum | Acrescenta `-termo` (ou `-"termo composto"`) à busca web |
| `intents` | `discovery`, `proof`, `objection`, `commerce` | todas | Quais tipos de consulta gerar |
| `exact` | `true`/`false` | `false` | Coloca o termo semente entre aspas na busca web |
| `platforms` | chaves de plataforma | todas | Limita onde pesquisar |
| `market` | `["BR", ...]` | `["BR"]` | Países de venda |

Cada linha de `queries` traz `intent` e `radius`, para você priorizar: comece pela camada 0 e pelas intenções `discovery` e `proof`, e vá abrindo conforme precisar.

## Raio: o quão longe da semente a busca vai

| Raio | Inclui | Quando usar |
|---|---|---|
| 0 | Só `pain_terms` | Pedido muito específico, pouca verba de busca |
| 1 (padrão) | + `related_terms` | Quase sempre: pega o jeito que o consumidor realmente fala |
| 2 | + `adjacent_terms` | Poucos candidatos na camada 1, ou o usuário quer ideias vizinhas ("tem algo parecido?") |
| 3 | + os mesmos termos em `analog_markets` | Procurar produtos que já estouraram lá fora e ainda não chegaram aqui |

Você (o modelo) gera `related_terms`, `adjacent_terms` e `analog_markets` a partir da dor; o script só aplica o raio e monta as consultas. Pense em círculos concêntricos: quanto mais longe, mais ruído e mais custo, então só abra o raio quando a camada anterior não bastar.

Exemplo para a dor "remover pelo de cachorro":
- Camada 1: "tirar pelo do sofá", "pelo grudado na roupa".
- Camada 2: "pelo de gato", "escovação para a muda do cão", "limpar estofado".
- Camada 3: `["US"]`, onde o nicho de pet costuma lançar antes (confirme com Trends, não suponha).

## Sondas: triagem barata antes da verificação cara

Verificar a fundo um candidato custa muitas buscas e leituras. A **sonda** é uma olhada rápida e padronizada, de uma ou duas buscas, que decide se vale gastar o resto.

Para cada candidato, na primeira página de resultados, **conte** (sem inventar):

| Contagem | O que contar | Peso |
|---|---|---|
| `social_hits` | Posts ou vídeos distintos sobre o candidato em redes sociais | 30% |
| `market_hits` | Anúncios distintos do candidato em marketplaces | 25% |
| `recent_hits` | Resultados do período recente (use `period_days`) | 25% |
| `ads_hits` | Anunciantes distintos vistos | 10% |
| `complaint_hits` | Resultados com reclamação ou "não funciona" (**negativa**) | até −25 pontos |

Cada contagem vai de 0 a 10. `python scripts/teixugo.py probe candidatos.json` calcula a nota 0–100 e o veredito:

| Nota | Veredito | Ação |
|---|---|---|
| ≥ 60 | `verify` | Verificação a fundo (verifier) |
| 35 a 59 | `watch` | Observar; refaça a sonda depois |
| < 35 | `drop` | Descartar (registre em `discarded`) |

Formato do arquivo de entrada:

```json
[
  {"id": "luva-removedora", "name": "Luva removedora", "probe": {"social_hits": 8, "market_hits": 7, "recent_hits": 9, "ads_hits": 5, "complaint_hits": 1}},
  {"id": "rolo-adesivo", "name": "Rolo adesivo", "probe": {"social_hits": 4, "market_hits": 6, "recent_hits": 3}}
]
```

Limites: as contagens são **de resultados encontrados**, não métricas de plataforma, e dependem do que a ferramenta de busca devolve; os pesos e os limiares são heurísticas ajustáveis (`--verify-at`, `--watch-at`). A sonda **ordena a fila**, não prova nada: a prova vem na verificação. Contagem que faltou aparece em "Sem dado" e baixa a confiança.

## Operadores de busca

A busca na web aceita, em geral, operadores no estilo Google. Os que a skill usa:

| Operador | Uso | Observação |
|---|---|---|
| `site:dominio` | Mirar uma plataforma | Base de toda a descoberta |
| `after:AAAA-MM-DD` | Só resultados depois da data | Vem de `period_days` |
| `-termo` | Excluir termo | Vem de `exclude` |
| `"frase exata"` | Casar a frase | Vem de `exact` |

Dependem de a ferramenta de busca aceitá-los. **Testado em 2026-10-05:** a busca na web usada nos testes aceitou a consulta, mas **ignorou o `after:`** (voltaram vídeos de 2022, 2023 e 2024 para um filtro de julho de 2026). Portanto:

- **nunca presuma** que `period_days` filtrou: confira a data de cada resultado antes de contá-lo como recente (`recent_hits` da sonda, sinais do sonar);
- para vídeos do **TikTok**, `python scripts/teixugo.py post-date URL…` deduz a data aproximada do ID do vídeo, sem abrir a página (que é bloqueada). É uma **estimativa** (comportamento observado do ID, não documentado pela plataforma): use `method: "estimate"`;
- para o YouTube, a API oficial (`youtube --days 90`) filtra por data de verdade;
- o `validate` avisa quando o `top_post` é um vídeo do TikTok com mais de 365 dias.

## Exemplo completo

```json
{
  "kind": "pain",
  "pain": "remover pelo de cachorro",
  "quantity": 3,
  "market": ["BR"],
  "radius": 2,
  "pain_terms": {"pt-BR": ["remover pelo de cachorro"], "en": ["remove dog hair"]},
  "related_terms": {"pt-BR": ["tirar pelo do sofá", "pelo grudado na roupa"]},
  "adjacent_terms": {"pt-BR": ["pelo de gato no estofado"]},
  "period_days": 90,
  "exclude": ["usado", "olx"],
  "intents": ["discovery", "proof", "objection"],
  "platforms": ["tiktok", "youtube", "mercado_livre", "google_trends"]
}
```

`python scripts/teixugo.py queries brief.json --format searches` gera, por exemplo: `site:tiktok.com tirar pelo do sofá funciona mesmo -usado -olx after:2026-07-07`.
