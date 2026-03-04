import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

PWC_SEARCH = "https://paperswithcode.com/api/v1/papers/"

def fetch_pwc(fetch_days: int = 14, page_size: int = 30) -> List[Dict[str, Any]]:
    keywords = [
        "intrusion detection",
        "network anomaly",
        "cybersecurity",
        "federated intrusion detection",
        "distributed intrusion detection",
    ]
    cutoff = datetime.utcnow().date() - timedelta(days=fetch_days)

    out: List[Dict[str, Any]] = []
    for kw in keywords:
        params = {"page": 1, "items_per_page": page_size, "q": kw}
        try:
            r = requests.get(PWC_SEARCH, params=params, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue

        for p in data.get("results", []):
            title = (p.get("title") or "").strip()
            url = (p.get("url") or "").strip()
            abstract = (p.get("abstract") or "").strip()
            published = (p.get("published") or "").strip()

            if published:
                try:
                    d = datetime.fromisoformat(published[:10]).date()
                    if d < cutoff:
                        continue
                except Exception:
                    pass

            out.append({
                "id": ("https://paperswithcode.com" + url) if url and url.startswith("/") else url or title,
                "title": " ".join(title.split()),
                "url": ("https://paperswithcode.com" + url) if url and url.startswith("/") else url,
                "source": "PapersWithCode",
                "published": published[:10] if published else "",
                "venue": "",
                "abstract": " ".join(abstract.split()),
                "extra": "pwc",
            })
    return out