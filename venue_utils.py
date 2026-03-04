import re
from typing import Tuple, Optional

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()

# 你关心的“顶级会议/期刊”白名单（可持续补充）
CONF_MAP_ZH = {
    "neurips": "NeurIPS（神经信息处理系统大会）",
    "icml": "ICML（国际机器学习大会）",
    "iclr": "ICLR（国际学习表征会议）",
    "aaai": "AAAI（人工智能大会）",
    "kdd": "KDD（知识发现与数据挖掘大会）",
    "ijcai": "IJCAI（国际人工智能联合会议）",

    "usenix security": "USENIX Security（USENIX安全大会）",
    "ndss": "NDSS（网络与分布式系统安全研讨会）",
    "acm ccs": "ACM CCS（计算机与通信安全大会）",
    "ccs": "ACM CCS（计算机与通信安全大会）",
    "ieee s&p": "IEEE S&P（安全与隐私）",
    "oakland": "IEEE S&P（安全与隐私）",
    "acsac": "ACSAC（计算机安全应用年会）",
    "raid": "RAID（入侵检测与响应）",
}

JOURNAL_MAP_ZH = {
    "ieee tdsc": "IEEE TDSC（可信与安全计算汇刊）",
    "ieee tifs": "IEEE TIFS（信息取证与安全汇刊）",
    "acm tocs": "ACM TOCS（计算机系统汇刊）",
    "computers & security": "Computers & Security（期刊）",
    "computers and security": "Computers & Security（期刊）",
}

TOP_SECURITY_CONFS = {"usenix security", "ndss", "acm ccs", "ccs", "ieee s&p", "oakland", "acsac", "raid"}
TOP_ML_CONFS = {"neurips", "icml", "iclr", "aaai", "kdd", "ijcai"}
TOP_JOURNALS = {"ieee tdsc", "ieee tifs", "acm tocs", "computers & security", "computers and security"}

def classify_venue(venue: str, source: str) -> Tuple[str, str, Optional[str]]:
    """
    返回：类型中文、水平中文、中文venue名(可为空)
    类型：期刊/会议/预印本/未知
    水平：安全顶会/ML顶会/顶刊/一般/预印本/未知
    """
    v = _norm(venue)
    s = _norm(source)

    # 1) 类型判断
    if "arxiv" in s or v == "arxiv":
        vtype = "预印本"
        level = "预印本"
        vzh = "arXiv（预印本）"
        return vtype, level, vzh

    # 2) 会议/期刊白名单匹配（优先）
    # 会议
    for key, zh in CONF_MAP_ZH.items():
        if key in v:
            vtype = "会议"
            if key in TOP_SECURITY_CONFS:
                level = "安全顶会"
            elif key in TOP_ML_CONFS:
                level = "ML/AI顶会"
            else:
                level = "会议"
            return vtype, level, zh

    # 期刊
    for key, zh in JOURNAL_MAP_ZH.items():
        if key in v:
            vtype = "期刊"
            level = "顶刊" if key in TOP_JOURNALS else "期刊"
            return vtype, level, zh

    # 3) 兜底（规则猜测）
    # Semantic Scholar 有时 venue 会是期刊名/会议简称混杂
    if any(x in v for x in ["transactions", "journal", "ieee", "acm", "springer", "elsevier"]):
        return "期刊", "期刊", venue or None
    if any(x in v for x in ["conference", "proceedings", "symposium", "workshop"]):
        return "会议", "会议", venue or None

    # 4) 未知
    return "未知", "未知", venue or None