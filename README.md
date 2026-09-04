\# Research Assistant Agent



A ReAct-style AI agent built for Week 5 (Agents, Tools \& Function Calling).

The agent plans its steps, calls tools to gather real information, and produces

a structured markdown research report - all visible step-by-step in the logs/UI.



\## What it does



Given a research request like:



> "What are the latest trends in vector databases? Summarize top 3 and save a report."



the agent will:

1\. Think about what it needs to find out

2\. Search the web for relevant information

3\. Read promising pages in more depth

4\. Repeat until it has enough to answer

5\. Save a structured markdown report

6\. Return a final summary



\## Architecture



User request -> Agent (LLM, Think) -> Act: calls a tool -> Observe: reads result

\-> loops up to 8 times -> Final answer + markdown report saved



See architecture.png for the full diagram.



\## Tools



| Tool | Behavior |

|---|---|

| web\_search | Searches the web via DuckDuckGo, returns title/url/snippet for each result |

| read\_url | Fetches a specific webpage and extracts its readable text |

| save\_note | Saves the final findings as a timestamped markdown report in output/ |

| ask\_user | Pauses and asks the human a clarifying question if the request is ambiguous |



\## Safety guardrails



\- Max iteration limit: the agent stops after 8 loop iterations to prevent runaway loops

\- Scoped tools: the agent only has access to the 4 tools above

\- Visible reasoning: every step prints THINK / ACT / OBSERVE lines, so the agent's plan is visible before it acts



\## Setup



1\. Clone this repo and enter the folder

&#x20;  git clone https://github.com/RASHNARASHEED/research\_agent.git

&#x20;  cd research\_agent



2\. Create and activate a virtual environment

&#x20;  python -m venv venv

&#x20;  venv\\Scripts\\Activate.ps1



3\. Install dependencies

&#x20;  pip install -r requirements.txt



4\. Set up your API key

&#x20;  - Copy .env.example to .env

&#x20;  - Add your OpenAI API key



\## Usage



Terminal version:

&#x20;  python main.py



Web UI version (Streamlit):

&#x20;  streamlit run app.py



\## Tech stack



\- Python

\- OpenAI API (gpt-4o-mini) - function/tool calling

\- ddgs - free web search (DuckDuckGo)

\- requests + beautifulsoup4 - webpage fetching and parsing

\- streamlit - optional web UI



\## Project structure



research\_agent/

\- main.py       CLI entry point

\- app.py        Streamlit UI entry point

\- agent.py      ReAct loop (Think -> Act -> Observe)

\- tools.py      Tool functions + JSON schemas

\- requirements.txt

\- .env.example

\- output/       Generated markdown reports

