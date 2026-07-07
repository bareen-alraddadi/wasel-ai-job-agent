"""
Wasel — Daily Job Refresh Cron Script
Fetches fresh Saudi tech jobs from LinkedIn via the Job API,
maps them to the Qdrant schema, embeds, and upserts into Qdrant.
Also removes jobs older than 30 days.

Run manually:
    python scripts/refresh_jobs_cron.py

Schedule (Linux cron — runs at 2 AM daily):
    0 2 * * * cd /path/to/wasel/backend && python scripts/refresh_jobs_cron.py >> logs/cron.log 2>&1
"""

import os
import sys
import re
import json
import uuid
import asyncio
import logging
import httpx
from datetime import datetime, timedelta, date
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, Range
from openai import AsyncOpenAI
from app.core.config import settings

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("refresh_jobs")

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

JOB_API_BASE   = "https://j0b-api.vercel.app/api/jobs"
COLLECTION     = "wasel_jobs"
RESULTS_PER_TERM = 15        # 15 × 15 terms = 225 new jobs/day
TTL_DAYS       = 30           # delete jobs older than this
EMBED_BATCH    = 20           # OpenAI embedding batch size

# Saudi Arabia tech job categories
SEARCH_TERMS = [
    "Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Mobile Developer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "Product Manager",
    "UI UX Designer",
    "Business Analyst",
]

# ── Skill taxonomy (181 skills, sorted longest-first to avoid partial matches) ──
_TAXONOMY_PATH = Path(__file__).parent.parent.parent / "data" / "jobs_dataset" / "skills_taxonomy.json"

def _load_taxonomy() -> list[str]:
    if _TAXONOMY_PATH.exists():
        with open(_TAXONOMY_PATH, encoding="utf-8") as f:
            skills = json.load(f)
        return sorted(skills, key=len, reverse=True)
    # Fallback core taxonomy if file missing
    return sorted([
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "React", "Vue.js", "Angular", "Node.js", "FastAPI", "Django", "Flask", "Spring Boot",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "Google Cloud Platform", "Docker", "Kubernetes",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn",
        "pandas", "NumPy", "SQL", "Git", "GitHub", "Linux", "CI/CD",
        "REST API", "GraphQL", "Microservices", "Terraform", "Ansible",
    ], key=len, reverse=True)

TAXONOMY: list[str] = _load_taxonomy()

# Short ambiguous words that cause false positives — excluded from matching
_BLOCKLIST = {"r", "c", "go", "ai"}

def extract_skills(text: str) -> list[str]:
    """Extract skills from free-text using word-boundary regex against taxonomy."""
    if not text:
        return []
    found = []
    text_lower = text.lower()
    for skill in TAXONOMY:
        if skill.lower() in _BLOCKLIST:
            continue
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found[:20]   # cap at 20 skills per job

# ═══════════════════════════════════════════════════════════════════════
# SCHEMA MAPPER
# ═══════════════════════════════════════════════════════════════════════

JOB_TYPE_MAP = {
    "fulltime":   "Full-time",
    "full_time":  "Full-time",
    "full-time":  "Full-time",
    "parttime":   "Part-time",
    "part_time":  "Part-time",
    "contract":   "Contract",
    "internship": "Internship",
    "temporary":  "Temporary",
}

def _clean_company(raw: str) -> str:
    """Remove Arabic text and extra whitespace from company name."""
    # Remove Arabic characters and surrounding whitespace/pipes
    cleaned = re.sub(r"[\u0600-\u06FF\u0750-\u077F]+", "", raw)
    cleaned = re.sub(r"\s*[|]\s*", " ", cleaned)
    return cleaned.strip(" |-") or raw.strip()

def _clean_location(raw: str) -> str:
    """Extract city name: 'Al Khobar, Eastern, Saudi Arabia' → 'Al Khobar'"""
    if not raw:
        return "Saudi Arabia"
    parts = [p.strip() for p in raw.split(",")]
    return parts[0] if parts else raw

def _infer_industry(title: str, api_industry: str | None) -> str:
    """Return company_industry if available, otherwise infer from job title."""
    if api_industry:
        return api_industry
    t = title.lower()
    if any(k in t for k in ["data", "analyst", "bi", "business intel"]):
        return "Data & Analytics"
    if any(k in t for k in ["machine learning", "ai ", "artificial", "nlp", "computer vision"]):
        return "Artificial Intelligence"
    if any(k in t for k in ["devops", "cloud", "infrastructure", "sre", "platform"]):
        return "Cloud & Infrastructure"
    if any(k in t for k in ["security", "cyber", "penetration", "soc"]):
        return "Cybersecurity"
    if any(k in t for k in ["product manager", "product owner"]):
        return "Product Management"
    if any(k in t for k in ["ui", "ux", "design", "frontend", "front-end"]):
        return "Design & Frontend"
    if any(k in t for k in ["mobile", "ios", "android", "flutter", "react native"]):
        return "Mobile Development"
    return "Software Engineering"

def map_to_qdrant_payload(raw: dict, search_term: str) -> dict | None:
    """
    Map a raw Job API response object to our Qdrant payload schema.
    Returns None if the job lacks minimum required fields.
    """
    title       = (raw.get("title") or "").strip()
    company     = (raw.get("company") or "").strip()
    description = (raw.get("description") or "").strip()

    # Skip jobs without title, company, or description
    if not title or not company or not description:
        return None

    job_id      = raw.get("id") or f"li-{uuid.uuid4().hex[:12]}"
    location    = _clean_location(raw.get("location") or "")
    company     = _clean_company(company)
    date_posted = raw.get("date_posted") or str(date.today())

    # Skills
    required_skills  = extract_skills(description)
    preferred_skills: list[str] = []   # LinkedIn rarely separates these in free text

    # Normalize job_type
    raw_type  = (raw.get("job_type") or "").lower().replace(" ", "_")
    job_type  = JOB_TYPE_MAP.get(raw_type, "Full-time")

    # Salary — LinkedIn almost never returns this
    salary_range = "Not specified"
    if raw.get("min_amount") and raw.get("max_amount"):
        currency = raw.get("currency", "SAR")
        salary_range = f"{int(raw['min_amount']):,}–{int(raw['max_amount']):,} {currency}"

    industry   = _infer_industry(title, raw.get("company_industry"))
    apply_link = raw.get("job_url") or ""

    return {
        # ── Core fields (indexed in Qdrant) ──────────────────
        "job_id":           job_id,
        "title":            title,
        "company":          company,
        "location":         location,
        "industry":         industry,
        "job_type":         job_type,
        # ── Content fields ────────────────────────────────────
        "description":      description,
        "required_skills":  required_skills,
        "preferred_skills": preferred_skills,
        "salary_range":     salary_range,
        "apply_link":       apply_link,
        # ── Metadata for TTL cleanup ──────────────────────────
        "date_posted":      date_posted,
        "source":           "linkedin",
        "search_term":      search_term,
        "ingested_at":      datetime.utcnow().isoformat(),
    }

# ═══════════════════════════════════════════════════════════════════════
# JOB API FETCHER
# ═══════════════════════════════════════════════════════════════════════

async def fetch_jobs_for_term(client: httpx.AsyncClient, term: str) -> list[dict]:
    """Call the Job API for a single search term and return raw job dicts."""
    params = {
        "site_name":                  "linkedin",
        "search_term":                term,
        "location":                   "saudi arabia",
        "results_wanted":             RESULTS_PER_TERM,
        "linkedin_fetch_description": "true",
        "description_format":         "markdown",
        "enforce_annual_salary":      "true",
    }
    try:
        resp = await client.get(JOB_API_BASE, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("jobs", [])
        log.info(f"  [{term}] fetched {len(jobs)} raw jobs")
        return jobs
    except Exception as e:
        log.warning(f"  [{term}] API error: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════
# EMBEDDING
# ═══════════════════════════════════════════════════════════════════════

async def embed_batch(oai: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    try:
        resp = await oai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [d.embedding for d in resp.data]
    except Exception as e:
        log.error(f"Embedding error: {e}")
        return []

def build_embed_text(job: dict) -> str:
    """Build the text that will be embedded for semantic search."""
    skills_str = ", ".join(job.get("required_skills", []) + job.get("preferred_skills", []))
    return (
        f"{job['title']} at {job['company']} in {job['location']}. "
        f"Industry: {job['industry']}. Skills: {skills_str}. "
        f"{job['description'][:400]}"
    )

# ═══════════════════════════════════════════════════════════════════════
# QDRANT UPSERT
# ═══════════════════════════════════════════════════════════════════════

def upsert_jobs(qdrant: QdrantClient, jobs: list[dict], vectors: list[list[float]]) -> int:
    """Upsert a batch of job payloads + their vectors into Qdrant."""
    points = []
    for job, vec in zip(jobs, vectors):
        if not vec:
            continue
        # Deterministic UUID from job_id ensures re-runs overwrite duplicates
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"job|{job['job_id']}"))
        points.append(PointStruct(id=point_id, vector=vec, payload=job))

    if points:
        qdrant.upsert(collection_name=COLLECTION, points=points)
    return len(points)

# ═══════════════════════════════════════════════════════════════════════
# TTL CLEANUP
# ═══════════════════════════════════════════════════════════════════════

def cleanup_old_jobs(qdrant: QdrantClient) -> int:
    """
    Delete jobs from Qdrant where date_posted is older than TTL_DAYS.
    Uses scroll + delete by IDs (Qdrant doesn't support date filtering natively).
    """
    cutoff = (datetime.utcnow() - timedelta(days=TTL_DAYS)).date().isoformat()
    log.info(f"Cleaning up jobs posted before {cutoff}...")

    deleted = 0
    next_offset = None

    while True:
        # Scroll through all points in batches
        results, next_offset = qdrant.scroll(
            collection_name=COLLECTION,
            scroll_filter=None,
            limit=256,
            offset=next_offset,
            with_payload=["date_posted"],
            with_vectors=False,
        )

        old_ids = [
            r.id for r in results
            if (r.payload or {}).get("date_posted", "9999") < cutoff
        ]

        if old_ids:
            qdrant.delete(
                collection_name=COLLECTION,
                points_selector=old_ids,
            )
            deleted += len(old_ids)

        if next_offset is None:
            break

    log.info(f"Deleted {deleted} stale jobs (older than {TTL_DAYS} days)")
    return deleted

# ═══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════

async def main():
    log.info("=" * 60)
    log.info("  Wasel — Daily Job Refresh")
    log.info(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    log.info("=" * 60)

    # ── Clients ───────────────────────────────────────────────
    qdrant = QdrantClient(
        url=settings.URL_QDRANT,
        api_key=settings.API_KEY_QDRANT,
        timeout=60,
    )
    oai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Verify Qdrant connection
    try:
        cols = [c.name for c in qdrant.get_collections().collections]
        if COLLECTION not in cols:
            log.error(f"Collection '{COLLECTION}' not found! Run build_qdrant_index.py first.")
            return
        info = qdrant.get_collection(COLLECTION)
        log.info(f"Connected to Qdrant. '{COLLECTION}' has {info.points_count} points.")
    except Exception as e:
        log.error(f"Qdrant connection failed: {e}")
        return

    # ── Step 1: TTL Cleanup (before fetching new jobs) ───────
    log.info("\n[1/4] Cleaning up old jobs first...")
    deleted = cleanup_old_jobs(qdrant)

    # ── Step 2: Fetch from Job API ────────────────────────────
    log.info(f"\n[2/4] Fetching jobs for {len(SEARCH_TERMS)} search terms...")
    all_raw: list[tuple[dict, str]] = []  # (raw_job, search_term)

    async with httpx.AsyncClient() as http:
        for term in SEARCH_TERMS:
            raw_jobs = await fetch_jobs_for_term(http, term)
            for rj in raw_jobs:
                all_raw.append((rj, term))
            # Small delay to be polite to the API
            await asyncio.sleep(1.5)

    log.info(f"  Total raw jobs fetched: {len(all_raw)}")

    # ── Step 3: Map & deduplicate ─────────────────────────────
    log.info("\n[3/4] Mapping schema and extracting skills...")
    mapped_jobs: list[dict] = []
    seen_ids: set[str] = set()
    skipped = 0

    for raw_job, term in all_raw:
        payload = map_to_qdrant_payload(raw_job, term)
        if payload is None:
            skipped += 1
            continue
        # Deduplicate by job_id
        if payload["job_id"] in seen_ids:
            continue
        seen_ids.add(payload["job_id"])
        mapped_jobs.append(payload)

    log.info(f"  Valid jobs: {len(mapped_jobs)} | Skipped (no description): {skipped}")

    # ── Step 4: Embed + Upsert in batches ────────────────────
    log.info(f"\n[4/4] Embedding and upserting to Qdrant (batch={EMBED_BATCH})...")
    total_upserted = 0

    for i in range(0, len(mapped_jobs), EMBED_BATCH):
        batch = mapped_jobs[i: i + EMBED_BATCH]
        texts  = [build_embed_text(j) for j in batch]
        vectors = await embed_batch(oai, texts)

        if not vectors:
            log.warning(f"  Batch {i//EMBED_BATCH + 1}: embedding failed, skipping.")
            continue

        n = upsert_jobs(qdrant, batch, vectors)
        total_upserted += n
        log.info(f"  Upserted {total_upserted}/{len(mapped_jobs)} jobs...")

    # ── Summary ───────────────────────────────────────────────
    info = qdrant.get_collection(COLLECTION)
    log.info("\n" + "=" * 60)
    log.info("  ✅ DONE")
    log.info(f"  Old jobs deleted  : {deleted}")
    log.info(f"  New jobs upserted : {total_upserted}")
    log.info(f"  Total in Qdrant   : {info.points_count}")
    log.info("=" * 60)



if __name__ == "__main__":
    asyncio.run(main())
