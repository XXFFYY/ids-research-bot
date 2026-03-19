import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

def fetch_openalex(fetch_days: int = 14, per_page: int = 50) -> List[Dict[str, Any]]:
    # 你的5个核心监控关键词（英文即可）
    queries = [
    "multi-agent cybersecurity",
    "llm cybersecurity agent",
    "autonomous incident response",
    "soc automation large language model",
    "threat intelligence reasoning llm",
    ]

    since = (datetime.utcnow().date() - timedelta(days=fetch_days)).isoformat()
    out: List[Dict[str, Any]] = []

    for q in queries:
        url = "https://api.openalex.org/works"
        params = {
            "search": q,
            "filter": f"from_publication_date:{since}",
            "per-page": per_page,
            "sort": "publication_date:desc",
        }
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue

        for w in data.get("results", []):
            title = (w.get("title") or "").strip()
            oa_id = (w.get("id") or "").strip()
            pub = (w.get("publication_date") or "").strip()
            # venue
            host = w.get("host_venue") or {}
            venue = (host.get("display_name") or "").strip()

            # url：尽量给可点击的
            landing = (w.get("primary_location") or {}).get("landing_page_url") or ""
            url2 = landing or oa_id

            out.append({
                "id": oa_id or url2 or title,
                "title": " ".join(title.split()),
                "url": url2,
                "source": "OpenAlex",
                "published": pub,
                "venue": venue,
                "abstract": "",      # OpenAlex 的 abstract 常是 inverted index，这里先留空（你已有 title/venue/时间筛选）
                "extra": "openalex",
            })

    return out