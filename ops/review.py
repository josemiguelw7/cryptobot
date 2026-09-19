"""Weekly-review tool (charter s8 / s10.1, charter_v2 Tier 1).

REPAIR under charter_v2 s3.2: bot/squad.py says a -6%/7d halt "resumes at
review", but no code path ever resumed anything, so a temporary halt was
permanent. This tool is that missing path. It changes NO threshold.

  .venv/bin/python ops/review.py                 # report only (any day)
  .venv/bin/python ops/review.py --resume BOT... # owner, Saturday only
  .venv/bin/python ops/review.py --resume all

Guards (each has a failing test in ops/test_review.py, charter_v2 s5.1):
  - resumes only on Saturday, America/Chicago (s10.1)
  - never resumes a BENCHED bot (-10% lifetime is retirement, not a halt)
  - every resume is appended to logs/review_log.csv
An LLM must not run --resume on its own: resuming is the owner's act.
"""
import csv, json, os, sys, tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = {"crypto": os.path.join(ROOT, "bot", "squad_state.json"),
          "stocks": os.path.join(ROOT, "bot", "squad_stocks_state.json")}
LOG = os.path.join(ROOT, "logs", "review_log.csv")
CT = ZoneInfo("America/Chicago")


def now_ct():
    return datetime.now(timezone.utc).astimezone(CT)


def is_review_day(t=None):
    return (t or now_ct()).weekday() == 5          # Saturday


def report(st, track):
    rows = []
    for name, b in st["bots"].items():
        flag = ("BENCHED" if b.get("benched") else
                "halt->review" if b.get("halt_review") else
                "halt-data" if b.get("halt_data") else "active")
        rows.append((name, b.get("last_eq", 0.0), flag))
    act = sum(1 for r in rows if r[2] == "active")
    print(f"[{track}] {act}/{len(rows)} activos"
          f"{'  SQUAD HALT' if st.get('squad_halt_review') else ''}")
    for n, eq, f in rows:
        print(f"   {n:<16} ${eq:>9,.2f}  {f}")
    return rows


def resume(st, names, t=None):
    """Returns list of resumed names. Raises on any guard breach."""
    if not is_review_day(t):
        raise PermissionError("resume solo en la revision del sabado (s10.1)")
    done = []
    for n in names:
        b = st["bots"][n]
        if b.get("benched"):
            raise PermissionError(f"{n} esta BENCHED: retiro, no se reanuda")
        if b.get("halt_review"):
            b["halt_review"] = False
            done.append(n)
    return done


def save(path, st):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, path)


def main(argv):
    want = argv[argv.index("--resume") + 1:] if "--resume" in argv else None
    for track, path in STATES.items():
        st = json.load(open(path))
        report(st, track)
        if want is None:
            continue
        halted = [n for n, b in st["bots"].items() if b.get("halt_review")]
        names = halted if want == ["all"] else [n for n in want if n in st["bots"]]
        done = resume(st, names)
        if done:
            save(path, st)
            new = not os.path.exists(LOG)
            with open(LOG, "a", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["utc", "track", "bot", "action"])
                for n in done:
                    w.writerow([datetime.now(timezone.utc).isoformat(),
                                track, n, "RESUME"])
            print(f"   reanudados: {', '.join(done)}")


if __name__ == "__main__":
    main(sys.argv[1:])
