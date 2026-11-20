import importlib.util
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, name, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
js = os.path.join(ROOT, "out", "jobs.v1.json")
n = load("discover").run(os.path.join(ROOT, "fixtures", "resume.txt"),
                         os.path.join(ROOT, "fixtures", "jobs.json"), js)
print("discover:", n, "jobs ->", js)
csv_path = os.path.join(ROOT, "out", "matching_jobs.csv")
print("report:", load("report").run(js, csv_path), "rows ->", csv_path)
