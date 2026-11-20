"""Read a manually saved Insight Global job page in a visible Chromium (offline) -> job CSV."""
import argparse
import csv
import os
import re

from playwright.sync_api import sync_playwright

COLS = ["source", "job_id", "title", "company", "location", "description", "job_url"]
JS = """() => {
  const t = id => { const e = document.querySelector('lib-job-details-card [data-testid="' + id + '"]');
                    return e ? e.innerText : ''; };
  return {title: t('job-details-job-title'), company: t('job-details-company-name'),
          location: t('job-details-worksite-location'), description: t('job-details-job-description')};
}"""

ap = argparse.ArgumentParser()
ap.add_argument("--input", default="~/Downloads/insightglobal_job.html")
ap.add_argument("--output", required=True)
ap.add_argument("--job-id", default="")
ap.add_argument("--job-url", default="")
ap.add_argument("--smoke", action="store_true")
a = ap.parse_args()
path = os.path.abspath(os.path.expanduser(a.input))
blocked = []

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=False, args=["--start-maximized"])
    ctx = b.new_context(no_viewport=True, java_script_enabled=False)  # static saved DOM, no scripts
    ctx.route(re.compile(r"^https?://"), lambda r: (blocked.append(r.request.url), r.abort()))
    page = ctx.new_page()
    page.goto("file://" + path)
    page.wait_for_selector("lib-job-details-card", timeout=10000)
    f = {k: " ".join(v.split()) for k, v in page.evaluate(JS).items()}
    if not f["title"] or not f["description"]:
        raise SystemExit("Extraction unreliable: title/description not found.")
    row = {"source": "INSIGHT GLOBAL - MANUALLY SAVED HTML (NOT LIVE COLLECTION)",
           "job_id": a.job_id, "job_url": a.job_url, **f}
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerow({c: row[c] for c in COLS})
    print({k: (v[:60] + "...") if len(v) > 60 else v for k, v in row.items()})
    print("missing:", [c for c in COLS if not row[c]], "| external requests blocked:", len(blocked))
    if not a.smoke:
        print("Browser open for inspection; close the window to exit.")
        page.wait_for_event("close", timeout=0)
    b.close()
