
import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Research Assistant Agent", page_icon="🔎", layout="centered")

st.title("Research Assistant Agent")
st.caption("Enter a research request. The agent will plan, search, read, and save a report.")

user_request = st.text_area(
    "Your request:",
    placeholder="What are the latest trends in vector databases? Summarize top 3 and save a report.",
    height=100
)

run_button = st.button("Run Agent", type="primary")

if run_button:
    if not user_request.strip():
        st.warning("Please enter a request first.")
    else:
        st.subheader("Agent Steps (Think → Act → Observe)")
        log_box = st.empty()
        logs = []

        def log_callback(line):
            logs.append(line)
            log_box.code("\n".join(logs))

        with st.spinner("Agent working..."):
            final_answer = run_agent(user_request, log_callback=log_callback)

        st.subheader("Final Report")
        st.markdown(final_answer)
