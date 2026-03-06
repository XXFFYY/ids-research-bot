from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from report_common import BEIJING, load_cfg, fetch_papers_in_range, render_report, llm_trend_summary, push_pushplus

def main():
    cfg = load_cfg()
    today_bj = datetime.now(BEIJING).date()
    # 周报：过去7天（含今天-6到今天）
    start = today_bj - timedelta(days=6)
    end = today_bj

    papers, mapping = fetch_papers_in_range(cfg.db_path, start, end)
    stats_md, items_md = render_report(cfg, "周报", start, end, papers, mapping)
    insight = llm_trend_summary(cfg, "周报", start, end, stats_md, items_md)

    md = "\n".join([
        f"# IDS 科研周报（{start.isoformat()} ~ {end.isoformat()}）",
        "",
        stats_md,
        "",
        items_md,
        "",
        insight,
    ])

    title = f"IDS科研周报（{start.isoformat()}~{end.isoformat()}）"
    ok = push_pushplus(cfg.pushplus_token, title, md)
    print("[OK]" if ok else "[WARN]", "weekly pushed")

if __name__ == "__main__":
    main()