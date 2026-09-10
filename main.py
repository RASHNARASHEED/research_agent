from agent import run_agent, resume_agent


def main():
    print("Research Assistant Agent")
    print("Type your research request below.\n")

    user_request = input("You: ").strip()

    if not user_request:
        print("No request given. Exiting.")
        return

    state = run_agent(user_request)

    while state["status"] == "waiting_for_user":
        answer = input(f"\nAgent asks: {state['question']}\nYour answer: ").strip()
        state = resume_agent(state["messages"], answer)

    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)

    if state["status"] in ("done", "max_iterations"):
        print(state["answer"])
    else:
        print(f"Agent stopped with an error: {state.get('answer', 'unknown error')}")


if __name__ == "__main__":
    main()