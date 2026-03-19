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
    
    boost_flags = {
    "dataset": ["dataset", "data set", "benchmark"],
    "code": ["code", "github", "open source", "repository"],
    "survey": ["survey", "tutorial", "systematic review"],
    }

    # 你的重点关键词（核心5个 + 扩展）
    core_keywords = [
    "multi-agent cybersecurity",
    "llm for cybersecurity",
    "security agent",
    "autonomous incident response",
    "soc automation",
    ]

    primary_areas = {
    "Multi-Agent Security": [
        "multi-agent", "multi agent", "llm agent", "language agent",
        "agentic", "agent-based", "multi-agent system", "collaborative agent",
    ],
    "Security Operations / SOC": [
        "soc", "security operations", "security operation center",
        "alert triage", "incident response", "security orchestration",
        "analyst copilot", "security assistant",
    ],
    "Threat Intelligence & Reasoning": [
        "threat intelligence", "ioc", "ttp", "attack chain",
        "mitre att&ck", "attack graph", "threat hunting",
        "reasoning", "cyber reasoning",
    ],
    "LLM for Cybersecurity": [
        "large language model", "llm", "retrieval-augmented generation",
        "rag", "tool use", "planning", "reflection", "self-correction",
    ],
    "Cyber Defense Automation": [
        "autonomous defense", "automated response", "defensive agent",
        "security workflow", "playbook", "orchestration", "verification",
    ],
    }

    secondary_areas = {
    "Benchmark/Dataset": [
        "benchmark", "dataset", "evaluation", "leaderboard",
    ],
    "Agent Memory/Planning": [
        "memory", "planner", "planning", "task decomposition",
        "coordination", "workflow",
    ],
    "Knowledge Graph / Graph Reasoning": [
        "knowledge graph", "graph reasoning", "attack graph",
        "graph neural", "graph-based",
    ],
    }

def get_config() -> Config:
    cfg = Config()
    if not cfg.openai_api_key:
        print("[WARN] OPENAI_API_KEY is empty. Summarization will fallback to heuristic.")
    if not cfg.pushplus_token:
        print("[WARN] PUSHPLUS_TOKEN is empty. PushPlus push will be skipped.")
    return cfg