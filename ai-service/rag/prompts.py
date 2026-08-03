"""提示词模板 — 仅按检索上下文回答 + 强制引用来源。"""

SYSTEM_PROMPT = """你是企业知识库「KnowledgeFlow」的智能问答助手。

回答规则：
1. 仅依据下方「知识库内容」回答用户问题，禁止编造知识库外的信息。
2. 若知识库内容不足以回答，直接说明「知识库中没有相关信息」，不要臆测。
3. 引用来源：在相关内容后标注来源，格式为 [来源：文档名 第X页]。
4. 回答使用简体中文，结构清晰、简洁。"""


def build_context(results: list[dict]) -> str:
    """将检索结果组装为带来源的上下文。"""
    parts = []
    for i, r in enumerate(results, 1):
        doc = r.get("documentName", "未知文档")
        page = r.get("page", 1)
        content = r.get("content", "")
        parts.append(f"【来源{i}：{doc} 第{page}页】\n{content}")
    return "\n\n".join(parts)


def build_messages(question: str, history: list[dict] | None, results: list[dict]) -> list[dict]:
    """组装 messages：system + 历史 + 用户问题（含检索上下文）。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 多轮历史（最近若干条，避免超长）
    for item in (history or [])[-6:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    context = build_context(results)
    user_prompt = f"""【知识库内容】
{context}

【用户问题】
{question}

请根据上述知识库内容回答问题，并标注引用来源。"""
    messages.append({"role": "user", "content": user_prompt})
    return messages
