import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    fetch_days: int = int(os.getenv("FETCH_DAYS", "7"))
    daily_min_items: int = int(os.getenv("DAILY_MIN_ITEMS", "3"))
    daily_max_items: int = int(os.getenv("DAILY_MAX_ITEMS", "5"))

    db_path: str = os.getenv("DB_PATH", "./data/bot.db").strip()
    pushplus_token: str = os.getenv("PUSHPLUS_TOKEN", "").strip()
    archive_dir: str = os.getenv("ARCHIVE_DIR", "./archive").strip()

    recent_months: int = int(os.getenv("RECENT_MONTHS", "18"))

    # 你的重点关键词（核心5个 + 扩展）
    core_keywords = [
        "intrusion detection",
        "anomaly detection",
        "distributed ids",
        "federated security",
        "ai for cybersecurity",
    ]

    primary_areas = {
        "IDS": [
            "intrusion detection", "network intrusion", "ids",
            "network security", "network traffic", "traffic analysis",
            "anomaly detection", "malware", "botnet",
        ],
        "AI+Security": [
            "ai for cybersecurity", "machine learning", "deep learning",
            "adversarial", "evasion", "poisoning", "robust",
        ],
        "Distributed/Collaborative IDS": [
            "distributed ids", "collaborative ids", "multi-agent",
            "multi agent", "federated", "collaborative detection",
            "feature partition", "information fusion",
        ],
        "Comm-efficient Learning": [
            "communication-efficient", "compression", "quantization",
            "sketch", "distillation", "low bandwidth", "feature compression",
        ],
        "Federated Security": [
            "federated learning", "privacy-preserving", "secure aggregation",
            "differential privacy", "federated ids", "federated security",
        ],
    }

    secondary_areas = {
        "Transformer/Attention": [
            "transformer", "attention", "self-attention",
        ],
        "GNN/Security": [
            "graph neural", "gnn", "graph-based",
        ],
        "Tabular ML": [
            "tabular", "xgboost", "lightgbm", "catboost",
        ],
    }

    boost_flags = {
        "dataset": ["dataset", "data set", "benchmark"],
        "code": ["code", "github", "open source", "repository"],
        "survey": ["survey", "tutorial", "systematic review"],
    }

def get_config() -> Config:
    cfg = Config()
    if not cfg.openai_api_key:
        print("[WARN] OPENAI_API_KEY is empty. Summarization will fallback to heuristic.")
    if not cfg.pushplus_token:
        print("[WARN] PUSHPLUS_TOKEN is empty. PushPlus push will be skipped.")
    return cfg