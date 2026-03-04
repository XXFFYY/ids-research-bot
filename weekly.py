from collections import Counter
from typing import List, Dict, Any
from datetime import datetime, timedelta

def render_weekly_trend(today_str: str, recent_papers: List[Dict[str, Any]]) -> str:
    # 统计tags热度（近7天）
    # recent_papers来自SQLite，可能包含更久；这里只做近7天粗过滤（按published字符串前10位）
    cutoff = (datetime.utcnow().date() - timedelta(days=7)).isoformat()
    tags = []
    for p in recent_papers:
        pub = (p.get("published") or "")[:10]
        if pub and pub >= cutoff:
            tags.extend(p.get("tags",[]) if isinstance(p.get("tags",[]), list) else [])
    c = Counter(tags)
    top = c.most_common(10)

    lines = []
    lines.append(f"# 本周 IDS/AI安全 趋势总结（截至 {today_str}）\n")
    if not top:
        lines.append("近7天数据不足，建议扩大FETCH_DAYS或检查数据源。")
        return "\n".join(lines)

    lines.append("## 🔥 热点标签 Top10")
    for k, v in top:
        lines.append(f"- {k}: {v}")

    lines.append("\n## 可能的新趋势（粗粒度）")
    lines.append("- 如果 `Distributed/Collaborative IDS`、`Comm-efficient Learning`、`Federated Security` 同时升温，通常意味着“协同检测 + 低通信代价”成为热点。")
    lines.append("- 如果 `adversarial/robust` 相关标签升温，说明“对抗攻击/鲁棒IDS”在活跃。")
    return "\n".join(lines)