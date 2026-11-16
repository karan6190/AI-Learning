"""
STEP 4 — See the trace: one request, three processes, one picture
=================================================================

Reads observability_lab/traces.jsonl (written by every process) and draws the
latest trace as a tree with a timeline bar, like the waterfall in Jaeger or LangSmith:

    SPAN                                     SERVICE           TIME   TIMELINE
    plan trip                                supervisor       480ms   ██████████████████████████████
    ├─ discover agents                       supervisor        20ms   █
    ├─ a2a SendMessage -> Weather Agent      supervisor        90ms    █████
    │  └─ agent Weather Agent                a2a-agents        80ms    █████
    │     └─ mcp call_tool get_weather       a2a-agents        75ms    ████
    │        └─ tool get_weather             mcp-tool-server   52ms     ███
    ...

Run:
    python observability_lab/04_view_trace.py              # latest trace
    python observability_lab/04_view_trace.py <trace-id>   # a specific trace (first chars are enough)
    python observability_lab/04_view_trace.py --list       # list all traces
    python observability_lab/04_view_trace.py --clear      # delete the trace file
"""

import json
import sys
from collections import defaultdict

from telemetry import TRACE_FILE

BAR_WIDTH = 30
RED, DIM, RESET = "\033[31m", "\033[2m", "\033[0m"


def load_spans() -> list[dict]:
    if not TRACE_FILE.exists():
        sys.exit("No traces yet. Run 03_supervisor.py first.")
    spans = []
    for line in TRACE_FILE.read_text(encoding="utf-8").splitlines():
        try:
            spans.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # skip a damaged line rather than crash
    return spans


def group_by_trace(spans: list[dict]) -> dict[str, list[dict]]:
    traces = defaultdict(list)
    for s in spans:
        traces[s["trace_id"]].append(s)
    # oldest first, so the last one is the latest
    return dict(sorted(traces.items(), key=lambda kv: max(s["end_ns"] for s in kv[1])))


def root_of(spans: list[dict]) -> dict:
    ids = {s["span_id"] for s in spans}
    return min((s for s in spans if s["parent_id"] not in ids), key=lambda s: s["start_ns"])


def list_traces(traces: dict) -> None:
    print(f"{'TRACE ID':<34} {'ROOT SPAN':<14} {'SPANS':>5} {'TIME':>8}  ERRORS")
    for trace_id, spans in traces.items():
        root = root_of(spans)
        errors = sum(s["status"] == "ERROR" for s in spans)
        ms = (root["end_ns"] - root["start_ns"]) / 1e6
        print(f"{trace_id:<34} {root['name']:<14} {len(spans):>5} {ms:>6.0f}ms  {errors or ''}")


def draw(trace_id: str, spans: list[dict]) -> None:
    children = defaultdict(list)
    for s in spans:
        children[s["parent_id"]].append(s)
    for kids in children.values():
        kids.sort(key=lambda s: s["start_ns"])

    root = root_of(spans)
    t0, total = root["start_ns"], max(root["end_ns"] - root["start_ns"], 1)

    print(f"\nTrace {trace_id}   ({len(spans)} spans, {total / 1e6:.0f} ms)\n")
    print(f"{'SPAN':<44} {'SERVICE':<16} {'TIME':>7}   TIMELINE")

    def walk(span: dict, prefix: str, is_last: bool, is_root: bool) -> None:
        branch = "" if is_root else ("└─ " if is_last else "├─ ")
        start = int((span["start_ns"] - t0) / total * BAR_WIDTH)
        length = max(1, round((span["end_ns"] - span["start_ns"]) / total * BAR_WIDTH))
        bar = " " * start + "█" * length
        ms = (span["end_ns"] - span["start_ns"]) / 1e6
        failed = span["status"] == "ERROR"
        line = f"{(prefix + branch + span['name'])[:44]:<44} {span['service']:<16} {ms:>5.0f}ms   {bar}"
        print(f"{RED}{line}  ✗ {span['error']}{RESET}" if failed else line)

        kids = children.get(span["span_id"], [])
        child_prefix = prefix + ("" if is_root else ("   " if is_last else "│  "))
        for i, kid in enumerate(kids):
            walk(kid, child_prefix, i == len(kids) - 1, False)

    walk(root, "", True, True)

    # Attributes worth showing: what went in and out of each hop
    print(f"\n{DIM}Details (inputs/outputs recorded on each span):{RESET}")
    for s in sorted(spans, key=lambda s: s["start_ns"]):
        shown = {k: v for k, v in s["attributes"].items() if k.endswith(("input", "output")) or ".input." in k}
        if shown:
            print(f"  {s['name']}")
            for k, v in shown.items():
                print(f"      {k} = {v}")


def main(args: list[str]) -> None:
    if args and args[0] == "--clear":
        TRACE_FILE.unlink(missing_ok=True)
        print("Trace file cleared.")
        return
    traces = group_by_trace(load_spans())
    if args and args[0] == "--list":
        list_traces(traces)
        return
    if args:
        matches = [t for t in traces if t.startswith(args[0])]
        if not matches:
            sys.exit(f"No trace starts with {args[0]!r}. Try --list.")
        trace_id = matches[0]
    else:
        trace_id = list(traces)[-1]
    draw(trace_id, traces[trace_id])


if __name__ == "__main__":
    main(sys.argv[1:])
