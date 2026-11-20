"""Report: reads only jobs.v1.json, writes CSV."""
import csv
import json


def safe(v):
    v = str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def run(json_path, csv_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "company", "location", "score",
                    "matched_skills", "job_url"])
        for j in data["jobs"]:
            w.writerow([safe(j["title"]), safe(j["company"]),
                        safe(j["location"]), j["score"],
                        safe(", ".join(j["matched_skills"])),
                        safe(j["job_url"])])
    return len(data["jobs"])
