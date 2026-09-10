import os
import json
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APITimeoutError, APIError
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

IMPORTANT: If the user's request does not clearly state a specific topic 
or subject to research, you MUST call ask_user first, before calling any 
other tool. Do not guess, assume, or pick a "reasonable default" topic on 
your own — even if you think you know what they probably mean. Only 
proceed with web_search once the topic is explicit, either from the 
original request or from the user's answer to your clarifying question.

Before every tool call, briefly state your reasoning in one short sentence
(e.g. "I need to search for recent trends before I can summarize them.").
Then call the appropriate tool. Only call save_note once you have gathered
enough information for a complete, well-structured report.
"""
def _call_model(messages, log):
    """Wraps the completion call with retry on transient failures."""
    for attempt in range(3):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                max_tokens=600,
            )
        except (RateLimitError, APITimeoutError) as e:
            if attempt == 2:
                raise
            log(f"  (transient error: {e}, retrying...)")
            import time
            time.sleep(2 ** attempt)
        except APIError as e:
            log(f"  (API error, not retrying: {e})")
            raise


def run_agent(user_request, log_callback=None):
    """
    Starts a fresh agent run.

    Returns a dict, always — check "status":
      - {"status": "done", "answer": str, "messages": [...]}
      - {"status": "waiting_for_user", "question": str, "messages": [...]}
      - {"status": "max_iterations", "answer": str, "messages": [...]}

    "messages" is the full running state — pass it straight into resume_agent()
    once you have the user's answer to a "waiting_for_user" pause.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_request},
    ]
    return _run_loop(messages, log_callback)


def resume_agent(messages, user_answer, log_callback=None):
    """
    Continues a paused run. `messages` is exactly what run_agent()/resume_agent()
    returned last time under "messages". `user_answer` is the human's reply to
    the pending "question".
    """
    last_assistant_msg = messages[-1]
    tool_call_id = last_assistant_msg["tool_calls"][0]["id"]

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": user_answer,
    })
    return _run_loop(messages, log_callback, start_iteration=messages_iteration_count(messages))


def messages_iteration_count(messages):
    """Rough iteration count so a resumed run still respects MAX_ITERATIONS overall."""
    return sum(1 for m in messages if m.get("role") == "assistant")


def _run_loop(messages, log_callback=None, start_iteration=0):
    def log(line):
        if log_callback:
            log_callback(line)
        else:
            print(line)

    for iteration in range(start_iteration + 1, MAX_ITERATIONS + 1):
        log(f"\n--- Iteration {iteration} ---")

        try:
            response = _call_model(messages, log)
        except Exception as e:
            log(f"FATAL: could not get a response from the model: {e}")
            return {
                "status": "error",
                "answer": f"Agent stopped due to an API error: {e}",
                "messages": messages,
            }

        message = response.choices[0].message
        messages.append(message.model_dump())

        if message.content:
            log(f"THINK: {message.content}")

        if not message.tool_calls:
            log("\n--- Final Answer ---")
            log(message.content)
            return {"status": "done", "answer": message.content, "messages": messages}

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            log(f"ACT: calling {function_name}({arguments})")

            if function_name == "ask_user":
                question = arguments.get("question", "Could you clarify your request?")
                log(f"PAUSED: waiting on human answer to: {question}")
                return {
                    "status": "waiting_for_user",
                    "question": question,
                    "messages": messages,
                }

            function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
            if function_to_call:
                try:
                    raw_result = function_to_call(**arguments)
                    result = str(raw_result)[:2000]
                except Exception as e:
                    result = f"Error running {function_name}: {e}"
            else:
                result = f"Error: unknown tool {function_name}"

            log(f"OBSERVE: {result[:300]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    log("\nMax iterations reached. Stopping.")
    return {
        "status": "max_iterations",
        "answer": "Agent stopped: reached maximum iterations without a final answer.",
        "messages": messages,
    }


if __name__ == "__main__":
    user_request = input("What should the agent research? ")
    state = run_agent(user_request)

    while state["status"] == "waiting_for_user":
        answer = input(f"\nAgent asks: {state['question']}\nYour answer: ")
        state = resume_agent(state["messages"], answer)

    if state["status"] in ("done", "max_iterations"):
        print("\n=== RESULT ===")
        print(state["answer"])
    else:
        print("\n=== ERROR ===")
        print(state["answer"])