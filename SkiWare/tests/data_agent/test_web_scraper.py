import logging
from unittest.mock import MagicMock, patch
from data_agent.sources.web_scraper import WebScraperSource, HEADERS, URLS


def _mock_resp(status_code: int, html: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = html
    return resp


def test_skips_url_on_non_200_and_logs_warning(caplog):
    with patch("data_agent.sources.web_scraper.requests.get", return_value=_mock_resp(403)), \
         patch("data_agent.sources.web_scraper.time.sleep"), \
         caplog.at_level(logging.WARNING, logger="data_agent.sources.web_scraper"):
        docs = WebScraperSource().fetch()
    assert docs == []
    assert any("403" in r.message for r in caplog.records)


def test_returns_document_on_200():
    html = "<html><body><main>Wax your skis in 5 steps.</main></body></html>"
    with patch("data_agent.sources.web_scraper.requests.get", return_value=_mock_resp(200, html)), \
         patch("data_agent.sources.web_scraper.time.sleep"):
        docs = WebScraperSource().fetch()
    assert len(docs) > 0
    assert "Wax your skis in 5 steps." in docs[0].content


def test_uses_chrome_user_agent():
    assert "Mozilla" in HEADERS["User-Agent"]
    assert "Chrome" in HEADERS["User-Agent"]


def test_continues_after_failed_url():
    good_html = "<html><body><main>Ski edge guide.</main></body></html>"
    # First URL fails (403), all remaining succeed
    responses = [_mock_resp(403)] + [_mock_resp(200, good_html)] * (len(URLS) - 1)
    with patch("data_agent.sources.web_scraper.requests.get", side_effect=responses), \
         patch("data_agent.sources.web_scraper.time.sleep"):
        docs = WebScraperSource().fetch()
    assert len(docs) == len(URLS) - 1
    assert "Ski edge guide." in docs[0].content
