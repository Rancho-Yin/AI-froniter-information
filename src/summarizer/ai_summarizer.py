"""
AI Summarizer – uses the Claude API to generate:

  1. An overall AI development summary paragraph (Chinese + English).
  2. Per-section highlights when needed.
"""

import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


def _build_digest_context(
    papers: list[dict],
    feeds: dict[str, list[dict]],
) -> str:
    """Build a compact text representation of all collected content."""
    lines: list[str] = []

    if papers:
        lines.append("=== 最新 arXiv 论文 ===")
        for p in papers[:10]:
            lines.append(f"• [{p['category_label']}] {p['title']} ({p['published']})")
            lines.append(f"  摘要: {p['summary'][:200]}")

    for category, label in [
        ("intl_news", "国际 AI 资讯"),
        ("cn_news", "国内 AI 资讯"),
        ("hardware", "AI 硬件 / 算力"),
        ("papers", "HF / PWC 论文"),
    ]:
        items = feeds.get(category, [])
        if items:
            lines.append(f"\n=== {label} ===")
            for item in items[:8]:
                lines.append(f"• [{item['source']}] {item['title']} ({item['published']})")
                if item.get("summary"):
                    lines.append(f"  {item['summary'][:150]}")

    return "\n".join(lines)


def generate_overall_summary(
    papers: list[dict],
    feeds: dict[str, list[dict]],
    model: str = "claude-opus-4-6",
    max_tokens: int = 2000,
    api_key: Optional[str] = None,
) -> str:
    """
    Call Claude to produce a 300-500 word overall AI development summary
    in Chinese, covering today's most important trends across research,
    industry, and hardware.
    """
    context = _build_digest_context(papers, feeds)

    system_prompt = (
        "你是一位专注于人工智能领域的资深分析师，每天为高端读者撰写 AI 前沿日报。"
        "你的文字专业、简洁、富有洞察力，能够迅速抓住技术趋势的核心。"
    )

    user_prompt = f"""以下是今天从 arXiv、Hugging Face、国内外主流 AI 资讯平台收集到的内容摘要：

{context}

请根据以上内容，用中文撰写一段 300-500 字的「今日 AI 发展总览」。要求：
1. 首先用 2-3 句话概括今天 AI 领域最重要的整体趋势。
2. 分别从「前沿研究」「大模型与产品动态」「AI 硬件与算力」三个维度各用 2-3 句话点评最值得关注的进展。
3. 结尾用一句话给出你的研判或展望。
4. 语言精炼、客观，避免夸大。
5. 直接输出正文，不需要标题。"""

    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not resolved_key:
        logger.warning("ANTHROPIC_API_KEY not set; returning placeholder summary")
        return "（Claude API 密钥未配置，总览摘要暂不可用。请设置 ANTHROPIC_API_KEY 环境变量。）"

    try:
        client = anthropic.Anthropic(api_key=resolved_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        summary = message.content[0].text.strip()
        logger.info("Overall summary generated (%d chars)", len(summary))
        return summary
    except anthropic.APIError as exc:
        logger.error("Claude API error: %s", exc)
        return f"（AI 总览生成失败：{exc}）"


def generate_paper_highlights(
    papers: list[dict],
    model: str = "claude-opus-4-6",
    max_tokens: int = 1000,
    api_key: Optional[str] = None,
) -> str:
    """
    Ask Claude to pick the top 3 most impactful papers and explain why
    in 1-2 sentences each (Chinese).
    """
    if not papers:
        return ""

    paper_list = "\n".join(
        f"{i+1}. {p['title']}\n   {p['summary'][:200]}"
        for i, p in enumerate(papers[:12])
    )

    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not resolved_key:
        return ""

    try:
        client = anthropic.Anthropic(api_key=resolved_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"以下是今天 arXiv 的最新论文列表：\n\n{paper_list}\n\n"
                        "请从中选出最值得关注的 3 篇，每篇用 1-2 句中文说明其核心贡献和意义。"
                        "格式：序号. 论文标题 — 核心亮点说明。直接输出，不要其他文字。"
                    ),
                }
            ],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        logger.error("Paper highlights generation failed: %s", exc)
        return ""
