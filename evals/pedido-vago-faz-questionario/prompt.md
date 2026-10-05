---
name: pedido-vago-faz-questionario
description: Pedido vago, sem dor, quantidade, mercado nem formato. A skill deve perguntar o essencial e não sair pesquisando às cegas.
expected_outcome: Faz perguntas curtas (dor ou nicho primeiro) e oferece o padrão para o resto.
tags: [briefing, smoke]
runs: 3
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
---

acha um produto bom pra eu vender
