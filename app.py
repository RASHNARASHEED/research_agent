import os
import re
import streamlit as st
from agent import run_agent, resume_agent

st.set_page_config(page_title="Research Assistant Agent", page_icon="🔎", layout="centered")

st.title("Research Assistant Agent")
st.caption("Enter a research request. The agent will plan, search, read, and save a report — "
           "and will pause to ask you a question if your request is ambiguous.")

# ---- session state ----
if "state" not in st.session_state:
    st.session_state.state = {"status": "idle"}
if "logs" not in st.session_state:
    st.session_state.logs = []


def log_callback(line):
    st.session_state.logs.append(line)


def find_saved_report_path(messages):
    """Scan the tool results in the conversation for a save_note confirmation
    like 'Report saved to output/report_....md' and return that path, if any."""
    for m in messages:
        content = m.get("content") if isinstance(m, dict) else None
        if content and "saved to" in content.lower():
            match = re.search(r"([\w\-./\\]+\.md)", content)
            if match:
                return match.group(1)
    return None


def reset():
    st.session_state.state = {"status": "idle"}
    st.session_state.logs = []


# ---- input (only when not mid-run) ----
if st.session_state.state["status"] in ("idle", "done", "max_iterations", "error"):
    user_request = st.text_area(
        "Your request:",
        placeholder="What are the latest trends in vector databases? Summarize top 3 and save a report.",
        height=100,
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        run_button = st.button("Run Agent", type="primary")
    with col2:
        if st.session_state.state["status"] != "idle" and st.button("Reset"):
            reset()
            st.rerun()

    if run_button:
        if not user_request.strip():
            st.warning("Please enter a request first.")
        else:
            st.session_state.logs = []
            with st.spinner("Agent working..."):
                st.session_state.state = run_agent(user_request, log_callback=log_callback)
            st.rerun()

# ---- paused: waiting on a human answer ----
if st.session_state.state["status"] == "waiting_for_user":
    st.info(f"**Agent needs clarification:** {st.session_state.state['question']}")
    answer = st.text_input("Your answer:", key="user_answer")
    if st.button("Send answer", type="primary"):
        if answer.strip():
            with st.spinner("Agent is continuing..."):
                st.session_state.state = resume_agent(
                    st.session_state.state["messages"], answer, log_callback=log_callback
                )
            st.rerun()
        else:
            st.warning("Type an answer before sending.")

# ---- finished: show the report ----
if st.session_state.state["status"] in ("done", "max_iterations", "error"):
    st.subheader("Final Report")

    report_path = find_saved_report_path(st.session_state.state.get("messages", []))

    if report_path and os.path.exists(report_path):
        # Render the actual saved report content directly — a local file path
        # can't be opened as a web link, so we read and display it instead.
        with open(report_path, "r", encoding="utf-8") as f:
            report_content = f.read()

        st.markdown(report_content)
        st.download_button(
            label="Download report (.md)",
            data=report_content,
            file_name=os.path.basename(report_path),
            mime="text/markdown",
        )
    else:
        # No file was saved this run (or it couldn't be located) — just show
        # whatever the agent's final answer text was.
        st.markdown(st.session_state.state.get("answer", "No answer produced."))

# ---- reasoning trace ----
if st.session_state.logs:
    with st.expander("Agent reasoning trace (think → act → observe)", expanded=False):
        st.code("\n".join(st.session_state.logs), language=None)