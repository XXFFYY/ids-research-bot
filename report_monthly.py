from datetime import datetime, timedelta

from report_common import BEIJING, load_cfg, fetch_papers_in_range, render_report, llm_trend_summary, push_pushplus

def main():
    cfg = load_cfg()
    today_bj = datetime.now(BEIJING).date()

    # 月报：过去30天
    start = today_bj - timedelta(days=29)
    end = today_bj

    papers, mapping = fetch_papers_in_range(cfg.db_path, start, end)
    stats_md, items_md = render_report(cfg, "月报", start, end, papers, mapping)
    insight = llm_trend_summary(cfg, "月报", start, end, stats_md, items_md)

    md = "\n".join([
        f"# IDS 科研月报（{start.isoformat()} ~ {end.isoformat()}）",
        "",
        stats_md,
        "",
        items_md,
        "",
        insight,
    ])

    title = f"IDS科研月报（{start.isoformat()}~{end.isoformat()}）"
    ok = push_pushplus(cfg.pushplus_token, title, md)
    print("[OK]" if ok else "[WARN]", "monthly pushed")

if __name__ == "__main__":
    main()