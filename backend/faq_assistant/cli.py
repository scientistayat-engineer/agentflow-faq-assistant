"""Quick terminal test:  python -m faq_assistant.cli "How long does a refund take?" """
import argparse
import json

from .graph import run_assistant


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the FAQ assistant a question.")
    parser.add_argument("question")
    parser.add_argument("--no-langgraph", action="store_true", help="run the nodes sequentially")
    args = parser.parse_args()
    print(json.dumps(run_assistant(args.question, use_langgraph=not args.no_langgraph), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
