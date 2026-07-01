"""Receipts CLI: transcripts -> themes -> verified quotes -> report.html

    python run.py                      # uses ./data/transcripts, writes report.html
    python run.py --data path/ --out out.html --model claude-haiku-4-5
"""

from __future__ import annotations

import argparse
import sys

from receipts.data import load_transcripts
from receipts.pipeline import MODEL, synthesize
from receipts.report import write_report
from receipts.verify import (
    UNVERIFIED, MISATTRIBUTED, BAD_SOURCE, LOOSE, verify_synthesis,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Receipts: grounded research synthesis.")
    ap.add_argument("--data", default="data/transcripts", help="dir of .txt transcripts")
    ap.add_argument("--out", default="report.html", help="output HTML path")
    ap.add_argument("--model", default=MODEL, help="Claude model id")
    args = ap.parse_args()

    transcripts = load_transcripts(args.data)
    print(f"Loaded {len(transcripts)} transcripts from {args.data}")
    print(f"Synthesizing themes with {args.model} ...")

    try:
        synthesis = synthesize(transcripts, model=args.model)
    except Exception as e:  # noqa: BLE001 - surface any API/auth error plainly
        print(f"\nSynthesis failed: {e}", file=sys.stderr)
        print("Is ANTHROPIC_API_KEY set? (see .env.example)", file=sys.stderr)
        return 1

    report = verify_synthesis(synthesis, transcripts)

    print(f"\nGrounded score: {round(report.grounded_score * 100)}%  "
          f"({report.total} quotes across {len(report.themes)} themes)")
    print(f"  verified {report.counts['verified']}  "
          f"paraphrased {report.counts[LOOSE]}  "
          f"misattributed {report.counts[MISATTRIBUTED]}  "
          f"not-found {report.counts[UNVERIFIED] + report.counts[BAD_SOURCE]}\n")

    for theme in report.themes:
        print(f"[{round(theme.grounded_score * 100):3d}%] {theme.title}")
        for e in theme.evidence:
            if e.status != "verified":
                where = f" (found in {e.found_in})" if e.found_in else ""
                print(f"        !! {e.status}{where}: \"{e.quote[:70]}...\"")

    subtitle = f"{len(transcripts)} interviews · synthesized with {args.model}"
    write_report(args.out, report, subtitle)
    print(f"\nWrote {args.out} -- open it in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
