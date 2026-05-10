"""
web_search.py — MCP-style web search tool.

In production, wire this to Google Custom Search API or SerpAPI.
For MVP, it returns a structured response using Gemini's knowledge.
"""
import httpx
import os
from typing import Optional


async def web_search(query: str, num_results: int = 5) -> dict:
    """
    Perform a web search and return structured results.

    Args:
        query: The search query string.
        num_results: Maximum number of results to return.

    Returns:
        dict with keys: query, results (list of {title, url, snippet}), total_found
    """
    # Check for Google Custom Search API credentials
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")

    if api_key and cx:
        return await _google_search(query, num_results, api_key, cx)

    # Fallback: return a structured placeholder indicating no live search is configured
    return {
        "query": query,
        "results": [
            {
                "title": f"Search result for: {query}",
                "url": "https://www.google.com/search?q=" + query.replace(" ", "+"),
                "snippet": (
                    "Live web search is not configured. "
                    "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX environment variables "
                    "to enable real web search results."
                ),
            }
        ],
        "total_found": 0,
        "note": "Fallback mode — no live search API configured.",
    }


async def _google_search(query: str, num_results: int, api_key: str, cx: str) -> dict:
    """Call the Google Custom Search JSON API."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num_results, 10),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", [])
    results = [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in items
    ]
    return {
        "query": query,
        "results": results,
        "total_found": int(data.get("searchInformation", {}).get("totalResults", 0)),
    }
