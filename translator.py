import requests
import hashlib

def _hid(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()

def translate_title_and_tags(title: str, tags: list[str], cfg) -> tuple[str, list[str]]:
    """
    返回：中文标题, 中文标签列表
    """
    if not cfg.openai_api_key:
        return title, tags

    tags_text = ", ".join(tags)
    prompt = f"""
请把下面内容翻译成中文，要求：学术风格、准确、简洁。
1) 论文标题翻译（不要加解释）
2) 标签翻译（逐个翻译，保持短语）

输出格式严格为JSON：
{{
  "title_zh": "...",
  "tags_zh": ["...","..."]
}}

标题：
{title}

标签：
{tags_text}
""".strip()

    url = cfg.openai_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.openai_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": cfg.openai_model,
        "messages": [
            {"role": "system", "content": "你是严谨的学术翻译助手，只输出JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=45)
    if r.status_code != 200:
        return title, tags

    content = r.json()["choices"][0]["message"]["content"].strip()
    # 尝试解析JSON（简单容错：去掉可能的代码块）
    content = content.strip("`").strip()
    import json
    try:
        obj = json.loads(content)
        tzh = obj.get("title_zh") or title
        tags_zh = obj.get("tags_zh") or tags
        return tzh, tags_zh
    except Exception:
        return title, tags

def cache_key(title: str, tags: list[str]) -> str:
    return _hid(title + "||" + ",".join(tags))