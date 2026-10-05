"""YouTube pela API oficial (YouTube Data API v3): números reais de visualizações, curtidas e comentários.

É o caminho legítimo e verificável para engajamento no YouTube. Exige uma chave de API gratuita
(Google Cloud Console), lida da variável de ambiente YOUTUBE_API_KEY (nunca como argumento, para não
ficar no histórico do terminal). A busca custa 100 unidades da cota diária (padrão: 10 mil).
A chave nunca é impressa: as mensagens de erro não incluem a URL.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

API = "https://www.googleapis.com/youtube/v3"


class YouTubeError(RuntimeError):
    pass


def _default_get(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa da API)
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.load(e).get("error", {}).get("message", "")
        except Exception:
            pass
        raise YouTubeError(f"YouTube API respondeu HTTP {e.code}. {detail}".strip()) from None
    except Exception as e:
        raise YouTubeError(f"falha ao falar com a YouTube API ({type(e).__name__})") from None


def search_videos(
    query: str,
    api_key: str,
    region: str = "BR",
    language: str | None = None,
    days: int | None = 90,
    max_results: int = 10,
    get_json: Callable[[str, float], Any] | None = None,
    timeout: float = 15.0,
) -> list[dict[str, Any]]:
    """Busca vídeos e devolve, ordenados por visualizações, com as estatísticas de cada um."""
    if not api_key:
        raise YouTubeError("defina a variável de ambiente YOUTUBE_API_KEY")
    get = get_json or _default_get
    params = {"part": "snippet", "type": "video", "q": query, "order": "viewCount", "regionCode": region,
              "maxResults": max(1, min(int(max_results), 50)), "key": api_key}
    if language:
        params["relevanceLanguage"] = language
    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        params["publishedAfter"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    found = get(f"{API}/search?{urllib.parse.urlencode(params)}", timeout)
    ids = [i["id"]["videoId"] for i in found.get("items", []) if i.get("id", {}).get("videoId")]
    if not ids:
        return []
    stats = get(f"{API}/videos?{urllib.parse.urlencode({'part': 'statistics,snippet', 'id': ','.join(ids), 'key': api_key})}", timeout)
    out: list[dict[str, Any]] = []
    for v in stats.get("items", []):
        s = v.get("statistics", {})
        out.append(
            {
                "video_id": v["id"],
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "title": v.get("snippet", {}).get("title", ""),
                "channel": v.get("snippet", {}).get("channelTitle", ""),
                "published_at": v.get("snippet", {}).get("publishedAt", ""),
                "views": int(s["viewCount"]) if "viewCount" in s else None,
                "likes": int(s["likeCount"]) if "likeCount" in s else None,  # pode estar oculto
                "comments": int(s["commentCount"]) if "commentCount" in s else None,  # pode estar desligado
            }
        )
    return sorted(out, key=lambda x: x["views"] or 0, reverse=True)


def as_evidence(videos: list[dict[str, Any]], today: str | None = None) -> dict[str, Any] | None:
    """Campos `engagement`, `top_post` e `signals.engagement` prontos para o relatório (vídeo mais visto)."""
    if not videos:
        return None
    top = videos[0]
    day = today or date.today().isoformat()
    parts = []
    for key, label in (("views", "views"), ("likes", "likes"), ("comments", "comments")):
        if top.get(key) is not None:
            parts.append(f"{top[key]:,} {label}".replace(",", "."))
    return {
        "engagement": {
            "value": " · ".join(parts) + " (YouTube)",
            "label": "verified",
            "source": top["url"],
            "date": day,
            "method": "api",
        },
        "top_post": {
            "value": top["url"],
            "label": "verified",
            "source": "YouTube Data API v3",
            "date": day,
            "method": "api",
            "note": "vídeo mais visto entre os resultados da busca, no período consultado",
        },
        "signals": {"engagement": top["views"] or 0},
    }
