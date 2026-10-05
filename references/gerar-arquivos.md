# Gerar o relatório

Formatos: **.md, .txt, .html, .docx (Word), .xlsx (Excel), .pdf**. Todos saem do **mesmo `report.json`**, então os números nunca divergem entre formatos.

## Passo a passo

```bash
python scripts/teixugo.py doctor                                   # o que está disponível
python scripts/teixugo.py rank     teixugo-relatorios/report.json --write
python scripts/teixugo.py validate teixugo-relatorios/report.json  # deve terminar em "ok"
python scripts/teixugo.py check-links teixugo-relatorios/report.json
python scripts/teixugo.py render   teixugo-relatorios/report.json --format pdf,xlsx --out teixugo-relatorios
```

Saída: `teixugo-relatorios/<dor>-<AAAA-MM-DD>.<ext>`. Informe o caminho completo ao usuário. `render` recusa gerar se o relatório tiver erros de validação (nada é escrito pela metade).

## O que cada formato entrega

| Formato | Conteúdo | Dependência |
|---|---|---|
| `.md` / `.txt` | Relatório completo, legível em qualquer editor | Nenhuma |
| `.html` | Página única, com cores, modo escuro e impressão limpa | Nenhuma |
| `.docx` | Documento Word com tabelas e etiquetas coloridas | `python-docx` |
| `.xlsx` | Abas Resumo, Ranking, Fichas, Evidências, Unit economics (com **fórmulas**) e Fontes | `openpyxl` |
| `.pdf` | PDF em paisagem, com tabelas | `reportlab` |

Instale as opcionais com `pip install -r requirements-optional.txt`. Se faltar uma, `render` pula só aquele formato, avisa e gera os demais (código de saída 3).

## Se um formato não puder ser gerado

1. `.docx`, `.xlsx`, `.pdf` sem biblioteca: tente instalar com `pip` se o ambiente permitir. Se houver uma skill de documentos no ambiente (Word, Excel, PDF), use-a **a partir do `.md` ou do `.html`** que o script gerou.
2. Sem Python: escreva o `.md` à mão seguindo `references/formato-de-saida.md` e entregue. Diga ao usuário o que faltou e como converter.
3. PDF pelo navegador: abra o `.html` e use "Imprimir → Salvar como PDF" (o CSS de impressão já está pronto).

## Conferência final

- `validate` terminou em "ok"? `check-links` não acusou `broken` ou `error`?
- Os números do arquivo batem com o que você disse no chat?
- O arquivo existe e tem tamanho maior que zero (o `render` imprime os bytes)?
- Relatório de exemplo (`meta.demo = true`) nunca vai para o usuário como resultado real.
