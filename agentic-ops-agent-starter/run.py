"""
Entrypoint. Run your agent from the command line:

    python run.py "What is today's date?"
    python run.py "Read notes.txt and summarise the action items"

On day one (Session 0) just run:  python run.py "hello"
and watch the loop tick once. That's your agent working end-to-end.
"""
import sys
from agent.loop import run_agent


def main():
    goal = " ".join(sys.argv[1:]).strip()
    if not goal:
        goal = "Say hello, tell me today's date, then stop."
        print(f'(no goal given — using default: "{goal}")')

    print(f'\n🎯 GOAL: {goal}')
    final = run_agent(goal)
    print("\n" + "=" * 60)
    print("✅ FINAL:", final)


if __name__ == "__main__":
    main()
