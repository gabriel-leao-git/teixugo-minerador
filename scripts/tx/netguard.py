"""Proteção de rede: impede que `fetch` e `check-links` sejam usados para alcançar a rede interna (SSRF).

Uma URL que veio da web é dado não confiável: pode apontar para localhost, para a rede da sua casa ou
da empresa, ou para o endereço de metadados de uma nuvem (169.254.169.254). Antes de pedir qualquer página,
este módulo recusa:

  * esquemas que não sejam http/https (file://, ftp://, javascript: etc.);
  * URLs com usuário e senha embutidos;
  * portas fora de 80 e 443;
  * nomes internos (localhost, *.local, *.internal, metadata.google.internal);
  * qualquer nome ou IP que resolva para endereço não público (loopback, rede privada, link-local, CGNAT, reservado).

Limite conhecido: a checagem resolve o nome antes de pedir a página; um servidor DNS malicioso poderia
responder diferente na segunda consulta (DNS rebinding). O risco é pequeno para uma ferramenta local
de uma página por vez, mas é um limite, não uma garantia.
"""
from __future__ import annotations

import ipaddress
import socket
from typing import Any, Callable
from urllib.parse import urlparse

ALLOWED_PORTS = (None, 80, 443)
BLOCKED_HOSTS = {"localhost", "metadata", "metadata.google.internal", "instance-data"}
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".corp", ".intranet")


def ip_is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return False
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped
    return addr.is_global and not addr.is_multicast


def check_url(url: str, resolver: Callable[..., Any] | None = None) -> tuple[bool, str]:
    """(permitido, motivo da recusa). `resolver` imita socket.getaddrinfo (útil em testes)."""
    try:
        p = urlparse(url)
        port = p.port
    except ValueError:
        return False, "URL inválida"
    if p.scheme not in ("http", "https"):
        return False, f"esquema '{p.scheme or '?'}' não permitido (só http e https)"
    host = (p.hostname or "").lower().rstrip(".")
    if not host:
        return False, "URL sem endereço"
    if p.username or p.password:
        return False, "URL com usuário e senha embutidos"
    if port not in ALLOWED_PORTS:
        return False, f"porta {port} não permitida (só 80 e 443)"
    if host in BLOCKED_HOSTS or host.endswith(BLOCKED_SUFFIXES):
        return False, f"endereço interno '{host}' não permitido"

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        return (True, "") if ip_is_public(str(literal)) else (False, f"IP não público ({literal})")

    resolve = resolver or socket.getaddrinfo
    try:
        infos = resolve(host, port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError:
        return True, ""  # não resolveu: a requisição vai falhar sozinha, sem alcançar nada
    for info in infos:
        ip = info[4][0]
        if not ip_is_public(ip):
            return False, f"'{host}' resolve para um endereço não público ({ip})"
    return True, ""
