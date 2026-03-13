"""
arXiv paper collector – fetches the latest AI/ML/NLP/CV papers published
in the last 24 hours from arXiv's official API.
"""

import arxiv
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Human-readable category labels
CATEGORY_LABELS = {
    "cs.AI": "人工智能",
    "cs.LG": "机器学习",
    "cs.CL": "自然语言处理",
    "cs.CV": "计算机视觉",
    "cs.RO": "机器人",
}


def collect_arxiv_papers(categories: list[str], max_results: int = 15) -> list[dict]:
    """
    Fetch recent arXiv papers across the given categories.

    Returns a list of dicts with keys:
        title, authors, summary, url, published, categories, category_label
    """
    query = " OR ".join(f"cat:{c}" for c in categories)
    client = arxiv.Client(num_retries=3)

    search = arxiv.Search(
        query=query,
        max_results=max_results * 2,          # over-fetch, then filter by date
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    papers: list[dict] = []

    try:
        for result in client.results(search):
            if result.published < cutoff:
                break
            if len(papers) >= max_results:
                break

            primary_cat = result.primary_category
            papers.append(
                {
                    "title": result.title,
                    "authors": [str(a) for a in result.authors[:3]],
                    "summary": result.summary[:400].replace("\n", " "),
                    "url": result.entry_id,
                    "published": result.published.strftime("%Y-%m-%d"),
                    "categories": result.categories[:3],
                    "category_label": CATEGORY_LABELS.get(primary_cat, primary_cat),
                }
            )
    except Exception as exc:
        logger.error("arXiv collection failed: %s", exc)

    logger.info("Collected %d arXiv papers", len(papers))
    return papers
