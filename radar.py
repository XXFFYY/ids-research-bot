import re
from typing import Dict, Any, List

GITHUB_RE = re.compile(r"(https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")

def extract_github_links(text: str) -> List[str]:
    if not text:
        return []
    links = GITHUB_RE.findall(text)
    # 去重保持顺序
    seen = set()
    out = []
    for x in links:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out

def enrich_paper_signals(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    超轻量增强：
    - 从 abstract/title 里提取 GitHub
    - 标注 “dataset/benchmark/code/survey” 强信号
    """
    title = (p.get("title") or "").lower()
    abstract = (p.get("abstract") or "").lower()
    text = f"{title} {abstract}"

    flags = []
    if any(k in text for k in ["dataset", "data set", "benchmark"]):
        flags.append("dataset/benchmark")
    if any(k in text for k in ["github", "open source", "repository", "code available", "code"]):
        flags.append("code")
    if any(k in text for k in ["survey", "tutorial", "systematic review", "comprehensive review"]):
        flags.append("survey")

    gh = extract_github_links(p.get("abstract","")) + extract_github_links(p.get("extra",""))
    p2 = dict(p)
    p2["radar_flags"] = flags
    p2["github_links"] = gh
    return p2