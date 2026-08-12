"""
ops/void_verdict.py — the ONLY sanctioned way to void an exam verdict.

Charter v2 rule (2026-08-08): a verdict may be voided when, and only
when, a DOCUMENTED code bug affected the exam that produced it. Voiding:

  * appends a VOID row to the ledger (the ledger is never rewritten,
    never shortened — the original row stays as history);
  * frees the name for one re-exam on fixed code (exam.ledger_names()
    reads a name's LATEST row);
  * does NOT reduce K: every row, including VOID rows and the original
    verdict, still counts as a trial. The compute was spent; the luck
    hurdle only ever rises.

What voiding is NOT for: disliking a FAIL, a reviewer's opinion, a
different sample, or "the market changed." The --bug argument must point
at a committed document or commit hash describing the defect. No
document, no void.

Usage:
    python ops/void_verdict.py --name d3_trend \
        --bug docs/review/2026-08-08_external_review.md#C-1 \
        --reason "SlowClock frozen by len%k boundary; seed made 1 decision per window"
"""
import argparse, csv, os, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backtest"))
LEDGER = os.path.join(ROOT, "backtest", "results", "exam_ledger.csv")
VOIDLOG = os.path.join(ROOT, "backtest", "results", "void_log.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--bug", required=True,
                    help="path#anchor or commit hash documenting the bug")
    ap.add_argument("--reason", required=True)
    a = ap.parse_args()

    if not os.path.exists(LEDGER):
        sys.exit("no ledger found")

    with open(LEDGER) as f:
        rdr = csv.reader(f)
        header = next(rdr)
        rows = list(rdr)

    target = [r for r in rows if r and r[0] == a.name]
    if not target:
        sys.exit(f"{a.name!r} has no ledger row: nothing to void")
    last = target[-1]
    if last[2] == "VOID":
        sys.exit(f"{a.name!r} is already void")

    # the bug reference must exist in the repo (a doc path before any
    # '#anchor', or be plausibly a commit hash)
    doc = a.bug.split("#")[0]
    if not (os.path.exists(os.path.join(ROOT, doc))
            or all(c in "0123456789abcdef" for c in doc.lower())):
        sys.exit(f"bug reference {a.bug!r} does not exist in the repo. "
                 f"No document, no void.")

    # VOID row: same shape as the original so the CSV stays rectangular,
    # verdict replaced, date updated. Original row is untouched above it.
    void_row = list(last)
    void_row[1] = date.today().isoformat()
    void_row[2] = "VOID"
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow(void_row)

    new = not os.path.exists(VOIDLOG)
    with open(VOIDLOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["candidate", "date", "original_date",
                        "original_verdict", "bug_ref", "reason"])
        w.writerow([a.name, date.today().isoformat(), last[1], last[2],
                    a.bug, a.reason])

    print(f"VOIDED {a.name}: name freed for one re-exam on fixed code.")
    print(f"  original verdict {last[2]} ({last[1]}) stands as history")
    print(f"  bug ref: {a.bug}")
    print(f"  K is unchanged upward: the void row itself is a ledger row.")
    print(f"ledger -> {LEDGER}\nvoid log -> {VOIDLOG}")


if __name__ == "__main__":
    main()
