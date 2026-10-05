"""Detecção barata de injeção de prompt e de vazamento de segredo em texto vindo da web.

O texto de páginas, resultados de busca e respostas de agentes é DADO NÃO CONFIÁVEL: pode trazer frases
que tentam dar ordens ao modelo ("ignore as instruções anteriores..."). Esta checagem é uma camada
extra de defesa, não a defesa principal (a principal é tratar a web como dado e separar privilégios,
veja references/seguranca.md). Ela encontra padrões conhecidos; não encontra tudo.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlparse

_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+|the\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", "tenta anular as instruções anteriores"),
    (r"disregard\s+(all\s+|the\s+|any\s+)?(previous|prior|above|earlier)", "tenta anular as instruções anteriores"),
    (r"ignor[ae]\s+(todas?\s+)?(as\s+)?(instru[cç][õo]es|regras)\s+(anteriores|acima|passadas)", "tenta anular as instruções anteriores"),
    (r"(system|developer)\s+prompt|prompt\s+do\s+sistema|mensagem\s+do\s+desenvolvedor", "menciona o prompt do sistema"),
    (r"(new|updated)\s+instructions?\s*:|novas?\s+instru[cç][õo]es\s*:", "apresenta 'novas instruções'"),
    (r"do\s+not\s+(tell|inform|mention)\s+(this\s+to\s+)?the\s+user|n[ãa]o\s+(diga|avise|conte)\s+(isso\s+)?ao\s+usu[aá]rio", "pede para esconder algo do usuário"),
    (r"(send|post|upload|email|exfiltrate|envie|mande|poste)\s+.{0,40}(api[\s_-]?key|token|password|credentials?|senha|chave|segredo)", "pede para enviar credenciais"),
    (r"<\s*script\b", "contém tag <script>"),
    (r"javascript\s*:|data\s*:\s*text/html", "contém URL executável (javascript: ou data:)"),
    (r"(curl|wget)\s+[^|\n]{0,200}\|\s*(sh|bash|zsh|python)", "contém comando que baixa e executa código"),
    (r"base64\s+(-d|--decode)|powershell\s+.{0,20}-enc", "contém comando ofuscado"),
    (r"\brm\s+-rf\b|\bformat\s+c:|del\s+/f\s+/s", "contém comando destrutivo"),
    (r"[A-Za-z0-9+/]{240,}={0,2}", "contém bloco longo codificado (possível payload escondido)"),
]
_COMPILED = [(re.compile(p, re.I | re.S), why) for p, why in _PATTERNS]

_SECRET_QUERY_KEYS = {
    "token", "access_token", "auth", "authorization", "key", "apikey", "api_key", "api-key", "password", "passwd",
    "secret", "session", "sessionid", "sid", "sig", "signature", "code", "jwt", "bearer",
}


def scan_text(text: str) -> list[str]:
    """Motivos pelos quais o texto parece uma tentativa de injeção (lista vazia = nada encontrado)."""
    if not isinstance(text, str) or not text:
        return []
    found: list[str] = []
    for rx, why in _COMPILED:
        if rx.search(text) and why not in found:
            found.append(why)
    return found


def scan_url(url: str) -> list[str]:
    """Avisos sobre uma URL que seria gravada no relatório (credenciais embutidas ou segredo na query)."""
    out: list[str] = []
    try:
        p = urlparse(url)
    except ValueError:
        return out
    if p.username or p.password:
        out.append("URL com usuário e senha embutidos")
    bad = sorted({k for k, _ in parse_qsl(p.query, keep_blank_values=True) if k.lower() in _SECRET_QUERY_KEYS})
    if bad:
        out.append(f"URL com parâmetro que pode ser segredo ({', '.join(bad)})")
    return out


def walk_strings(obj, path: str = ""):
    """Gera (caminho, texto) para todas as strings de um JSON."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
