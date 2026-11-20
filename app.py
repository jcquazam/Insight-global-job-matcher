

import csv as csvmod
import io
import json
import os

import streamlit as st

from run_demo_loader import load  # noqa

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
discover, report = load("discover"), load("report")

st.title("Job Matcher")

up = st.file_uploader("Upload a fictional TXT resume", type=["txt"])
REQ = ["source", "job_id", "title", "company", "location", "description", "job_url"]
jobs_up = st.file_uploader("Optional: job listings CSV (default: SYNTHETIC FIXTURE jobs)", type=["csv"])
jobs_path, label, jobs_err = os.path.join(ROOT, "fixtures", "jobs.json"), "SYNTHETIC FIXTURE", None
if jobs_up:
    rows = list(csvmod.DictReader(io.StringIO(jobs_up.getvalue().decode("utf-8-sig", errors="replace"))))
    cols = set(rows[0].keys()) if rows else set()
    missing = [c for c in REQ if c not in cols]
    if missing or not rows:
        jobs_err = "Missing columns: " + ", ".join(missing) if missing else "CSV has no rows."
        st.error(jobs_err)
    else:
        os.makedirs(OUT, exist_ok=True)
        jobs_path, label = os.path.join(OUT, "user_jobs.json"), "USER-PROVIDED"
        with open(jobs_path, "w", encoding="utf-8") as f:
            json.dump([{c: r[c] for c in REQ} for r in rows], f)
(st.warning if label == "SYNTHETIC FIXTURE" else st.info)("Job source: " + label + (" - all jobs are fictional records" if label == "SYNTHETIC FIXTURE" else ""))

kw = st.text_input("Job title keyword (optional)")
loc = st.text_input("Location (optional)")


def filter_jobs(jobs, kw, loc):
    kw, loc = kw.strip().lower(), loc.strip().lower()
    return [j for j in jobs if kw in j["title"].lower() and loc in j["location"].lower()]


if up and not jobs_err:
    text = up.getvalue().decode("utf-8", errors="replace")
    st.write("**Candidate skills:**", ", ".join(discover.extract_skills(text)) or "none found")
    if st.button("Run Discover"):
        os.makedirs(OUT, exist_ok=True)
        rpath = os.path.join(OUT, "uploaded_resume.txt")
        with open(rpath, "w", encoding="utf-8") as f:
            f.write(text)
        st.session_state.pop("jobs", None)
        with open(jobs_path, encoding="utf-8") as f:
            kept = filter_jobs(json.load(f), kw, loc)
        if not kept:
            st.info("No jobs match your filters. Try clearing or changing them.")
            st.stop()
        fpath = os.path.join(OUT, "filtered_jobs.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(kept, f)
        js = os.path.join(OUT, "jobs.v1.json")
        discover.run(rpath, fpath, js)
        cp = os.path.join(OUT, "matching_jobs.csv")
        report.run(js, cp)
        with open(js, encoding="utf-8") as f:
            st.session_state["jobs"] = json.load(f)["jobs"]
        st.session_state["label"] = label
        with open(cp, "rb") as f:
            st.session_state["csv"] = f.read()

if "jobs" in st.session_state:
    st.subheader("Ranked jobs (" + st.session_state.get("label", "") + ")")
    st.caption("Score = matched job skills / required job skills x 100. Required skills are the "
               "dictionary skills found in the job title and description; missing skills are "
               "required skills not found in your resume.")
    st.dataframe(
        [{"title": j["title"], "company": j["company"], "location": j["location"],
          "score": j["score"], "matched skills": ", ".join(j["matched_skills"]),
          "missing skills": ", ".join(j["missing_skills"]),
          "job URL": j["job_url"]} for j in st.session_state["jobs"]],
        column_config={"job URL": st.column_config.LinkColumn("job URL")},
        hide_index=True, use_container_width=True)
    st.download_button("Download CSV", st.session_state["csv"],
                       "matching_jobs.csv", "text/csv")
