import requests
from typing import Dict, Any

def summarize_with_llm(p: Dict[str, Any], cfg) -> Dict[str, str]:
    title = p.get("title","")
    abstract = p.get("abstract","")
    tags = ", ".join(p.get("tags",[]))

    # 没有key则fallback
    if not cfg.openai_api_key:
        return fallback_summary(p)
    radar_flags = ", ".join(p.get("radar_flags", [])) or "无"
    gh_links = p.get("github_links", [])
    gh_text = "\n".join(gh_links[:3]) if gh_links else "无"

    prompt = f"""
你是“多智能体网络安全 + 安全运营自动化”方向的科研助理。
请基于以下论文信息，生成中文结构化摘要，用于每日科研前沿推送。

【标题】
{title}

【摘要】
{abstract}

【命中的标签】
{tags}

【雷达信号（dataset/benchmark/code/survey）】
{radar_flags}

【可能的GitHub链接】
{gh_text}

请严格按以下6项输出（每项1-3句，简洁、信息密度高）：
1️⃣ 研究问题
2️⃣ 核心方法
3️⃣ 关键实验/数据集/评估（若未知就说“摘要未说明”）
4️⃣ 与“多智能体协同安全分析 / SOC自动化 / 威胁情报推理 / 事件响应自动化”的关系（务必具体）
5️⃣ 对我研究“类MetaGPT框架在网络安全中的应用”的启发/可复用点
6️⃣ 数据集/代码/benchmark 可复用点（若有，请明确点出并说明；若无则写‘摘要未说明’。）

如果论文与网络安全关系较弱，但在 agent workflow / planning / reflection / tool use / multi-agent coordination 上有借鉴价值，也请明确指出。
""".strip()

    url = cfg.openai_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.openai_model,
        "messages": [
            {"role": "system", "content": "你输出要专业、克制、可读性强。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=45)
    if r.status_code != 200:
        return fallback_summary(p)

    data = r.json()
    content = data["choices"][0]["message"]["content"].strip()
    return {"full": content}

def fallback_summary(p: Dict[str, Any]) -> Dict[str, str]:
    # 极省资源降级摘要：不调用LLM
    title = p.get("title","")
    tags = ", ".join(p.get("tags",[])) or "未命中标签"
    abstract = (p.get("abstract","") or "").strip()
    abstract_short = (abstract[:260] + "…") if len(abstract) > 260 else abstract

    content = f"""1️⃣ 研究问题：围绕 {tags} 的智能体协作/安全分析问题（摘要未用LLM精读）。
2️⃣ 核心方法：摘要未说明细节（建议查看原文中的 agent 角色设计、工具调用、RAG 或 workflow 部分）。
3️⃣ 关键实验/评估：摘要未说明。
4️⃣ 与我的研究关系：可能与“多智能体协同安全分析、SOC自动化、威胁情报推理、事件响应自动化”相关，建议优先看系统框架与实验部分。
5️⃣ 启发：可关注任务拆解、角色分工、记忆机制、工具使用、校验/反思机制。
（摘要片段：{abstract_short}）
"""
    return {"full": content}