"""
web_scraper.py — MCP tool: fetch and clean full page content from a URL.

Used by ResearchAgent to retrieve the full text of search result pages,
going beyond the snippets returned by web_search.
"""
import httpx
import re
from typing import Optional


async def scrape_url(url: str, timeout: int = 10) -> dict:
    """
    Fetch a URL and return cleaned plain-text content.

    Strips HTML tags, scripts, styles, and excess whitespace.
    Returns up to 8 000 characters to stay within Gemini context budget.

    Args:
        url:     The page URL to fetch.
        timeout: Request timeout in seconds (default 10).

    Returns:
        {
            "url":          str,
            "title":        str,
            "text_content": str,   # cleaned plain text, max 8 000 chars
            "char_count":   int,
            "success":      bool,
            "error":        str | None,
        }
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; NexusMindBot/1.0; +https://nexusmind.app)"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers=headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        # ── Extract title ─────────────────────────────────────────────────────
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # ── Strip scripts and styles ──────────────────────────────────────────
        html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>",  " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

        # ── Strip all remaining HTML tags ─────────────────────────────────────
        text = re.sub(r"<[^>]+>", " ", html)

        # ── Decode common HTML entities ───────────────────────────────────────
        entities = {
            "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&quot;": '"', "&#39;": "'", "&nbsp;": " ",
        }
        for ent, ch in entities.items():
            text = text.replace(ent, ch)

        # ── Normalise whitespace ──────────────────────────────────────────────
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        # ── Cap at 8 000 chars to fit Gemini prompt budget ────────────────────
        MAX_CHARS = 8_000
        truncated = len(text) > MAX_CHARS
        text = text[:MAX_CHARS]
        if truncated:
            text += "\n\n[... content truncated ...]"

        return {
            "url":          url,
            "title":        title,
            "text_content": text,
            "char_count":   len(text),
            "success":      True,
            "error":        None,
        }

    except httpx.HTTPStatusError as e:
        return {"url": url, "title": "", "text_content": "", "char_count": 0,
                "success": False, "error": f"HTTP {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"url": url, "title": "", "text_content": "", "char_count": 0,
                "success": False, "error": "Request timed out"}
    except Exception as e:
        return {"url": url, "title": "", "text_content": "", "char_count": 0,
                "success": False, "error": str(e)}
