import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"

def fetch_semantic(fetch_days: int = 7, limit: int = 40) -> List[Dict[str, Any]]:
    # 用关键词召回，优先近1-3年；S2支持year过滤
    # 注意：S2无key也可用但有速率限制；小规模每天一次基本OK
    today = datetime.utcnow().date()
    year_from = (today - timedelta(days=365*3)).year

    queries = [
        "Intrusion Detection",
        "Network Anomaly Detection",
        "Distributed IDS",
        "Federated Intrusion Detection",
        "AI for Cybersecurity IDS",
    ]

    fields = "title,abstract,url,venue,year,publicationDate"
    out = []
    for q in queries:
        params = {
            "query": q,
            "limit": limit,
            "fields": fields,
            "year": f"{year_from}-",
        }
        r = requests.get(S2_SEARCH, params=params, timeout=20)
        if r.status_code != 200:
            continue
        data = r.json()
        for p in data.get("data", []):
            title = (p.get("title") or "").strip()
            abstract = (p.get("abstract") or "").strip()
            url = (p.get("url") or "").strip()
            venue = (p.get("venue") or "").strip()
            pub = p.get("publicationDate") or ""
            year = p.get("year") or ""
            published = pub if pub else (f"{year}-01-01" if year else "")

            out.append({
                "id": url or (title + str(year)),
                "title": " ".join(title.split()),
                "url": url,
                "source": "SemanticScholar",
                "published": published,
                "venue": venue,
                "abstract": " ".join(abstract.split()),
                "extra": "",
            })
    return out