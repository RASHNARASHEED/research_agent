
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime


def web_search(query, max_results=5):
    """
    Search the web using DuckDuckGo and return a list of results.
    Each result has: title, url, snippet
    """
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body")
            })
    return results


def read_url(url):
    """
    Fetch a webpage and return its clean, readable text (HTML stripped out).
    Truncates to ~3000 characters to keep it manageable for the LLM.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except Exception as e:
        return f"Error fetching URL: {e}"


def save_note(title, content):
    """
    Save a markdown report to the output/ folder.
    Returns the filepath where it was saved.
    """
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/report_{timestamp}.md"
    markdown_content = f"# {title}\n\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n{content}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    return f"Report saved to {filename}"


def ask_user(question):
    """
    Pause execution and ask the human a clarifying question via the terminal.
    Returns whatever the human types.
    """
    print(f"\nAgent needs clarification: {question}")
    answer = input("Your answer: ")
    return answer


# Lookup table connecting tool names (as strings) to the real Python functions
AVAILABLE_FUNCTIONS = {
    "web_search": web_search,
    "read_url": read_url,
    "save_note": save_note,
    "ask_user": ask_user
}


# JSON schemas describing each tool to the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on a topic. Use this when you need up-to-date facts, news, or information not in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": "Fetch and read the content of a specific webpage. Use this after web_search when you want to read more details from one of the search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the webpage to read"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save the final research findings as a markdown report file. Use this only once you have gathered enough information and are ready to produce the final report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the report"
                    },
                    "content": {
                        "type": "string",
                        "description": "The full markdown-formatted content of the report"
                    }
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask the human user a clarifying question when their request is ambiguous or you need more information to proceed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The clarifying question to ask the user"
                    }
                },
                "required": ["question"]
            }
        }
    }
]


