import logging
import time

import requests
from bs4 import BeautifulSoup

from data_agent.sources.base import Document, Source

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

URLS = [
    # Wikipedia — generic but reliable, good structural context
    "https://en.wikipedia.org/wiki/Ski_binding",
    "https://en.wikipedia.org/wiki/Ski_wax",
    "https://en.wikipedia.org/wiki/Alpine_skiing",

    # outdoor-ed.com — full ski tuning walkthrough
    "https://www.outdoor-ed.com/how-to/how-to-tune-skis/",

    # Tognar — specialty tuning supplier, comprehensive maintenance guide
    # covers base flattening, structuring, edge tuning, waxing, maintenance schedule
    "https://www.tognar.com/basic-ski-tuning-and-waxing-maintenance-guide/",

    # Renoun — ski brand how-to covering edge angles, base prep, wax selection,
    # detuning tips/tails, park vs all-mountain guidance
    "https://renoun.com/blogs/blog/tune-wax-skis-guide",

    # Racewax — race-oriented guide covering base/side edge bevel angles,
    # diamond stone sharpening, iron waxing technique
    "https://racewax.com/pages/quick-tuning-guide",

    # Powder7 — shop blog covering wax frequency, tuning intervals, damage
    # assessment (core shots vs. surface scratches), storage waxing
    "https://www.powder7.com/ski-blog/ski-maintenance/",
]


def _extract_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    for selector in ["article", "main", "body"]:
        node = soup.find(selector)
        if node:
            return node.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def _get_title(soup: BeautifulSoup, url: str) -> str:
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else url


class WebScraperSource(Source):
    def fetch(self) -> list[Document]:
        docs = []
        for url in URLS:
            logger.info(f"Scraping {url}")
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    logger.warning(f"Skipping {url} — HTTP {resp.status_code}")
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                content = _extract_content(soup)
                title = _get_title(soup, url)
                docs.append(
                    Document(
                        url=url,
                        title=title,
                        content=content,
                        source_type="web",
                        metadata={"scraped_url": url},
                    )
                )
                logger.info(f"Scraped {url} ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
            time.sleep(2)
        return docs
