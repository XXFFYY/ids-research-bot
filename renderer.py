from typing import List, Dict, Any
from datetime import date

def render_daily(date_str: str, items: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append(f"# 今日 IDS / AI安全 科研前沿（{date_str}）")
    lines.append("")
    lines.append("> 覆盖：IDS｜AI+安全｜分布式协同IDS｜通信效率学习｜联邦学习安全（优先1–3年新进展）")
    lines.append("")


    for i, p in enumerate(items, 1):
        title = p.get("title","").strip()
        title_zh = (p.get("title_zh") or "").strip()
        show_title = f"{title_zh}\n\n**{title}**" if title_zh and title_zh != title else title
        
        tags = ", ".join(p.get("tags",[]))
        tags_zh = ", ".join(p.get("tags_zh",[]))
        url = p.get("url","").strip()
        src = p.get("source","")
        pub = p.get("published","")
        venue = p.get("venue","") or ""

        summary = p.get("summary_full","").strip()

        lines.append(f"---\n## {i}️⃣ {show_title}")

        vtype = p.get("venue_type_zh", "未知")
        level = p.get("venue_level_zh", "未知")
        vzh = p.get("venue_zh", "")  # 中文venue名（或原venue）

        # 示例：- 类型/水平：会议｜安全顶会  - 发表：USENIX Security（USENIX安全大会）  - 日期：2026-03-04
        lines.append(f"- 类型/水平：{vtype}｜{level}")
        if vzh:
            lines.append(f"- 发表：{vzh}")
        lines.append(f"- 日期：{pub} ｜来源：{src}")
        if tags_zh:
            lines.append(f"- 标签：`{tags_zh}`（{tags}）")
        elif tags:
            lines.append(f"- 标签：`{tags}`")
        lines.append("")
        lines.append(summary)
        lines.append("")
        if url:
            lines.append(f"论文链接：{url}")
        lines.append("")
        radar_flags = ", ".join(p.get("radar_flags", []))
        gh_links = p.get("github_links", [])

        if radar_flags:
            lines.append(f"- 雷达信号：**{radar_flags}**")

        if gh_links:
            lines.append("- 可能的开源链接：")
            for link in gh_links[:3]:
                lines.append(f"  - {link}")

    return "\n".join(lines)