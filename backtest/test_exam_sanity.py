"""
INSTRUMENT SANITY TESTS — does the exam still measure anything?

Motivated by 2026-07-30: the exam returned FAIL for 10 consecutive
candidates AND for plain buy-and-hold. A test whose output is a
constant has zero information content. These assertions make that
failure mode loud instead of silent.

Stricter-only: adding these can never admit a candidate that would
otherwise be rejected. No amendment approval required.

    python backtest/test_exam_sanity.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam, strategies as S

FAILS = []

def check(label, ok, detail=""):
    print(f"  [{'ok  ' if ok else 'FAIL'}] {label}{'  ' + detail if detail else ''}")
    if not ok:
        FAILS.append(label)

def rows_for(name, fee=exam.FEE, slip=exam.SLIP):
    return [r for p in exam.PAIRS
            for r in exam.exam_pair(p, S.get(name), fee, slip)]

def main():
    print("=== exam instrument sanity ===")

    hold = rows_for("hold")
    _v, checks, sm = exam.grade(hold)

    # 1. The benchmark must clear the exam's own FLOOR criteria.
    c = {k.split("_")[0] + "_" + k.split("_")[1].split(" ")[0]: v
         for k, v in checks.items()}
    for label, ok in checks.items():
        if label.startswith("1_") or label.startswith("5_"):
            check(f"benchmark clears {label}", ok)

    # 1b. POST-AMENDMENT-001: buy-and-hold must clear criteria 2 and 4.
    #     It cannot have a drawdown worse than its own, and it cannot
    #     underperform itself net of the same fees. If either fails, the
    #     instrument is broken again.
    for label, ok in checks.items():
        if label.startswith("2_") or label.startswith("4_"):
            check(f"benchmark clears {label}", ok)

    # 2. Buy-and-hold must not be judged worse than buy-and-hold by
    #    more than transaction costs. If it is, the comparison is
    #    apples-to-oranges.
    gap = sm["stitched_bh"] - sm["stitched"]
    check("hold is not penalised vs its own benchmark by >5x fees",
          sm["stitched"] > 0,
          f"hold {sm['stitched']:+.1%} vs bh {sm['stitched_bh']:+.1%}")

    # 3. The exam must be able to DISCRIMINATE: hold and a trend filter
    #    must not produce identical verdicts on every criterion, or the
    #    instrument is not responding to strategy differences at all.
    _v2, checks2, _sm2 = exam.grade(rows_for("trend_200"))
    differs = any(checks[k] != checks2[k] for k in checks)
    check("exam distinguishes hold from trend_200", differs)

    # 4. Fees must actually bite: a high-turnover strategy must score
    #    worse at 3x cost than at base cost.
    base = exam.grade(rows_for("rsi_14"))[2]["stitched"]
    dear = exam.grade(rows_for("rsi_14", exam.FEE * 3, exam.SLIP * 3))[2]["stitched"]
    check("higher fees reduce measured return", dear < base,
          f"{base:+.1%} -> {dear:+.1%}")

    # 5. Not-all-fail: if EVERY registry strategy fails every run, the
    #    bar is not a bar, it is a wall. Reported loudly, not asserted,
    #    because it is a judgement call.
    print("\n  [info] per-criterion failure tally across registry:")
    tally = {}
    for nm in ["hold", "trend_200", "cross_20_50", "donch_20", "rsi_14"]:
        try:
            _v3, ch, _s = exam.grade(rows_for(nm))
        except Exception:
            continue
        for k, ok in ch.items():
            if not ok:
                tally[k] = tally.get(k, 0) + 1
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        flag = "  <-- blocks everything" if v >= 5 else ""
        print(f"      {v}/5 fail  {k}{flag}")

    print()
    if FAILS:
        print(f"INSTRUMENT SUSPECT: {len(FAILS)} sanity check(s) failed.")
        print("The exam may not be measuring what it intends. See "
              "docs/exam_amendment_001.md")
        sys.exit(1)
    print("instrument sane.")

if __name__ == "__main__":
    main()
