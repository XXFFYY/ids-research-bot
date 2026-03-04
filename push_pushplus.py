import requests

def push_pushplus(token: str, title: str, content: str) -> bool:
    """
    PushPlus 推送（微信公众号消息）
    content: 支持 Markdown / 文本（PushPlus 会渲染）
    """
    if not token:
        return False

    url = "http://www.pushplus.plus/send"
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",  # 用markdown更适合你的论文格式
    }
    r = requests.post(url, json=payload, timeout=20)
    return r.status_code == 200 and (r.json().get("code") == 200)