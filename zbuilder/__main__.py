"""python -m zbuilder <command>

    spec [--force]        fetch + index the Z-Machine Standard, extract §14
    stories               download the conformance stories in stories/urls.txt
    plan                  render the tiered plan (and, with a model, propose changes)
    build [--tier N] [--task ID] [--provider NAME]
                          run the agent loop (offline: briefs + verification)
    verify [--task ID]    run the Verifier's checks only
    review [--task ID]    run the Reviewer's audit (+ LLM judge with a model)
    ask "QUESTION"        ask the Spec Analyst (answers cite §sections)
    status                show every task's state
    golden --record|--check
                          freeze / compare today's build outputs (refactor gate)
"""
from __future__ import annotations

import argparse
import sys

from zbuilder.llm.provider import ProviderError, get_provider
from zbuilder.orchestrator import Orchestrator
from zbuilder.plan import DEFAULT_PLAN, find


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="zbuilder", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--provider", help="rovodev | anthropic | openai | gemini | ollama | brief")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("spec")
    s.add_argument("--force", action="store_true")
    sub.add_parser("stories")
    sub.add_parser("plan")
    b = sub.add_parser("build")
    b.add_argument("--tier", type=int)
    b.add_argument("--task")
    v = sub.add_parser("verify")
    v.add_argument("--task")
    r = sub.add_parser("review")
    r.add_argument("--task")
    a = sub.add_parser("ask")
    a.add_argument("question", nargs="+")
    sub.add_parser("status")
    g = sub.add_parser("golden")
    g.add_argument("--record", action="store_true", help="a human runs this once, before Tier 5")
    g.add_argument("--check", action="store_true")
    args = p.parse_args(argv)

    if args.command == "golden":
        from zbuilder.tools import golden
        if args.record:
            print("\n".join(golden.record()))
            return 0
        problems = golden.check()
        print("\n".join(problems) or "golden: all outputs byte-identical")
        return 1 if problems else 0

    if args.command == "stories":
        from zbuilder.tools.fetch_stories import fetch_stories
        for line in fetch_stories():
            print(line)
        return 0
    try:
        provider = get_provider(args.provider)
    except ProviderError as exc:
        print(f"zbuilder: {exc}", file=sys.stderr)
        return 2
    orch = Orchestrator(provider)

    if args.command == "spec":
        print(orch.spec.build(force=args.force))
    elif args.command == "plan":
        print(orch.architect.propose() if not provider.offline else orch.architect.render_plan())
    elif args.command == "build":
        return 0 if orch.build(args.tier, args.task) else 1
    elif args.command in ("verify", "review"):
        tasks = [find(args.task)] if args.task else DEFAULT_PLAN
        if None in tasks:
            print(f"zbuilder: unknown task {args.task}", file=sys.stderr)
            return 2
        ok = True
        for task in tasks:
            if args.command == "verify":
                report = orch.verifier.verify(task)
                ok &= report["passed"]
                print(f"  {'PASS' if report['passed'] else 'FAIL'}  {task.id}")
                for c in report["checks"]:
                    if not c["passed"]:
                        print("      " + c["tail"].replace("\n", "\n      ")[-1500:])
            else:
                result = orch.reviewer.review(task)
                print(f"  {result['verdict']:<8} {task.id}  ({len(result['issues'])} issues)")
                for issue in result["issues"]:
                    print(f"      - {issue}")
        return 0 if ok else 1
    elif args.command == "ask":
        print(orch.spec.answer(" ".join(args.question)))
    elif args.command == "status":
        print(orch.status_table())
    return 0


if __name__ == "__main__":
    sys.exit(main())
