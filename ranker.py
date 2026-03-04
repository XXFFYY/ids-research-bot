from typing import Dict, Any, List, Tuple
import re
from datetime import datetime, timedelta

def is_recent_enough(published: str, recent_months: int) -> bool:
    if not published:
        return True  # 没日期的先放行，后面会在 scoring 里降权
    try:
        d = datetime.fromisoformat(published[:10]).date()
    except Exception:
        return True
    cutoff = (datetime.utcnow().date() - timedelta(days=30 * recent_months))
    return d >= cutoff

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

def score_paper(p: Dict[str, Any], cfg) -> Tuple[float, Dict[str, Any]]:
    title = _norm(p.get("title",""))
    abstract = _norm(p.get("abstract",""))
    text = f"{title} {abstract}"

    score = 0.0
    tags = []

    # 核心5关键词强加权
    for kw in cfg.core_keywords:
        if kw in text:
            score += 5.0
            tags.append(kw)

    # 一级领域权重（你的核心研究）
    for area, kws in cfg.primary_areas.items():
        hit = sum(1 for k in kws if _norm(k) in text)
        if hit:
            score += 4.0 + 0.8 * hit
            tags.append(area)

    # 二级领域权重
    for area, kws in cfg.secondary_areas.items():
        hit = sum(1 for k in kws if _norm(k) in text)
        if hit:
            score += 1.5 + 0.4 * hit
            tags.append(area)

    # “数据集/benchmark/代码/survey”额外加权
    for flag, kws in cfg.boost_flags.items():
        if any(_norm(k) in text for k in kws):
            score += 3.0
            tags.append(flag)

    # source微调：PWC更偏代码/benchmark信号；arXiv更新快
    src = (p.get("source","") or "").lower()
    if "paperswithcode" in src:
        score += 0.8
    if "arxiv" in src:
        score += 0.4

    meta = {"score": score, "tags": sorted(set(tags))}
    pub = (p.get("published") or "")[:10]
    try:
        d = datetime.fromisoformat(pub).date()
        days_ago = (datetime.utcnow().date() - d).days
        # 0-30天 +4 分，30-180天 +2 分，180-540天 +1 分
        if days_ago <= 30:
            score += 4.0
        elif days_ago <= 180:
            score += 2.0
        elif days_ago <= 540:
            score += 1.0
    except Exception:
        # 没有日期/解析失败：不加分（相对靠后）
        pass
    return score, meta

def rank_and_select(papers: List[Dict[str, Any]], cfg, k_min: int, k_max: int) -> List[Dict[str, Any]]:
    papers = [p for p in papers if is_recent_enough(p.get("published",""), cfg.recent_months)]
    scored = []
    for p in papers:
        s, meta = score_paper(p, cfg)
        p2 = dict(p)
        p2["score"] = s
        p2["tags"] = meta["tags"]
        scored.append(p2)

    scored.sort(key=lambda x: (x.get("score",0), x.get("published","")), reverse=True)

    # 选Top，但尽量覆盖多个方向（简单多样性策略）
    picked = []
    seen_areas = set()
    for p in scored:
        if len(picked) >= k_max:
            break
        areas = [t for t in p.get("tags",[]) if t in cfg.primary_areas or t in cfg.secondary_areas]
        key_area = areas[0] if areas else "Other"

        if key_area not in seen_areas or len(picked) < k_min:
            picked.append(p)
            seen_areas.add(key_area)

    # 不足则补齐
    if len(picked) < k_min:
        for p in scored:
            if p in picked:
                continue
            picked.append(p)
            if len(picked) >= k_min:
                break

    return picked[:k_max]