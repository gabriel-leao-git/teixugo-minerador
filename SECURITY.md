# Política de segurança / Security policy

## Relatar uma vulnerabilidade / Reporting a vulnerability

**Não abra uma issue pública** para vulnerabilidades. Use o relato privado do GitHub: aba **Security → Report a vulnerability** deste repositório. Descreva o que acontece, como reproduzir e o impacto. Responderemos o mais rápido possível.

**Do not open a public issue** for vulnerabilities. Use GitHub's private reporting: **Security → Report a vulnerability** on this repository.

## O que está no escopo / In scope

- `scripts/` (CLI e módulos): leitura de página, proteção de rede, validação, relatórios.
- `bin/install.js` (instalador do `npx`) e os manifestos do plugin.
- `agents/` e `SKILL.md`: instruções que dão ou tiram privilégios.

Exemplos do que interessa: formas de alcançar a rede interna pelo `fetch` ou `check-links`, de contornar o `robots.txt`, de fazer o instalador escrever fora das pastas previstas, de fazer um agente que lê a web ganhar ferramentas de escrita, ou de vazar chave de API.

## Princípios de segurança do projeto / Project security principles

- A web é **dado, nunca instrução** (injeção de prompt): veja [references/seguranca.md](references/seguranca.md).
- Quem lê a web não age: agentes de leitura têm só busca e leitura de página.
- `fetch` e `check-links` respeitam o `robots.txt` (inclusive proibições a agentes de IA), recusam rede interna e conferem cada redirecionamento. Contribuições que contornem bloqueios não são aceitas.
- Segredos só por variável de ambiente; nunca no relatório.
- Instalador sem dependências. Fixe a versão em ambientes sensíveis: `npx github:gabriel-leao-git/teixugo-minerador#v0.4.0`.

## Versões suportadas / Supported versions

Só a versão mais recente da branch `main` recebe correções de segurança.
