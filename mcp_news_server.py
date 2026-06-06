import os
import httpx
import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("News Research Server")

@mcp.tool()
async def fetch_news(query: str, language: str = "en") -> str:
    """Fetch live news articles from NewsData.io and return facts + sources."""
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NEWSDATA_KEY")
    if not api_key:
        return "ERROR: NEWSDATA_KEY not provided."

    url = "https://newsdata.io/api/1/news"
    params = {"apikey": api_key, "q": query, "language": language}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    articles = data.get("results", [])[:5]
    if not articles:
        return "NO_ARTICLES===SOURCES===No sources found."

    facts = []
    source_links = []
    for a in articles:
        title = a.get("title", "No Title")
        description = a.get("description", "No Description")
        link = a.get("link", "#")
        facts.append(f"- Title: {title}\n  Summary: {description}")
        if link != "#":
            source_links.append(f"* [{title}]({link})")

    articles_text = "\n\n".join(facts)
    sources_text = "\n".join(source_links) if source_links else "No sources found."

    # Delimiter lets workflow.py split facts from URLs cleanly
    return f"{articles_text}===SOURCES==={sources_text}"

if __name__ == "__main__":
    mcp.run()