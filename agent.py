
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOLS, AVAILABLE_FUNCTIONS

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"
MAX_ITERATIONS = 8

SYSTEM_PROMPT = """You are a research assistant agent. You have access to tools:
- web_search: search the web for information
- read_url: read the full content of a specific webpage
- save_note: save your final findings as a markdown report
- ask_user: ask the user a clarifying question if their request is ambiguous

Before every tool call, briefly state your reasoning in one short sentence
(e.g. "I need to search for recent trends before I can summarize them.").
Then call the appropriate tool. Only call save_note once you have gathered
enough information for a complete, well-structured report.
"""


def run_agent(user_request, log_callback=None):
    """
    log_callback: optional function(str) -> None, called with each log line.
    If not provided, logs print to terminal as before.
    """
    def log(line):
        if log_callback:
            log_callback(line)
        else:
            print(line)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_request}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        log(f"\n--- Iteration {iteration} ---")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS
        )

        message = response.choices[0].message
        messages.append(message)

        if message.content:
            log(f"THINK: {message.content}")

        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                log(f"ACT: calling {function_name}({arguments})")

                function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                if function_to_call:
                    try:
                        result = function_to_call(**arguments)
                    except Exception as e:
                        result = f"Error running {function_name}: {e}"
                else:
                    result = f"Error: unknown tool {function_name}"

                log(f"OBSERVE: {str(result)[:300]}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
        else:
            log("\n--- Final Answer ---")
            log(message.content)
            return message.content

    log("\nMax iterations reached. Stopping.")
    return "Agent stopped: reached maximum iterations without a final answer."
