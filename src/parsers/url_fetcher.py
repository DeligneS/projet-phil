"""URL content fetcher for web pages."""

import re
import requests
from bs4 import BeautifulSoup


def fetch_url_content(url: str, timeout: int = 30) -> str | None:
    """Fetch and extract text content from a URL.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text content, or None if fetching failed.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    except requests.RequestException as e:
        return None


def parse_urls_from_text(text: str) -> list[str]:
    """Extract URLs from a text string.

    Args:
        text: Text potentially containing URLs (one per line or space-separated).

    Returns:
        List of valid URLs found.
    """
    # Split by whitespace and newlines
    potential_urls = text.split()

    # Filter valid URLs
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return [url.strip() for url in potential_urls if url_pattern.match(url.strip())]


def fetch_multiple_urls(urls: list[str]) -> list[tuple[str, str]]:
    """Fetch content from multiple URLs.

    Args:
        urls: List of URLs to fetch.

    Returns:
        List of (url, content) tuples for successful fetches.
    """
    results = []
    for url in urls:
        content = fetch_url_content(url)
        if content:
            results.append((url, content))
    return results
