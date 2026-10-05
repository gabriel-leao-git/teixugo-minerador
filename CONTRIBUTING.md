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

## Conduta com sites

A skill e os scripts **respeitam o `robots.txt`**, inclusive as regras contra agentes de IA, e tratam HTTP 401/403/429/503, captcha e login como "não". Contribuições que contornem bloqueios (troca de User-Agent, proxies, serviços de scraping para furar restrição, opção para ignorar o `robots.txt`) **não serão aceitas**. Para dados que o site não deixa ler, use API oficial, o navegador do usuário ou dado fornecido por ele.

## Estrutura

```text
SKILL.md          fluxo e regras que o Claude segue
references/       conhecimento carregado sob demanda
scripts/          CLI (teixugo.py) e módulos (tx/)
examples/         brief e relatório fictícios
bin/install.js    instalador do npx (Node, sem dependências)
tests/            testes (unittest; os do instalador usam o Node)
```

## Publicar no npm (mantenedor)

O `npx github:gabriel-leao-git/teixugo-minerador` já funciona sem publicar. Para o comando curto `npx teixugo-minerador`:

```bash
# confirme que package.json, tx/__init__.py e CHANGELOG têm a mesma versão (o teste confere)
python -m unittest discover -s tests
npm pack --dry-run          # confira a lista de arquivos
npm login
npm publish
git tag v<versão> && git push --tags
```
