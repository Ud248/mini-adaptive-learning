#!/usr/bin/env python3
"""
Quick CLI to query RAGTool from terminal.

Usage examples:
  python -m tests.run_rag_query --grade 1 --skill S5 --skill-name "Mấy và mấy" --topk-sgv 3 --topk-sgk 5
  python tests/run_rag_query.py --skill S5
"""
import argparse
import json
import sys

from agent.tools.rag_tool import RAGTool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a RAGTool query and print results as JSON")
    parser.add_argument("--grade", type=int, default=None, help="Student grade (e.g., 1)")
    parser.add_argument("--skill", type=str, required=True, help="Skill ID (e.g., S5)")
    parser.add_argument("--skill-name", type=str, default=None, help="Human-readable skill name for lesson matching")
    parser.add_argument("--topk-sgv", type=int, default=5, help="Top-K teacher (SGV) chunks")
    parser.add_argument("--topk-sgk", type=int, default=20, help="Top-K textbook (SGK) chunks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tool = RAGTool()
    result = tool.query(
        grade=args.grade,
        skill=args.skill,
        skill_name=args.skill_name,
        topk_sgv=args.topk_sgv,
        topk_sgk=args.topk_sgk,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


