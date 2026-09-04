from agent import run_agent

def main():
    print("Research Assistant Agent")
    print("Type your research request below.\n")

    user_request = input("You: ").strip()

    if not user_request:
        print("No request given. Exiting.")
        return

    final_answer = run_agent(user_request)

    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)

if __name__ == "__main__":
    main()