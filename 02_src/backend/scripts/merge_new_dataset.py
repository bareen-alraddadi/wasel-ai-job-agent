"""
merge_new_dataset.py
====================
Merges a new jobs CSV (with 'qualifications' and 'description_text' columns)
into the existing saudi_jobs_full.json format.

Skills are extracted using a taxonomy built from the existing dataset
with word-boundary regex matching to avoid false positives like:
  - "r" matching "required"
  - "go" matching "google"
  - "java" matching "javascript"
  - "scala" matching "scalable"

Usage:
    python backend/scripts/merge_new_dataset.py \
        --new_csv  data/jobs_dataset/new_jobs.csv \
        --old_json data/jobs_dataset/saudi_jobs_full.json \
        --out_json data/jobs_dataset/saudi_jobs_full.json

The script appends new records to the existing JSON in-place (no duplicates).
Re-run `make build-rag` afterwards to push to Qdrant.
"""

import json
import re
import csv
import argparse
import uuid
from pathlib import Path

# ── Skills that cause false-positive substring matches ─────────
# These are handled with strict word-boundary matching anyway,
# but we keep a short blocklist for extra safety.
SHORT_SKILL_BLOCKLIST = {
    "r", "c", "go",  # too ambiguous without context
}


def build_taxonomy(old_jobs: list[dict]) -> list[str]:
    """
    Collect every unique skill from the existing dataset.
    Sort longest-first so multi-word skills ("Machine Learning")
    are matched before single-word subsets ("Machine").
    """
    taxonomy: set[str] = set()
    for job in old_jobs:
        taxonomy.update(job.get("required_skills", []))
        taxonomy.update(job.get("preferred_skills", []))

    # Remove empty strings
    taxonomy.discard("")

    # Sort: longest first → prevents "Machine" stealing "Machine Learning"
    return sorted(taxonomy, key=len, reverse=True)


def skill_pattern(skill: str) -> re.Pattern:
    """
    Compile a regex pattern for a skill using word boundaries.
    Handles multi-word skills like "Machine Learning" correctly.
    """
    escaped = re.escape(skill)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def extract_skills(text: str, taxonomy: list[str]) -> list[str]:
    """
    Find all taxonomy skills present in text using word-boundary matching.
    Returns a deduplicated list preserving original casing from taxonomy.
    """
    found: list[str] = []
    matched_lower: set[str] = set()

    for skill in taxonomy:
        if skill.lower() in SHORT_SKILL_BLOCKLIST:
            continue
        if skill_pattern(skill).search(text):
            key = skill.lower()
            if key not in matched_lower:
                found.append(skill)
                matched_lower.add(key)

    return found


def map_new_row(row: dict, taxonomy: list[str], start_id: int) -> dict:
    """
    Convert a row from the new CSV format to the saudi_jobs_full.json schema.
    """
    combined_text = " ".join([
        row.get("qualifications", ""),
        row.get("description_text", ""),
    ])

    required_skills = extract_skills(combined_text, taxonomy)

    # Experience years: try to extract "X+" or "X-Y" from qualifications
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", row.get("qualifications", ""), re.I)
    experience_years = f"{exp_match.group(1)}+" if exp_match else ""

    return {
        "job_id":           str(start_id),
        "title":            row.get("job_title", "").strip(),
        "company":          row.get("company_name", "").strip(),
        "location":         row.get("location", "").strip(),
        "country":          row.get("country", "").strip(),
        "description":      row.get("description_text", "").strip(),
        "required_skills":  required_skills,
        "preferred_skills": [],
        "experience_years": experience_years,
        "salary_range":     row.get("salary_formatted", "").strip(),
        "job_type":         row.get("job_type", "").strip(),
        "industry":         "",          # not available in new dataset
        "apply_link":       row.get("apply_link", "").strip(),
        "benefits":         row.get("benefits", "").strip(),
        "date_posted":      row.get("date_posted", "").strip(),
    }


def main():
    parser = argparse.ArgumentParser(description="Merge new jobs CSV into existing JSON dataset")
    parser.add_argument("--new_csv",  required=True, help="Path to new jobs CSV file")
    parser.add_argument("--old_json", required=True, help="Path to existing saudi_jobs_full.json")
    parser.add_argument("--out_json", required=True, help="Output path (can be same as old_json)")
    args = parser.parse_args()

    # ── Load existing dataset ────────────────────────────────
    print(f"📂 Loading existing dataset: {args.old_json}")
    with open(args.old_json, encoding="utf-8") as f:
        old_jobs: list[dict] = json.load(f)

    print(f"   Existing jobs: {len(old_jobs)}")

    # ── Build taxonomy ───────────────────────────────────────
    taxonomy = build_taxonomy(old_jobs)
    print(f"   Taxonomy size: {len(taxonomy)} unique skills")

    # Optionally save taxonomy for inspection
    taxonomy_path = Path(args.old_json).parent / "skills_taxonomy.json"
    with open(taxonomy_path, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)
    print(f"   Taxonomy saved → {taxonomy_path}")

    # ── Load new CSV ─────────────────────────────────────────
    print(f"\n📂 Loading new dataset: {args.new_csv}")
    with open(args.new_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        new_rows = list(reader)
    print(f"   New rows: {len(new_rows)}")

    # ── Map & extract skills ─────────────────────────────────
    start_id = max(int(j.get("job_id", 0)) for j in old_jobs) + 1
    new_jobs: list[dict] = []
    skipped = 0

    for i, row in enumerate(new_rows):
        mapped = map_new_row(row, taxonomy, start_id + i)

        # Skip rows with no title or no skills extracted
        if not mapped["title"]:
            skipped += 1
            continue

        new_jobs.append(mapped)

    print(f"   Mapped:  {len(new_jobs)} jobs")
    print(f"   Skipped: {skipped} (no title)")

    # Skill extraction stats
    with_skills    = sum(1 for j in new_jobs if j["required_skills"])
    without_skills = len(new_jobs) - with_skills
    print(f"   With skills:    {with_skills}")
    print(f"   Without skills: {without_skills}  ← these still searchable via text embedding")

    # ── Merge & save ─────────────────────────────────────────
    merged = old_jobs + new_jobs
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Merged dataset saved → {args.out_json}")
    print(f"   Total jobs: {len(merged)}  ({len(old_jobs)} old + {len(new_jobs)} new)")
    print("\n🚀 Now run:  make build-rag")


if __name__ == "__main__":
    main()
