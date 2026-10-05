# Contribuindo / Contributing

Contribuições são bem-vindas: correções, novas fontes de pesquisa, novos idiomas, melhorias nos scripts e relatórios de exemplo.

## Antes de abrir um PR

```bash
pip install -r requirements-optional.txt     # opcional: habilita os testes de docx/xlsx/pdf
python -m unittest discover -s tests         # tudo deve passar
python scripts/teixugo.py validate examples/report.example.pt-BR.json
```

## Regras do projeto

1. **Nada de dado inventado.** Exemplos são fictícios e marcados com `"demo": true`; nunca use marca, loja ou pessoa real num exemplo.
2. **Sem segredos nem dados pessoais** em código, exemplos ou histórico.
3. **Núcleo só com biblioteca padrão.** Dependências novas só como opcionais, importadas sob demanda (veja `scripts/tx/office.py`).
4. **Todo comportamento novo vem com teste** em `tests/`.
5. **`SKILL.md` curto** (menos de 500 linhas): detalhes vão para `references/`. O teste `SkillFile` confere o frontmatter e se os arquivos citados existem.
6. **Descrição do frontmatter** sem `: ` (dois-pontos e espaço) nem ` #`, para o YAML continuar válido.
7. Atualize o `CHANGELOG.md`.

## Estrutura

```
SKILL.md          fluxo e regras que o Claude segue
references/       conhecimento carregado sob demanda
scripts/          CLI (teixugo.py) e módulos (tx/)
examples/         brief e relatório fictícios
tests/            testes (unittest)
```
