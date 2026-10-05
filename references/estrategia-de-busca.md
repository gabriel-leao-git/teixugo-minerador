# Estratégia de busca (para acertar mais)

O objetivo é achar produtos que **de fato** têm tração e provar isso, sem se enganar com viral passageiro, anúncio de nicho errado ou métrica inflada.

## 1. Decomponha a dor

Dor → situações → tipos de solução → nomes de produto → sinônimos. Exemplo, "remover pelo de cachorro":

- Situações: pelo no sofá, na roupa, no carpete, no carro, na muda do animal.
- Tipos de solução: luva, rolo adesivo, escova, rodo de borracha, aspirador pet, pedra removedora.
- Os termos dessa decomposição viram `pain_terms` (veja `references/briefing.md`).

## 2. Escada de consultas

Rode as consultas nesta ordem, do amplo ao específico. `python scripts/teixugo.py queries BRIEF.json --format searches` imprime os textos prontos para a **busca na web** (ex.: `site:tiktok.com remover pelo de cachorro review`); sem `--format`, a matriz traz também o link de busca nativo de cada plataforma. **Execute** as buscas e use as URLs reais que voltarem; o que a busca mostra é descoberta, não prova de métrica (`references/acesso-web.md`).

| Degrau | Objetivo | Exemplo |
|---|---|---|
| Descoberta | Que soluções existem? | "como remover pelo de cachorro do sofá" |
| Solução | Como cada tipo é vendido? | "luva removedora de pelo" |
| Prova | Funciona? | "… antes e depois", "… review" |
| Objeção | Onde falha? | "… reclamação", "… não funciona" |
| Comércio | Quem vende e a que preço? | "… comprar", marketplaces |

Os sufixos de prova e de objeção são a base para medir `effectiveness`. Reclamações recorrentes pesam mais que elogios isolados.

### Raio, período e sondas

Comece pelo raio 0 ou 1 e abra só se faltar candidato. Use `period_days` para ignorar resultado velho e `exclude` para cortar ruído (usado, revenda). Antes de verificar a fundo, **sonde** todos os candidatos e fique com os que passam. Parâmetros, contagens e limiares em `references/sondas-e-raio.md`.

## 3. Triangulação

Um candidato só entra no ranking com **sinal em pelo menos 3 fontes independentes**:

1. **Atenção:** vídeos/posts com engajamento (TikTok, Instagram, YouTube, Pinterest).
2. **Intenção:** busca (Google Trends, busca de YouTube, marketplaces).
3. **Dinheiro:** anúncios ativos há tempo, mais vendidos, avaliações em volume.

| Sinal | Quando |
|---|---|
| Forte | Atenção + intenção + dinheiro |
| Médio | Duas das três |
| Fraco | Só uma (viral isolado, ou venda só de marca grande). Não entra no top sem ressalva |

## 4. Verifique antes de registrar

Para cada dado que vai virar `verified`:

- **Abra** a página. Registre URL e data.
- **Recência:** engajamento dos últimos 90 dias; tendência de 12 meses. Post de anos atrás não prova nada hoje.
- **Produto certo:** o vídeo viral é mesmo do produto (não de outro item ou de uma marca)?
- **Original:** não é repost nem conta que revende o vídeo.
- **Métrica comparável:** mesma plataforma e mesma definição entre os produtos.
- **País:** o conteúdo é do mercado-alvo (idioma e moeda batem)?

## 5. Armadilhas comuns

| Armadilha | Como evitar |
|---|---|
| Misturar anúncio e orgânico | Registre qual é e use o mesmo critério nos três produtos |
| Termo de marca no lugar da solução | Busque pela solução; marcas viram risco, não candidatas |
| Avaliações de loja de dropshipping | Prefira marketplace com compra verificada |
| Pico de busca de uma semana | Compare 12 meses e 5 anos no Trends |
| Variantes do mesmo item contadas como produtos diferentes | Agrupe por tipo de solução |
| Anúncio "ativo" sem tempo de veiculação | Registre a data de início e calcule `ad_days` |
| Métricas escondidas ou arredondadas | Anote o que a plataforma mostra, não o que você supõe |

## 6. Quando parar

Pare de cavar quando, para cada um dos N produtos escolhidos: (a) há sinal em 3 fontes, (b) o `top_post` foi aberto e confirmado, (c) há pelo menos um fornecedor verificado. Se após um esforço razoável um campo continuar impossível, deixe `unverified`, anote em `limits` e siga. Mais busca não vale um dado inventado.

## 7. Fontes bloqueadas

Login, pagamento, captcha, `robots.txt` que proíbe agentes de IA ou bloqueio de robô (HTTP 403, 429, 503): **não contorne**. Registre em `limits` ("Meta Ad Library não acessível nesta sessão") e use outra fonte para o mesmo sinal: busca na web com `site:`, API oficial (`youtube`), CSV do Trends, navegador do usuário ou o modo assistido. Se o usuário tiver ferramentas pagas, peça a exportação ou o print e use como `estimated`.

## 8. Registre enquanto pesquisa

Atualize `report.json` a cada produto concluído (não deixe tudo para o fim): se a sessão cair, nada se perde. Rode `validate` com frequência: ele aponta `verified` sem fonte ou data antes de virar problema.
