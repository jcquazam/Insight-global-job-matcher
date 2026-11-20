"""Discover: skill extraction + matching. Writes the shared JSON contract."""
import json
import re

SKILLS = ["python", "pytorch", "tensorflow", "scikit-learn", "sql", "docker",
          "kubernetes", "aws", "nlp", "llm", "mlops", "spark", "fastapi",
          "git", "machine learning", "tableau"]


def extract_skills(text):
    t = text.lower()
    return [s for s in SKILLS
            if re.search(r"(?<![\w-])" + re.escape(s) + r"(?![\w-])", t)]


def run(resume_path, jobs_path, out_path):
    with open(resume_path, encoding="utf-8") as f:
        resume = extract_skills(f.read())
    with open(jobs_path, encoding="utf-8") as f:
        raw = json.load(f)
    seen, results = set(), []
    for j in raw:
        key = (j["source"], j["job_id"])
        if key in seen:
            continue
        seen.add(key)
        req = extract_skills(j["title"] + " " + j["description"])
        matched = [s for s in req if s in resume]
        missing = [s for s in req if s not in resume]
        score = round(len(matched) / len(req) * 100, 1) if req else 0.0
        results.append({"source": j["source"], "job_id": j["job_id"],
                        "title": j["title"], "company": j["company"],
                        "location": j["location"], "job_url": j["job_url"],
                        "required_skills": req, "matched_skills": matched,
                        "missing_skills": missing, "score": score})
    results.sort(key=lambda r: -r["score"])
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1", "synthetic": True,
                   "resume_skills": resume, "jobs": results}, f, indent=2)
    return len(results)
