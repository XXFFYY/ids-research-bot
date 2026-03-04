import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import urllib.parse

ARXIV_API = "http://export.arxiv.org/api/query"

def fetch_arxiv(fetch_days: int = 7, max_results: int = 80) -> List[Dict[str, Any]]:
    # 拉取最近N天，分类：cs.CR / cs.LG / cs.AI
    # arXiv API不直接支持“最近N天”过滤到非常精准，我们用 lastUpdatedDate 排序 + 拉取一定量再本地过滤
    search_query = "cat:cs.CR OR cat:cs.LG OR cat:cs.AI"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    feed = feedparser.parse(url)

    cutoff = datetime.now(timezone.utc) - timedelta(days=fetch_days)
    out = []
    for e in feed.entries:
        # updated/published are RFC3339
        published = datetime.fromisoformat(e.published.replace("Z", "+00:00"))
        updated = datetime.fromisoformat(e.updated.replace("Z", "+00:00"))
        if updated < cutoff and published < cutoff:
            continue

        out.append({
            "id": getattr(e, "id", ""),
            "title": " ".join(getattr(e, "title", "").split()),
            "url": getattr(e, "link", ""),
            "source": "arXiv",
            "published": published.date().isoformat(),
            "venue": "arXiv",
            "abstract": " ".join(getattr(e, "summary", "").split()),
            "extra": "",
        })
    return out