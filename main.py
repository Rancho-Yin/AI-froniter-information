"""
AI Frontier Daily Digest – main entry point.

Usage:
  # Run once immediately (CI / GitHub Actions)
  python main.py

  # Run on a daily schedule at the configured time (local daemon)
  python main.py --daemon

  # Send a test email with sample data (no API calls)
  python main.py --test
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytz
import schedule
import time
import yaml
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

BASE_DIR = Path(__file__).parent


def load_config() -> dict:
    cfg_path = BASE_DIR / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------- #
# Core digest pipeline
# --------------------------------------------------------------------------- #
def run_digest(cfg: dict) -> bool:
    """Collect, summarise, and email today's AI digest. Returns True on success."""

    from src.collectors.arxiv_collector import collect_arxiv_papers
    from src.collectors.rss_collector import collect_rss_feeds
    from src.summarizer.ai_summarizer import (
        generate_overall_summary,
        generate_paper_highlights,
    )
    from src.email_sender.html_template import render_email
    from src.email_sender.sender import send_digest

    tz = pytz.timezone(cfg["schedule"]["timezone"])
    now = datetime.now(tz)
    date_str = now.strftime("%Y年%m月%d日 %A")

    logger.info("=== AI Digest Pipeline started at %s ===", now.isoformat())

    # 1. Collect arXiv papers
    logger.info("Step 1/4 – Collecting arXiv papers …")
    arxiv_cfg = cfg["sources"]["arxiv"]
    papers = collect_arxiv_papers(
        categories=arxiv_cfg["categories"],
        max_results=arxiv_cfg["max_results"],
    )

    # 2. Collect RSS feeds
    logger.info("Step 2/4 – Collecting RSS feeds …")
    rss_cfg = cfg["sources"]["rss_feeds"]
    all_feeds: list[dict] = []
    for group in rss_cfg.values():
        all_feeds.extend(group)

    display = cfg.get("display", {})
    feeds = collect_rss_feeds(
        feed_configs=all_feeds,
        hours_back=48,
        max_per_feed=display.get("max_news_per_source", 5),
    )

    # 3. Generate AI summaries
    logger.info("Step 3/4 – Generating AI summaries via Zhipu AI …")
    zhipu_cfg = cfg["zhipu"]
    api_key = os.environ.get("ZHIPU_API_KEY")

    overall_summary = generate_overall_summary(
        papers=papers,
        feeds=feeds,
        model=zhipu_cfg["model"],
        max_tokens=zhipu_cfg["summary_max_tokens"],
        api_key=api_key,
    )
    paper_highlights = generate_paper_highlights(
        papers=papers,
        model=zhipu_cfg["model"],
        max_tokens=1000,
        api_key=api_key,
    )

    # 4. Render and send email
    logger.info("Step 4/4 – Rendering and sending email …")
    email_cfg = cfg["email"]
    subject = f"{email_cfg['subject_prefix']} · {now.strftime('%Y-%m-%d')}"

    html = render_email(
        date_str=date_str,
        overall_summary=overall_summary,
        papers=papers,
        paper_highlights=paper_highlights,
        feeds=feeds,
    )

    success = send_digest(
        subject=subject,
        html_body=html,
        smtp_server=email_cfg["smtp_server"],
        smtp_port=email_cfg["smtp_port"],
    )

    if success:
        logger.info("=== Digest pipeline completed successfully ===")
    else:
        logger.error("=== Digest pipeline completed with errors ===")

    return success


# --------------------------------------------------------------------------- #
# Test mode – renders a sample email and saves to file
# --------------------------------------------------------------------------- #
def run_test(cfg: dict):
    """Render a sample email to ./test_output.html without sending."""
    from src.email_sender.html_template import render_email

    tz = pytz.timezone(cfg["schedule"]["timezone"])
    now = datetime.now(tz)
    date_str = now.strftime("%Y年%m月%d日 %A")

    sample_papers = [
        {
            "title": "Attention Is All You Need (Redux): Advances in Transformer Architectures",
            "authors": ["Alice Zhang", "Bob Smith", "Carol Johnson"],
            "summary": (
                "We present a comprehensive review of transformer architecture advances since "
                "the original 2017 paper, focusing on efficiency improvements and multi-modal "
                "capabilities that have enabled today's frontier language models."
            ),
            "url": "https://arxiv.org/abs/2401.00001",
            "published": now.strftime("%Y-%m-%d"),
            "categories": ["cs.CL", "cs.AI"],
            "category_label": "自然语言处理",
        },
        {
            "title": "Scaling Laws for Multimodal Foundation Models",
            "authors": ["David Lee", "Eva Chen"],
            "summary": (
                "We derive empirical scaling laws governing the performance of multimodal "
                "models across text, image, audio and video modalities."
            ),
            "url": "https://arxiv.org/abs/2401.00002",
            "published": now.strftime("%Y-%m-%d"),
            "categories": ["cs.LG", "cs.CV"],
            "category_label": "机器学习",
        },
    ]

    sample_feeds = {
        "intl_news": [
            {
                "title": "OpenAI announces next-generation reasoning model",
                "url": "https://openai.com/blog/test",
                "summary": "OpenAI today unveiled its latest reasoning model, claiming significant improvements on mathematical benchmarks.",
                "source": "OpenAI Blog",
                "category": "intl_news",
                "published": now.strftime("%Y-%m-%d"),
            }
        ],
        "cn_news": [
            {
                "title": "量子位：国内大模型厂商最新进展盘点",
                "url": "https://www.qbitai.com/test",
                "summary": "本文梳理了过去一周国内主要大模型厂商的最新动态，包括百度、阿里、字节等。",
                "source": "量子位",
                "category": "cn_news",
                "published": now.strftime("%Y-%m-%d"),
            }
        ],
        "hardware": [
            {
                "title": "NVIDIA announces next-gen Blackwell Ultra GPU architecture",
                "url": "https://blogs.nvidia.com/test",
                "summary": "NVIDIA revealed details of the upcoming Blackwell Ultra architecture targeting datacenter AI workloads.",
                "source": "NVIDIA AI Blog",
                "category": "hardware",
                "published": now.strftime("%Y-%m-%d"),
            }
        ],
    }

    html = render_email(
        date_str=date_str,
        overall_summary=(
            "今日 AI 领域整体延续快速迭代态势。在前沿研究方面，多模态大模型持续突破，"
            "Transformer 架构效率提升研究成为热点，多篇论文在 arXiv 首发并迅速引发社区关注。"
            "在大模型与产品动态方面，国内外主要厂商均有新模型或功能发布，竞争格局愈发激烈。"
            "在 AI 硬件与算力方面，NVIDIA 新一代 GPU 架构细节逐步浮出水面，"
            "国内算力基础设施投资持续加速。展望后续，随着模型能力逼近人类专家水平，"
            "AI 落地与安全治理将成为下一阶段的核心议题。\n\n"
            "（此为测试模式样本内容，实际运行时由 Claude 实时生成。）"
        ),
        papers=sample_papers,
        paper_highlights=(
            "1. Attention Is All You Need (Redux) — 系统梳理了 Transformer 七年演进历程，"
            "为研究者提供了清晰的技术路线图。\n"
            "2. Scaling Laws for Multimodal Foundation Models — 首次在多模态场景下验证了"
            "规模定律的普适性，对模型设计具有重要指导意义。"
        ),
        feeds=sample_feeds,
    )

    out_path = BASE_DIR / "test_output.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("Test email rendered to: %s", out_path)
    print(f"\n✅  Test HTML saved to: {out_path}\nOpen it in a browser to preview the email layout.\n")


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="AI Frontier Daily Digest")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously as a daily scheduler (uses config.yaml time).",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Render a sample email to test_output.html without sending.",
    )
    args = parser.parse_args()

    cfg = load_config()

    if args.test:
        run_test(cfg)
        return

    if args.daemon:
        scheduled_time = cfg["schedule"]["time"]
        logger.info("Daemon mode: scheduling digest at %s (CST) every day", scheduled_time)
        schedule.every().day.at(scheduled_time).do(run_digest, cfg=cfg)
        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        # One-shot mode (GitHub Actions / manual run)
        success = run_digest(cfg)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
