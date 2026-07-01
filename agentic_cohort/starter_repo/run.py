"""Session 0 baseline — does my key work?  One call, no tools, no loop.

This is the "hello" tick from the pre-flight. If this prints a reply, your
.env + key + model are good and you're ready for Session 1.

Run:  python run.py "hello"
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.environ["MODEL"]


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "hello"
    resp = client.messages.create(
        model=MODEL, max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    print(next((b.text for b in resp.content if b.type == "text"), ""))


if __name__ == "__main__":
    main()
