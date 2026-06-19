"""Mini browser for CORTEX.

This module provides lightweight text-based browsing for URLs and
query-driven page summaries.
"""

import html
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from core.search import WikipediaSearch


class MiniBrowser:
    """Fetch web pages and extract readable summaries."""

    def __init__(self) -> None:
        self.wikipedia = WikipediaSearch()

    def browse(self, address: str) -> str:
        """Browse a URL or search query and return a text summary."""
        address = address.strip()
        if not address:
            return "Please provide a URL or search query after the browser command."

        if self._looks_like_url(address):
            return self._fetch_url(address)

        return self.wikipedia.search(address)

    def _looks_like_url(self, address: str) -> bool:
        address_lower = address.lower()
        return bool(
            re.match(r"^https?://", address_lower)
            or "." in address_lower and " " not in address_lower
        )

    def _normalize_url(self, address: str) -> str:
        if re.match(r"^https?://", address, re.IGNORECASE):
            return address
        return f"https://{address}"

    def _fetch_url(self, address: str) -> str:
        url = self._normalize_url(address)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CORTEX-MiniBrowser/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type.lower():
                    return f"Fetched non-HTML content from {url}. Content-Type: {content_type}"
                html_text = response.read().decode(response.headers.get_content_charset(failobj="utf-8"), errors="replace")
        except urllib.error.HTTPError as exc:
            return f"Browser HTTP error: {exc.code} {exc.reason}"
        except urllib.error.URLError as exc:
            return f"Browser connection failed: {exc.reason}"
        except Exception as exc:
            return f"Browser request failed: {exc}"

        title = self._extract_title(html_text) or url
        summary = self._extract_summary(html_text)
        return f"Mini Browser: {title}\n\n{summary}"

    def _extract_title(self, html_text: str) -> Optional[str]:
        match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self._cleanup_text(match.group(1))

    def _extract_summary(self, html_text: str) -> str:
        paragraphs = re.findall(r"<p>(.*?)</p>", html_text, re.IGNORECASE | re.DOTALL)
        cleaned = []
        for paragraph in paragraphs:
            text = self._cleanup_text(paragraph)
            if len(text) > 80:
                cleaned.append(text)
            if len(cleaned) >= 5:
                break
        if cleaned:
            return "\n\n".join(cleaned)

        text_content = re.sub(r"<[^>]+>", " ", html_text)
        text_content = self._cleanup_text(text_content)
        snippet = text_content[:1000].strip()
        if snippet:
            return snippet + ("..." if len(text_content) > 1000 else "")
        return "No readable text was found on the page."

    def _cleanup_text(self, content: str) -> str:
        text = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
