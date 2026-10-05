"""Data aproximada de publicação de um post, deduzida da própria URL (sem abrir a página).

Por que existe: as plataformas grandes bloqueiam a leitura automática, e o operador `after:` nem sempre é
respeitado pela ferramenta de busca, então resultados antigos aparecem como se fossem atuais. Em alguns casos a
data está dentro do ID do post:

  * TikTok: o ID do vídeo é um número em que os 32 bits mais altos são o instante de criação, em segundos
    desde 1970. Isso é um comportamento observado, NÃO documentado pela plataforma: trate o resultado como
    ESTIMATIVA derivada (`method: "estimate"`), nunca como dado verificado.

Plataformas sem essa propriedade (ex.: YouTube) devolvem `posted_at = None`.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any

TIKTOK_RE = re.compile(r"tiktok\.com/@[^/\s?#]+/video/(\d{15,20})")
# instantes plausíveis: 2014 a 2036 (descarta números que só parecem IDs)
_MIN_TS, _MAX_TS = 1_388_534_400, 2_082_758_400
OLD_POST_DAYS = 365  # acima disso o `validate` avisa que o engajamento pode não refletir o momento


def tiktok_posted_at(url: str) -> datetime | None:
    m = TIKTOK_RE.search(url or "")
    if not m:
        return None
    ts = int(m.group(1)) >> 32
    if not _MIN_TS <= ts <= _MAX_TS:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def post_date(url: str, today: date | None = None) -> dict[str, Any]:
    """Plataforma, data aproximada (AAAA-MM-DD ou None), idade em dias e como foi deduzida."""
    today = today or date.today()
    when = tiktok_posted_at(url)
    if when is None:
        return {"url": url, "platform": None, "posted_at": None, "age_days": None, "method": None,
                "note": "não há data deduzível desta URL; abra a página ou use a API oficial"}
    d = when.date()
    return {
        "url": url,
        "platform": "tiktok",
        "posted_at": d.isoformat(),
        "age_days": (today - d).days,
        "method": "estimate",
        "note": "deduzida do ID do vídeo (comportamento observado, não documentado); confirme na página quando puder",
    }
