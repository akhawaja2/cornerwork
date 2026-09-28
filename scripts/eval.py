"""Acceptance proxy for parse_log against tests/eval/logs.jsonl.
Usage: .venv/Scripts/python.exe scripts/eval.py            (fake, offline)
       .venv/Scripts/python.exe scripts/eval.py --live     (Claude; needs ANTHROPIC_API_KEY)
Labels were written by the developer, not yet coach-approved; treat the numbers as a regression floor, not truth."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.integrations.llm import ClaudeLLM, FakeLLM, safety_check  # noqa: E402

CASES = [json.loads(line) for line in (Path(__file__).resolve().parents[1] / "tests/eval/logs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def run(llm):
    hits = {"sentiment": 0, "injury": 0, "concussion": 0}
    misses = []
    t0 = time.time()
    for case in CASES:
        p = safety_check(case["transcript"], llm.parse_log(case["transcript"], "", []))
        area = (p.injury.area if p.injury else None)
        ok_injury = (area is None) == (case["injury_area"] is None) and (area is None or case["injury_area"] in area.lower())
        hits["sentiment"] += p.sentiment == case["sentiment"]
        hits["injury"] += ok_injury
        hits["concussion"] += p.concussion_flag == case["concussion_flag"]
        if not ok_injury or p.concussion_flag != case["concussion_flag"]:
            misses.append((case["transcript"][:60], area, p.concussion_flag))
    n = len(CASES)
    return {k: round(v / n * 100) for k, v in hits.items()} | {"n": n, "seconds": round(time.time() - t0, 1), "safety_misses": misses}


if __name__ == "__main__":
    llm = ClaudeLLM() if "--live" in sys.argv else FakeLLM()
    print(llm.model, json.dumps(run(llm), indent=1))
