import os
from push_pushplus import push_pushplus
from radar import enrich_paper_signals
from datetime import datetime
from config import get_config
from storage import Storage
from sources_arxiv import fetch_arxiv
from sources_semantic import fetch_semantic
from sources_pwc import fetch_pwc
from ranker import rank_and_select
from summarizer import summarize_with_llm
from renderer import render_daily
from translator import translate_title_and_tags, cache_key
from venue_utils import classify_venue
from dedup import canonical_key
from sources_openalex import fetch_openalex


def main():
    cfg = get_config()
    today = datetime.utcnow().date().isoformat()

    st = Storage(cfg.db_path)

    # 1) Fetch
    papers = []

    try:
        a = fetch_arxiv(cfg.fetch_days)
        print(f"[INFO] arXiv fetched: {len(a)}")
        papers += a
    except Exception as e:
        print("[WARN] arXiv fetch failed:", e)

    try:
        s = fetch_semantic(cfg.fetch_days)
        print(f"[INFO] SemanticScholar fetched: {len(s)}")
        papers += s
    except Exception as e:
        print("[WARN] SemanticScholar fetch failed:", e)

    try:
        o = fetch_openalex(cfg.fetch_days)
        print(f"[INFO] OpenAlex fetched: {len(o)}")
        papers += o
    except Exception as e:
        print("[WARN] OpenAlex fetch failed:", e)

    try:
        p = fetch_pwc(max(cfg.fetch_days, 14))
        print(f"[INFO] PWC fetched: {len(p)}")
        papers += p
    except Exception as e:
        print("[WARN] PWC fetch failed:", e)

    if not papers:
        print("[WARN] No papers fetched in first round. Fallback: try arXiv with larger window.")
        try:
            a2 = fetch_arxiv(max(cfg.fetch_days, 14), max_results=200)
            print(f"[INFO] arXiv fallback fetched: {len(a2)}")
            papers += a2
        except Exception as e:
            print("[WARN] arXiv fallback failed:", e)

    if not papers:
        print("[ERROR] No papers fetched.")
        return

    # 2) Store + normalize IDs
    stored = []
    for p in papers:
        # 先用 upsert 得到一个 pid
        pid = st.upsert_paper(p)

        # 再用 canonical_key 做跨源去重绑定
        ck = canonical_key(p.get("title",""), p.get("url",""))
        existing = st.get_paper_id_by_key(ck)
        if existing:
            p["id"] = existing
        else:
            st.bind_key(ck, pid)
            p["id"] = pid

        stored.append(p)

    # 3) Rank & select
    picked = rank_and_select(stored, cfg, cfg.daily_min_items, cfg.daily_max_items)
    picked = [enrich_paper_signals(p) for p in picked]

    # 4) Dedup today + Summarize
    final_items = []
    pushed_ids = []
    for p in picked:
        if st.already_pushed_today(today, p["id"]):
            continue

        summ = summarize_with_llm(p, cfg)
        p["summary_full"] = summ["full"]
        final_items.append(p)
        pushed_ids.append(p["id"])

    if not final_items:
        print("[INFO] Nothing new to push today.")
        return

    # 5) Render + push
    for p in final_items:
        k = cache_key(p.get("title",""), p.get("tags",[]))
        cached = st.get_translation(k)
        if cached:
            p["title_zh"], p["tags_zh"] = cached[0], cached[1]
            continue
        tzh, tags_zh = translate_title_and_tags(p.get("title",""), p.get("tags",[]), cfg)
        p["title_zh"], p["tags_zh"] = tzh, tags_zh
        st.save_translation(k, tzh, tags_zh)
    for p in final_items:
        vtype, level, vzh = classify_venue(p.get("venue",""), p.get("source",""))
        p["venue_type_zh"] = vtype
        p["venue_level_zh"] = level
        p["venue_zh"] = vzh or (p.get("venue","") or "")
    md = render_daily(today, final_items)
    os.makedirs(cfg.archive_dir, exist_ok=True)
    archive_path = os.path.join(cfg.archive_dir, f"daily_{today}.md")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("[INFO] archived:", archive_path)
    st.save_digest(today, md)
    ok = push_pushplus(cfg.pushplus_token, f"今日IDS科研前沿（{today}）", md)

    if ok:
        st.mark_pushed(today, pushed_ids)
        print("[OK] pushed:", len(final_items))
    else:
        print("[WARN] push skipped/failed; digest saved to DB.")

    st.close()

if __name__ == "__main__":
    main()