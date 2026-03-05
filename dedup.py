import re
import hashlib

ARXIV_RE = re.compile(r"arxiv\.org/(abs|pdf)/(\d{4}\.\d{4,5})(v\d+)?", re.I)

def normalize_title(title: str) -> str:
    t = (title or "").lower().strip()
    t = re.sub(r"[\W_]+", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_arxiv_id(url: str) -> str | None:
    if not url:
        return None
    m = ARXIV_RE.search(url)
    if not m:
        return None
    return m.group(2)

def canonical_key(title: str, url: str) -> str:
    arx = get_arxiv_id(url)
    if arx:
        return f"arxiv:{arx}"
    nt = normalize_title(title)
    h = hashlib.sha256(nt.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"title:{h}"