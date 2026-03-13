"""
HTML email template for the AI Frontier Daily Digest.
Renders a professional, mobile-friendly email using inline CSS.
"""

from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Inline CSS helpers
# ---------------------------------------------------------------------------
_STYLES = """
  body {
    margin: 0; padding: 0; background: #f4f6f9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue',
                 Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    color: #1a1a2e;
  }
  .wrapper { max-width: 700px; margin: 0 auto; background: #ffffff; }
  /* Header */
  .header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 36px 32px 28px;
    text-align: center;
  }
  .header h1 { margin: 0; color: #fff; font-size: 26px; letter-spacing: 2px; }
  .header .date { color: #a8b8ff; font-size: 14px; margin-top: 6px; }
  /* Sections */
  .section { padding: 28px 32px; border-bottom: 1px solid #eef0f5; }
  .section-title {
    font-size: 18px; font-weight: 700; margin: 0 0 16px;
    color: #302b63; display: flex; align-items: center; gap: 8px;
  }
  /* Summary box */
  .summary-box {
    background: #f0f4ff; border-left: 4px solid #5c6bc0;
    padding: 20px 22px; border-radius: 0 8px 8px 0;
    line-height: 1.8; font-size: 15px; color: #333;
  }
  /* Highlight box */
  .highlight-box {
    background: #fffbf0; border: 1px solid #ffe082;
    border-radius: 8px; padding: 16px 20px;
    margin-bottom: 18px; font-size: 14px; line-height: 1.7;
  }
  /* Cards */
  .card {
    background: #fafbff; border: 1px solid #e8eaf6;
    border-radius: 10px; padding: 16px 18px; margin-bottom: 14px;
  }
  .card-title { font-size: 15px; font-weight: 600; margin: 0 0 6px; }
  .card-title a { color: #3949ab; text-decoration: none; }
  .card-title a:hover { text-decoration: underline; }
  .card-meta {
    font-size: 12px; color: #757575; margin-bottom: 6px;
    display: flex; flex-wrap: wrap; gap: 8px;
  }
  .badge {
    background: #e8eaf6; color: #3949ab; border-radius: 4px;
    padding: 1px 7px; font-size: 11px; font-weight: 600;
  }
  .badge-green { background: #e8f5e9; color: #2e7d32; }
  .badge-orange { background: #fff3e0; color: #e65100; }
  .badge-red { background: #fce4ec; color: #c62828; }
  .card-summary { font-size: 13px; color: #555; line-height: 1.6; }
  /* Source tag */
  .source-tag {
    display: inline-block; background: #ede7f6; color: #4527a0;
    border-radius: 4px; padding: 1px 7px; font-size: 11px;
  }
  /* Footer */
  .footer {
    background: #302b63; padding: 24px 32px; text-align: center;
    color: #9fa8da; font-size: 13px; line-height: 1.8;
  }
  .footer a { color: #7986cb; }
  /* Divider */
  .divider { border: none; border-top: 1px solid #eef0f5; margin: 0; }
"""

_CATEGORY_BADGE = {
    "cs.AI": ("badge", "AI"),
    "cs.LG": ("badge badge-green", "ML"),
    "cs.CL": ("badge badge-orange", "NLP"),
    "cs.CV": ("badge badge-red", "CV"),
    "cs.RO": ("badge", "Robotics"),
}


def _paper_card(paper: dict) -> str:
    authors = ", ".join(paper.get("authors", []))
    cats = paper.get("categories", [])
    badges = " ".join(
        f'<span class="{_CATEGORY_BADGE.get(c, ("badge", c))[0]}">'
        f'{_CATEGORY_BADGE.get(c, ("badge", c))[1]}</span>'
        for c in cats[:3]
    )
    return f"""
    <div class="card">
      <div class="card-meta">{badges}
        <span>{paper.get('published','')}</span>
      </div>
      <div class="card-title">
        <a href="{paper['url']}" target="_blank">{paper['title']}</a>
      </div>
      <div class="card-meta">✍️ {authors}</div>
      <div class="card-summary">{paper.get('summary','')}</div>
    </div>"""


def _news_card(item: dict) -> str:
    summary_html = (
        f'<div class="card-summary">{item["summary"]}</div>'
        if item.get("summary") else ""
    )
    return f"""
    <div class="card">
      <div class="card-meta">
        <span class="source-tag">📰 {item['source']}</span>
        <span>{item.get('published','')}</span>
      </div>
      <div class="card-title">
        <a href="{item['url']}" target="_blank">{item['title']}</a>
      </div>
      {summary_html}
    </div>"""


def render_email(
    date_str: str,
    overall_summary: str,
    papers: list[dict],
    paper_highlights: str,
    feeds: dict[str, list[dict]],
) -> str:
    """Render the full HTML email string."""

    intl_news = feeds.get("intl_news", [])
    cn_news = feeds.get("cn_news", [])
    hardware = feeds.get("hardware", [])
    hf_papers = feeds.get("papers", [])

    # ---- Papers section ----
    all_papers = papers + hf_papers  # arXiv first, then HF/PWC
    paper_cards = "".join(_paper_card(p) for p in all_papers[:10])

    highlights_block = ""
    if paper_highlights:
        highlights_block = f"""
        <div class="highlight-box">
          <strong>🏆 Claude 精选三篇</strong><br/><br/>
          {paper_highlights.replace(chr(10), '<br/>')}
        </div>"""

    # ---- News sections ----
    intl_cards = "".join(_news_card(i) for i in intl_news[:8])
    cn_cards = "".join(_news_card(i) for i in cn_news[:8])
    hw_cards = "".join(_news_card(i) for i in hardware[:6])

    intl_section = f"""
      <div class="section">
        <div class="section-title">🌍 国际 AI 资讯</div>
        {intl_cards if intl_cards else '<p style="color:#888">暂无新内容</p>'}
      </div>""" if intl_news else ""

    cn_section = f"""
      <div class="section">
        <div class="section-title">🇨🇳 国内 AI 资讯（量子位 · 机器之心 · 新智元）</div>
        {cn_cards if cn_cards else '<p style="color:#888">暂无新内容</p>'}
      </div>""" if cn_news else ""

    hw_section = f"""
      <div class="section">
        <div class="section-title">💻 AI 硬件 · 算力动态</div>
        {hw_cards if hw_cards else '<p style="color:#888">暂无新内容</p>'}
      </div>""" if hardware else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AI 前沿日报 {date_str}</title>
<style>{_STYLES}</style>
</head>
<body>
<div class="wrapper">

  <!-- Header -->
  <div class="header">
    <h1>🤖 AI 前沿日报</h1>
    <div class="date">{date_str} &nbsp;|&nbsp; 每日 07:00 准时送达</div>
  </div>

  <!-- Overall AI summary -->
  <div class="section">
    <div class="section-title">🌐 今日 AI 发展总览</div>
    <div class="summary-box">{overall_summary.replace(chr(10), '<br/>')}</div>
  </div>

  <!-- Papers -->
  <div class="section">
    <div class="section-title">📄 前沿论文（arXiv · Hugging Face · Papers With Code）</div>
    {highlights_block}
    {paper_cards if paper_cards else '<p style="color:#888">暂无新论文</p>'}
  </div>

  {intl_section}
  {cn_section}
  {hw_section}

  <!-- Footer -->
  <div class="footer">
    <p>
      数据来源：arXiv · Hugging Face · 量子位 · 机器之心 · 新智元<br/>
      The Rundown AI · Import AI · AI Snake Oil · NVIDIA · SemiAnalysis
    </p>
    <p>
      由 <strong>Claude (Anthropic)</strong> 驱动 &nbsp;·&nbsp;
      <a href="https://github.com/Rancho-Yin/AI-froniter-information">GitHub 项目</a>
    </p>
    <p style="color:#7986cb;font-size:11px;">如需退订，请回复此邮件。</p>
  </div>

</div>
</body>
</html>"""
