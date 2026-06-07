"""
Stub out optional heavy dependencies (vertexai) so that data_agent
modules can be imported in the test environment without the real packages
installed.  Individual tests patch specific callables via unittest.mock.

Note: bs4 is NOT stubbed here because web_scraper tests require real
BeautifulSoup HTML parsing functionality.
"""
import sys
from unittest.mock import MagicMock

# Stub vertexai and its sub-modules used by data_agent/pipeline/embedder.py
for mod in (
    "vertexai",
    "vertexai.language_models",
):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
