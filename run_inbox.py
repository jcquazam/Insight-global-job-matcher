"""Read job CSVs from an inbox, rank against a resume via Discover, export via Report."""
import argparse
import csv
import glob
import importlib.util
import json
import os
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ["source", "job_id", "title", "company", "location",
            "description", "job_url"]


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, name, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", required=True)
    ap.add_argument("--resume", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(os.path.expanduser(a.inbox), "*.csv")))
    loaded, unique = 0, {}
    for p in files:
        with open(p, newline="", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            missing = [c for c in REQUIRED if c not in (r.fieldnames or [])]
            if missing:
                raise SystemExit(f"{p}: missing columns {missing}")
            for row in r:
                loaded += 1
                unique.setdefault((row["source"], row["job_id"]),
                                  {c: row[c] for c in REQUIRED})

    out_dir = os.path.dirname(os.path.abspath(a.output))
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        jobs_in, js = os.path.join(tmp, "jobs.json"), os.path.join(tmp, "jobs.v1.json")
        with open(jobs_in, "w", encoding="utf-8") as f:
            json.dump(list(unique.values()), f)
        load("discover").run(a.resume, jobs_in, js)
        exported = load("report").run(js, a.output)
    print(f"files read: {len(files)}\njobs loaded: {loaded}\n"
          f"unique jobs: {len(unique)}\nexported: {exported}")


if __name__ == "__main__":
    main()
