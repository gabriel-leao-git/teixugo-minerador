# Sonar, histórico e vigilâncias

## O que o sonar é (e o que não é)

**Não é previsão.** Ninguém sabe qual produto vai viralizar. O sonar mede **aceleração**: quanto engajamento, busca, avaliações e número de anunciantes cresceram **entre duas leituras**. Produto que cresce rápido e ainda tem poucos anunciantes é um sinal de oportunidade, não uma promessa.

Por isso o sonar precisa de **histórico**:
- **Primeira leitura** = linha de base (não há aceleração para calcular).
- **A partir da segunda** = aceleração. Intervalo recomendado entre leituras: 3 a 7 dias.

## Tipos de busca (`kind` no pedido)

| `kind` | Uso | Exige |
|---|---|---|
| `pain` | Produtos que resolvem uma dor (o modo padrão) | `pain` |
| `niche` | Produtos de um nicho, sem dor específica | `niche` |
| `sonar` | O que está acelerando num tema | `pain` ou `niche` (onde procurar) |

Filtros opcionais: `market` (países) e `platforms` (limita as plataformas pesquisadas; valores em `PLATFORM_KEYS`, ex.: `["tiktok","youtube","mercado_livre"]`).

## Sinais usados (`signals` em cada produto)

| Sinal | Componente | Observação |
|---|---|---|
| `engagement` | social | Mesma métrica e mesma janela em todas as leituras |
| `search_index` | busca | Do CSV do Trends (`trends-import`), mesmo gráfico e período |
| `reviews` | avaliações | Número de avaliações do anúncio principal |
| `advertisers` | anúncios | Anunciantes distintos com anúncio ativo, como a biblioteca de anúncios mostra |

- Defina um **`id` estável** (kebab-case) para cada produto e **use o mesmo em todas as leituras**. Sem `id`, a chave é o nome, e mudar o nome faz o produto parecer "novo".
- Sinal que você não conseguiu medir fica de fora (não invente). Um componente ausente em **qualquer** produto não entra no cálculo de aceleração; o relatório mostra o que ficou de fora.

## Fluxo de uma leitura

1. Pedido com `kind: "sonar"`. Rode a pesquisa normal (fases 1 a 4 do `SKILL.md`), com os 4 sinais acima.
2. Se for a primeira leitura, crie a vigilância: `python scripts/teixugo.py watch add ID BRIEF.json`.
3. `python scripts/teixugo.py watch update ID REPORT.json`. O comando:
   - grava o retrato em `teixugo-watch/history/ID.json`;
   - compara com a leitura anterior;
   - grava `sonar` em cada produto e `radar` no relatório (e reordena por aceleração);
   - escreve o resumo em `teixugo-watch/alerts/ID-AAAA-MM-DD.md`;
   - termina com **código 10 se há alerta**, 0 se não há.
4. `render REPORT.json` mostra a seção "Sonar" com a aceleração de cada produto.

## Como ler o resultado

| Campo | Significado |
|---|---|
| Crescimento por componente | Crescimento **semanal equivalente** (composto), para leituras com intervalos diferentes ficarem comparáveis |
| Nível `forte` | Nota de aceleração mínima (padrão 40) e ao menos **2** componentes acima do limite (padrão +20%/semana) |
| Nível `moderado` | Ao menos 1 componente acima do limite. Informativo; só alerta se `--alert-on-moderate` |
| Aceleração (0–100) | **Absoluta**: +100% por semana em um componente dá a nota máxima daquele componente. Não depende dos outros produtos |
| Janela (0–100) | **Relativa** à leitura: muita atenção e poucos anunciantes. Precisa de `engagement` e `advertisers` |
| Novos / sumiram | Produtos que apareceram ou deixaram de aparecer em relação à leitura anterior (sumir não prova que morreu: pode ser falha de busca) |

Salvaguardas: **bases pequenas são ignoradas** (de 10 para 40 views é +300% e não significa nada: o mínimo é 1.000 de engajamento, 5 de índice, 20 avaliações, 3 anunciantes) e leituras com menos de 2 dias de intervalo não são comparadas.

## Vigilâncias e agendamento

| Comando | Para quê |
|---|---|
| `watch add ID BRIEF.json [--channels email,calendar,push] [--schedule "toda segunda, 8h"]` | Cria a vigilância, com limites ajustáveis (`--min-growth`, `--min-score`, `--min-days`, `--alert-on-moderate`, `--no-alert-on-new`) |
| `watch list` | Lista as vigilâncias |
| `watch update ID REPORT.json` | Registra a leitura e mede a aceleração |
| `watch routine ID` | Imprime o **texto pronto** para criar uma rotina agendada |

**O agendamento não é da skill.** A skill e os scripts registram, comparam e escrevem o resumo; quem dispara no horário e quem envia o aviso são recursos do ambiente:

- **Rotina na nuvem do Claude Code** (`/schedule`, app desktop ou claude.ai/code/routines): roda no cronograma, com o computador desligado. Cole o texto de `watch routine ID` como prompt.
- **Conectores** (Gmail, Google Calendar): a rotina pode usá-los para enviar o resumo ou criar um lembrete. **Precisam estar autorizados** nas configurações de conectores do claude.ai. A skill não autoriza nada nem finge que enviou: se faltar, diz qual conector faltou. Se o conector de e-mail envia ou só cria rascunho depende do conector; confira antes de contar com o envio.
- **Memória entre execuções:** uma rotina na nuvem começa do zero. A pasta `teixugo-watch/` precisa persistir (por exemplo, commitada no repositório da rotina). Sem isso, toda leitura vira "linha de base".
- **Notificação** (`push`): só funciona onde o ambiente oferece.

## Limites (diga ao usuário)

- Aceleração mede o que foi **lido**: métricas ocultas ou páginas bloqueadas reduzem os sinais e a confiança.
- Crescimento de métrica pública pode ser impulsionado por anúncio pago ou por conta que revende vídeo: confira o link antes de agir.
- Sazonalidade (Natal, Dia das Mães) também "acelera". Compare com o mesmo período do ano anterior no Trends antes de apostar.
- Poucas leituras = pouca confiança. Duas leituras dão uma foto da variação; cinco ou mais mostram tendência.
