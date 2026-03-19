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
    lines.append(f"# 本周 多智能体网络安全 趋势总结（截至 {today_str}）\n")
    if not top:
        lines.append("近7天数据不足，建议扩大FETCH_DAYS或检查数据源。")
        return "\n".join(lines)

    lines.append("## 🔥 热点标签 Top10")
    for k, v in top:
        lines.append(f"- {k}: {v}")

    lines.append("\n## 可能的新趋势（粗粒度）")
    lines.append("- 如果 `Multi-Agent Security`、`LLM for Cybersecurity`、`Security Operations / SOC` 同时升温，通常意味着“多智能体安全运营自动化”正在成为热点。")
    lines.append("- 如果 `Threat Intelligence & Reasoning`、`Knowledge Graph / Graph Reasoning` 相关标签升温，说明“威胁情报关联与攻击链推理”在活跃。")
    return "\n".join(lines)