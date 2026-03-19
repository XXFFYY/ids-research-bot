import os
import json
import sqlite3
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv

BEIJING = ZoneInfo("Asia/Shanghai")

@dataclass
class Cfg:
    db_path: str
    pushplus_token: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str

def load_cfg() -> Cfg:
    load_dotenv()
    return Cfg(
        db_path=os.getenv("DB_PATH", "./data/bot.db").strip(),
        pushplus_token=os.getenv("PUSHPLUS_TOKEN", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "deepseek-chat").strip(),
    )

def push_pushplus(token: str, title: str, content_md: str) -> bool:
    if not token:
        print("[WARN] PUSHPLUS_TOKEN empty, skip push.")
        return False
    url = "http://www.pushplus.plus/send"
    payload = {"token": token, "title": title, "content": content_md, "template": "markdown"}
    r = requests.post(url, json=payload, timeout=30)
    ok = r.status_code == 200 and (r.json().get("code") == 200)
    if not ok:
        print("[WARN] PushPlus failed:", r.status_code, r.text[:300])
    return ok

def report_title_key(title_en: str) -> str:
    t = (title_en or "").strip().lower()
    h = hashlib.sha256(t.encode("utf-8", errors="ignore")).hexdigest()[:24]
    return f"report_title:{h}"

def get_title_zh(conn: sqlite3.Connection, title_en: str) -> str | None:
    key = report_title_key(title_en)
    cur = conn.execute("SELECT title_zh FROM translations WHERE key=? LIMIT 1", (key,))
    row = cur.fetchone()
    return row[0] if row and row[0] else None

def save_title_zh(conn: sqlite3.Connection, title_en: str, title_zh: str):
    key = report_title_key(title_en)
    conn.execute(
        "INSERT OR REPLACE INTO translations(key, title_zh, tags_zh, created_at) VALUES (?, ?, ?, ?)",
        (key, title_zh, "", datetime.utcnow().isoformat())
    )
    conn.commit()

def translate_titles_batch(cfg: Cfg, titles_en: List[str]) -> Dict[str, str]:
    """
    批量翻译标题：
    - 先查 translations 缓存
    - 缺失的再调用一次 DeepSeek
    - 翻译结果写回 translations
    """
    titles_en = [t.strip() for t in titles_en if t and t.strip()]
    if not titles_en:
        return {}

    conn = sqlite3.connect(cfg.db_path)
    out: Dict[str, str] = {}
    missing: List[str] = []

    try:
        for t in titles_en:
            cached = get_title_zh(conn, t)
            if cached:
                out[t] = cached
            else:
                missing.append(t)

        if not missing:
            return out

        if not cfg.openai_api_key:
            return out

        items = [{"id": i + 1, "title_en": t} for i, t in enumerate(missing)]
        prompt = f"""
请把下面这些论文标题翻译成中文，要求：
1. 准确
2. 学术风格
3. 简洁
4. 不要添加解释

请严格输出 JSON 数组，格式如下：
[
  {{"id": 1, "title_zh": "..."}},
  {{"id": 2, "title_zh": "..."}}
]

输入：
{json.dumps(items, ensure_ascii=False)}
""".strip()

        url = cfg.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {cfg.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cfg.openai_model,
            "messages": [
                {"role": "system", "content": "你是严谨的学术翻译助手，只输出JSON数组。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code != 200:
            return out

        content = r.json()["choices"][0]["message"]["content"].strip()
        content = content.strip("`").strip()

        arr = json.loads(content)
        id2zh = {
            int(x["id"]): (x.get("title_zh") or "").strip()
            for x in arr
            if "id" in x
        }

        for i, t in enumerate(missing, 1):
            zh = id2zh.get(i, "")
            if zh:
                out[t] = zh
                save_title_zh(conn, t, zh)

        return out
    except Exception:
        return out
    finally:
        conn.close()
    
def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]  # name at index 1

def _pick_col(cols: List[str], candidates: List[str]) -> str | None:
    s = set([c.lower() for c in cols])
    for c in candidates:
        if c.lower() in s:
            # return original casing
            for cc in cols:
                if cc.lower() == c.lower():
                    return cc
    return None

def fetch_papers_in_range(db_path: str, start: date, end: date) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    拉取 [start, end] 之间的论文。字段名可能因版本不同而不同，本函数自适应。
    返回：papers列表、字段映射信息（用于debug）
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cols = _table_columns(conn, "papers")
    # 常见字段名的兼容映射
    col_id = _pick_col(cols, ["id", "paper_id"])
    col_title = _pick_col(cols, ["title"])
    col_url = _pick_col(cols, ["url", "link"])
    col_source = _pick_col(cols, ["source"])
    col_venue = _pick_col(cols, ["venue"])
    col_published = _pick_col(cols, ["published", "publication_date", "pub_date", "date"])
    col_abstract = _pick_col(cols, ["abstract"])
    col_tags = _pick_col(cols, ["tags"])
    col_radar = _pick_col(cols, ["radar_flags", "flags"])

    if not col_title or not col_published:
        raise RuntimeError(f"papers表缺少必要字段：title/published. 当前列={cols}")

    # 日期字段通常是 "YYYY-MM-DD"；用字符串比较即可（同格式）
    start_s = start.isoformat()
    end_s = end.isoformat()

    select_cols = [c for c in [col_id, col_title, col_url, col_source, col_venue, col_published, col_abstract, col_tags, col_radar] if c]
    q = f"""
    SELECT {", ".join(select_cols)}
    FROM papers
    WHERE substr({col_published}, 1, 10) >= ? AND substr({col_published}, 1, 10) <= ?
    """
    rows = conn.execute(q, (start_s, end_s)).fetchall()
    conn.close()

    papers: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        papers.append(d)

    mapping = {
        "id": col_id or "",
        "title": col_title,
        "url": col_url or "",
        "source": col_source or "",
        "venue": col_venue or "",
        "published": col_published,
        "abstract": col_abstract or "",
        "tags": col_tags or "",
        "radar_flags": col_radar or "",
    }
    return papers, mapping

def normalize_title(title: str) -> str:
    t = (title or "").strip().lower()
    # 轻量归一：去多空格
    t = " ".join(t.split())
    return t

def dedup_by_title(papers: List[Dict[str, Any]], title_key: str) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for p in papers:
        k = normalize_title(p.get(title_key, ""))
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out

def top_k(papers: List[Dict[str, Any]], k: int, published_key: str) -> List[Dict[str, Any]]:
    # 没有 score 字段就按日期倒序；有 score 则优先 score
    def parse_date(s: str) -> str:
        return (s or "")[:10]
    has_score = any("score" in (x.lower() for x in papers[0].keys()) for _ in [0]) if papers else False

    if has_score:
        # 找出真实 score 列名（大小写兼容）
        score_key = None
        for kk in papers[0].keys():
            if kk.lower() == "score":
                score_key = kk
                break
        papers_sorted = sorted(
            papers,
            key=lambda p: (float(p.get(score_key, 0) or 0), parse_date(p.get(published_key, ""))),
            reverse=True
        )
    else:
        papers_sorted = sorted(papers, key=lambda p: parse_date(p.get(published_key, "")), reverse=True)

    return papers_sorted[:k]

def count_tokens_rough(text: str) -> int:
    # 粗略：按字符估计，避免喂给LLM过长
    return len(text)

def llm_trend_summary(cfg: Cfg, scope_name: str, start: date, end: date, stats_md: str, items_md: str) -> str:
    """
    只调用一次 LLM：根据统计+top列表输出“趋势洞察”，要求不胡编。
    """
    if not cfg.openai_api_key:
        return "（未配置 DeepSeek API Key，趋势洞察跳过）"

    # 控制输入长度，避免成本飙升
    blob = f"{stats_md}\n\n{items_md}"
    if count_tokens_rough(blob) > 24000:
        blob = blob[:24000] + "\n\n（内容过长已截断）"

    prompt = f"""
    你是网络安全与智能体系统方向的科研情报分析员。请基于我提供的“统计摘要 + Top论文列表”，用中文输出 {scope_name} 的研究趋势洞察。
    要求：
    - 只能使用提供的信息推断，不要编造不存在的论文、指标或结论。
    - 输出要落地：指出可能的热点方向、常见方法组合、数据集/benchmark/开源趋势、以及对“多智能体安全分析、SOC自动化、威胁情报关联、事件响应自动化”的启示。
    - 如果信息不足以支持某结论，请明确说“样本不足/信息不足”。

    输出格式（Markdown）：
    ### 趋势洞察（{start.isoformat()} ~ {end.isoformat()}）
    1. 热点方向（2-4条）
    2. 方法信号（2-4条）
    3. 数据集/Benchmark/开源（如有则列出1-3条；没有则说明缺失）
    4. 对“类MetaGPT安全框架研究”的可行动建议（3条，尽量具体）

    下面是输入数据：
    {blob}
    """.strip()

    url = cfg.openai_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.openai_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": cfg.openai_model,
        "messages": [
            {"role": "system", "content": "你输出必须严谨，避免幻觉。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        return f"（趋势洞察生成失败：HTTP {r.status_code}）"

    return r.json()["choices"][0]["message"]["content"].strip()

def render_report(cfg: Cfg, scope_name: str, start: date, end: date, papers: List[Dict[str, Any]], mapping: Dict[str, str]) -> str:
    title_key = mapping["title"]
    pub_key = mapping["published"]
    url_key = mapping["url"]
    source_key = mapping["source"]
    venue_key = mapping["venue"]

    # 轻量去重
    papers_u = dedup_by_title(papers, title_key)

    # 统计
    total = len(papers_u)
    by_source: Dict[str, int] = {}
    by_venue: Dict[str, int] = {}
    for p in papers_u:
        by_source[p.get(source_key, "Unknown") or "Unknown"] = by_source.get(p.get(source_key, "Unknown") or "Unknown", 0) + 1
        v = (p.get(venue_key, "") or "").strip()
        if v:
            by_venue[v] = by_venue.get(v, 0) + 1

    top_sources = sorted(by_source.items(), key=lambda x: x[1], reverse=True)[:6]
    top_venues = sorted(by_venue.items(), key=lambda x: x[1], reverse=True)[:8]

    stats_md = []
    stats_md.append(f"## 统计概览（{start.isoformat()} ~ {end.isoformat()}）")
    stats_md.append(f"- 去重后论文数：**{total}**")
    if top_sources:
        stats_md.append("- 来源分布：")
        for k, v in top_sources:
            stats_md.append(f"  - {k}: {v}")
    if top_venues:
        stats_md.append("- 高频Venue（粗统计）：")
        for k, v in top_venues:
            stats_md.append(f"  - {k}: {v}")
    stats_md_s = "\n".join(stats_md)

    # Top 列表
    top_items = top_k(papers_u, 12 if scope_name == "周报" else 20, pub_key)
    items_md = []
    items_md.append("## Top 论文（中文标题 + 英文标题）")
    items_md.append("")

    titles = [(p.get(title_key, "") or "").strip() for p in top_items]
    tmap = translate_titles_batch(cfg, titles)

    for i, p in enumerate(top_items, 1):
        t = (p.get(title_key, "") or "").strip()
        tzh = tmap.get(t, "")

        d = (p.get(pub_key, "") or "")[:10]
        u = (p.get(url_key, "") or "").strip()
        src = (p.get(source_key, "") or "").strip()
        ven = (p.get(venue_key, "") or "").strip()

        if tzh and tzh != t:
            items_md.append(f"{i}. **{tzh}**")
            items_md.append("")
            items_md.append(f"*{t}*")
        else:
            items_md.append(f"{i}. **{t}**")

        meta = []
        if d:
            meta.append(d)
        if ven:
            meta.append(ven)
        if src:
            meta.append(src)
        if meta:
            items_md.append(f"- {' | '.join(meta)}")
        if u:
            items_md.append(f"- 链接：{u}")

        items_md.append("")

    items_md_s = "\n".join(items_md)

    return stats_md_s, items_md_s