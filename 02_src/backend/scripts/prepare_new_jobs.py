"""
prepare_new_jobs.py
====================
Selects the best 10,000 jobs from clean_jobs_data.csv,
maps them to the saudi_jobs_full.json schema (same field names),
extracts required_skills via taxonomy + word-boundary regex,
and saves a preview JSON WITHOUT touching Qdrant.

Steps:
  1. Score every row (quality score 0-5)
  2. Keep SA only, sort by score desc, take top 10,000
  3. Extract skills from description_text via taxonomy
  4. Normalize job_type (Arabic → English)
  5. Save to data/jobs_dataset/new_jobs_prepared.json

After reviewing the output, run:
  python backend/scripts/build_qdrant_index.py --extra data/jobs_dataset/new_jobs_prepared.json
to upsert only the new jobs to Qdrant.
"""

import json
import csv
import re
from pathlib import Path

# ── Config ────────────────────────────────────────────────────
OLD_JSON     = Path("data/jobs_dataset/saudi_jobs_full.json")
NEW_CSV      = Path("data/jobs_dataset/clean_jobs_data.csv")
OUT_JSON     = Path("data/jobs_dataset/new_jobs_prepared.json")
TAXONOMY_OUT = Path("data/jobs_dataset/skills_taxonomy.json")
TOP_N        = 10_000

# Skills too short / ambiguous for substring matching
SHORT_SKILL_BLOCKLIST = {"r", "c", "go"}


# ── Step 1: Build taxonomy from old dataset ───────────────────

def build_taxonomy(old_jobs: list[dict]) -> list[str]:
    """Collect unique skills from existing dataset, longest-first."""
    skill_set: set[str] = set()
    for job in old_jobs:
        skill_set.update(job.get("required_skills", []))
        skill_set.update(job.get("preferred_skills", []))
    skill_set.discard("")
    return sorted(skill_set, key=len, reverse=True)  # longest first


def skill_regex(skill: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)


def extract_skills(text: str, taxonomy: list[str]) -> list[str]:
    found, seen = [], set()
    for skill in taxonomy:
        if skill.lower() in SHORT_SKILL_BLOCKLIST:
            continue
        if skill_regex(skill).search(text):
            key = skill.lower()
            if key not in seen:
                found.append(skill)
                seen.add(key)
    return found


# ── Step 2: Quality scoring ───────────────────────────────────

NULL_VALUES = {"nan", "none", "not specified", "not available", "unknown", ""}

def is_null(val: str) -> bool:
    return val.strip().lower() in NULL_VALUES

def quality_score(row: dict, taxonomy: list[str]) -> int:
    """Score 0-5 based on data completeness."""
    score = 0
    if not is_null(row.get("job_title", "")):      score += 1
    if not is_null(row.get("description_text", "")) and len(row["description_text"]) > 200:
                                                    score += 1
    if not is_null(row.get("apply_link", "")):      score += 1
    if not is_null(row.get("salary_formatted", "")): score += 1
    # Bonus: skills can be extracted
    desc = row.get("description_text", "")
    if extract_skills(desc, taxonomy[:50]):         score += 1  # quick check top-50 skills
    return score


# ── Step 3: Normalize fields ──────────────────────────────────

def normalize_job_type(raw: str) -> str:
    t = raw.lower()
    if "intern" in t or "تدريب" in t or "فترة تدريبية" in t:
        return "Internship"
    if "part" in t or "جزئي" in t:
        return "Part-time"
    if "contract" in t or "عقد" in t:
        return "Contract"
    if "temp" in t or "مؤقت" in t:
        return "Temporary"
    # Full-time / Permanent / دوام كامل / دائم → Full-time
    return "Full-time"


def clean(val: str) -> str:
    return "" if is_null(val) else val.strip()


def map_row(row: dict, taxonomy: list[str], job_id: int) -> dict:
    desc = row.get("description_text", "")

    # Extract years from description
    exp_m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", desc, re.IGNORECASE)
    experience_years = f"{exp_m.group(1)}+" if exp_m else ""

    return {
        "job_id":           str(job_id),
        "title":            clean(row.get("job_title", "")),
        "company":          clean(row.get("company_name", "")),
        "location":         clean(row.get("location", "")),
        "description":      desc.strip(),
        "required_skills":  extract_skills(desc, taxonomy),
        "preferred_skills": [],
        "experience_years": experience_years,
        "salary_range":     clean(row.get("salary_formatted", "")),
        "job_type":         normalize_job_type(row.get("job_type", "")),
        "industry":         "",           # not in new dataset
        "apply_link":       clean(row.get("apply_link", "")),
        # Extra fields (kept as bonus metadata — ignored by matching algo)
        "country":          clean(row.get("country", "")),
    }


# ── Main ──────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Wasel — New Jobs Dataset Preparation (DRY RUN)")
    print("  ⚠️  Nothing will be uploaded to Qdrant")
    print("=" * 60)

    # Load old dataset
    print(f"\n📂 Loading existing dataset: {OLD_JSON}")
    with open(OLD_JSON, encoding="utf-8") as f:
        old_jobs: list[dict] = json.load(f)
    print(f"   Existing jobs: {len(old_jobs)}")

    # Build taxonomy
    taxonomy = build_taxonomy(old_jobs)
    print(f"   Taxonomy: {len(taxonomy)} skills")
    with open(TAXONOMY_OUT, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)
    print(f"   Taxonomy saved → {TAXONOMY_OUT}")

    # Load new CSV
    print(f"\n📂 Loading new CSV: {NEW_CSV}")
    with open(NEW_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"   Raw rows: {len(rows)}")

    # Filter: SA only + has title + description > 100 chars
    filtered = [
        r for r in rows
        if r.get("country", "").strip().upper() == "SA"
        and not is_null(r.get("job_title", ""))
        and len(r.get("description_text", "")) > 100
    ]
    print(f"   After filter (SA + title + description): {len(filtered)}")

    # Score and sort
    print(f"\n⚙️  Scoring {len(filtered)} rows… (this takes ~30s)")
    scored = [(r, quality_score(r, taxonomy)) for r in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Take top N
    top_rows = [r for r, _ in scored[:TOP_N]]
    print(f"   Selected top {len(top_rows)} rows")

    # Score distribution
    score_dist = {}
    for _, s in scored[:TOP_N]:
        score_dist[s] = score_dist.get(s, 0) + 1
    print(f"   Score distribution: {dict(sorted(score_dist.items(), reverse=True))}")

    # Map to schema
    print(f"\n🔄 Mapping to schema…")
    start_id = max(int(j.get("job_id", 0)) for j in old_jobs) + 1
    new_jobs = [map_row(row, taxonomy, start_id + i) for i, row in enumerate(top_rows)]

    # Stats
    with_skills    = sum(1 for j in new_jobs if j["required_skills"])
    with_apply     = sum(1 for j in new_jobs if j["apply_link"])
    with_salary    = sum(1 for j in new_jobs if j["salary_range"])
    avg_skills     = sum(len(j["required_skills"]) for j in new_jobs) / len(new_jobs)

    print(f"\n📊 STATS:")
    print(f"   Total prepared:          {len(new_jobs)}")
    print(f"   With skills extracted:   {with_skills} ({with_skills/len(new_jobs)*100:.1f}%)")
    print(f"   With apply_link:         {with_apply} ({with_apply/len(new_jobs)*100:.1f}%)")
    print(f"   With salary:             {with_salary} ({with_salary/len(new_jobs)*100:.1f}%)")
    print(f"   Avg skills per job:      {avg_skills:.1f}")

    # Sample output
    print(f"\n📋 SAMPLE (first 3 jobs):")
    for job in new_jobs[:3]:
        print(json.dumps(job, ensure_ascii=False, indent=2))
        print("---")

    # Save
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(new_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved → {OUT_JSON}")
    print(f"   {len(new_jobs)} new jobs ready for review")
    print(f"\n⚠️  Review the file before uploading!")
    print(f"   When ready, run:  make build-rag")


if __name__ == "__main__":
    main()
