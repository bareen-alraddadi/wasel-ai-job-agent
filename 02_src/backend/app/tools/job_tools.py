"""
Wasel — Job Tools

This module extracts job requirements, matches resumes to jobs, and calls the RAG
pipeline for semantic job search.
"""
import json
import logging
import re
from typing import Dict, List, Tuple

from app.core.llm import chat_complete
from app.tools.resume_tools import extract_skills

logger = logging.getLogger(__name__)


async def analyze_job_posting_llm(text: str) -> Dict:
    """
    Parse a job description using the LLM instead of regex-only matching.

    Why this matters:
    - Regex can confuse words like "excellent" with "Excel".
    - Regex can confuse "scalable" with "Scala".
    - The LLM understands context and extracts only real technical skills.
    """
    if not text or not text.strip():
        return analyze_job_posting(text)

    system_prompt = """
You are a precise job-description parser for an AI career assistant.

Extract only explicit, real job requirements from the text.

Critical rules:
- Do NOT treat adjectives as skills.
- "excellent" is NOT "Excel".
- "scalable" is NOT "Scala".
- "organized" is NOT a technical skill.
- "communication" is a soft skill only if explicitly required.
- Do NOT invent skills that are not clearly mentioned.
- Keep skill names short and canonical, e.g. "Python", "SQL", "Power BI", "Machine Learning".

Return JSON only with this exact shape:
{
  "title": "",
  "company": "",
  "location": "",
  "required_skills": [],
  "preferred_skills": [],
  "soft_skills": [],
  "experience_years": null,
  "education_level": "",
  "salary_range": "",
  "job_type": "",
  "description": ""
}
"""

    try:
        response = await chat_complete(
            messages=[{"role": "user", "content": text[:6000]}],
            system=system_prompt,
            max_tokens=900,
            temperature=0,
            json_mode=True,
        )
        data = json.loads(response)
    except Exception as e:
        logger.warning(f"LLM JD parsing failed, falling back to regex parser: {e}")
        return analyze_job_posting(text)

    required = _clean_skill_list(data.get("required_skills", []))
    preferred = [s for s in _clean_skill_list(data.get("preferred_skills", [])) if s not in required]

    return {
        "title": data.get("title") or _fallback_title(text),
        "company": data.get("company") or _company(text),
        "location": data.get("location") or "",
        "description": text[:2000],
        "required_skills": required[:15],
        "preferred_skills": preferred[:10],
        "soft_skills": data.get("soft_skills", []),
        "experience_years": data.get("experience_years"),
        "education_level": data.get("education_level") or "",
        "salary_range": data.get("salary_range") or _salary(text),
        "job_type": data.get("job_type") or _job_type(text),
    }


def analyze_job_posting(text: str) -> Dict:
    """
    Regex fallback parser.

    This is kept as a backup if the LLM call fails, but the JobAgent should use
    analyze_job_posting_llm() for normal JD analysis.
    """
    tl = text.lower()
    title = _fallback_title(text)

    all_skills = extract_skills(text)

    req_text = _section(text, ["required", "must have", "requirements", "you will need", "minimum"])
    pref_text = _section(text, ["preferred", "nice to have", "bonus", "plus", "desired"])

    required_skills = extract_skills(req_text) if req_text else []
    preferred_skills = [s for s in extract_skills(pref_text) if s not in required_skills] if pref_text else []

    if not required_skills:
        mid = max(1, len(all_skills) // 2)
        required_skills = all_skills[:mid]
        preferred_skills = all_skills[mid:]

    exp_m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience", tl)
    exp_yrs = int(exp_m.group(1)) if exp_m else None

    edu = ""
    if "bachelor" in tl or "b.s" in tl:
        edu = "Bachelor's"
    elif "master" in tl or "m.s" in tl:
        edu = "Master's"
    elif "phd" in tl or "doctorate" in tl:
        edu = "PhD"

    return {
        "title": title,
        "company": _company(text),
        "location": "",
        "description": text[:2000],
        "required_skills": required_skills[:15],
        "preferred_skills": preferred_skills[:10],
        "experience_years": exp_yrs,
        "education_level": edu,
        "salary_range": _salary(text),
        "job_type": _job_type(text),
    }


def _clean_skill_list(skills: List[str]) -> List[str]:
    """Normalize LLM skill output and remove common false positives."""
    blocked = {
        "excellent", "scalable", "organized", "motivated", "passionate",
        "fast-paced", "team player", "communication", "problem solving",
    }
    cleaned = []
    seen = set()
    for skill in skills or []:
        if not isinstance(skill, str):
            continue
        s = skill.strip()
        if not s:
            continue
        if s.lower() in blocked:
            continue
        key = s.lower()
        if key not in seen:
            cleaned.append(s)
            seen.add(key)
    return cleaned


def _fallback_title(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return lines[0][:80] if lines else "Software Engineer"


def _section(text: str, keywords: List[str]) -> str:
    tl = text.lower()
    for kw in keywords:
        i = tl.find(kw)
        if i != -1:
            return text[i: i + 600]
    return ""


def _company(text: str) -> str:
    for pat in [
        r"(?:at|@|join)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s+is|\s+are|\s+we|\.|,|\n)",
        r"([A-Z][A-Za-z0-9\s&.]+?)\s+is\s+(?:looking|hiring|seeking)",
    ]:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()[:50]
    return ""


def _salary(text: str) -> str:
    sal_m = re.search(r"\$[\d,]+\s*[-–]\s*\$[\d,]+|\d+[\d,]*\s*SAR\s*[-–]\s*[\d,]+\s*SAR", text, re.I)
    return sal_m.group(0) if sal_m else ""


def _job_type(text: str) -> str:
    tl = text.lower()
    if "full-time" in tl or "full time" in tl:
        return "Full-time"
    if "part-time" in tl or "part time" in tl:
        return "Part-time"
    if "internship" in tl or "intern" in tl:
        return "Internship"
    return ""


def match_resume_to_job(
    resume_profile: Dict,
    job_profile: Dict,
) -> Tuple[float, List[str], List[str], str]:
    """
    Calculate match score between candidate and job.
    Returns (score 0-100, matched_skills, missing_skills, explanation).

    Scoring weights:
      - Required skills : 80 points  (was 70 + hardcoded 10 exp)
      - Preferred skills: 20 points
      (exp_score removed — resume parser doesn't extract structured years,
       so hardcoding 10 for everyone was giving students the same score as seniors)
    """
    candidate = {s.lower() for s in resume_profile.get("skills", [])}
    required = [s.lower() for s in job_profile.get("required_skills", [])]
    preferred = [s.lower() for s in job_profile.get("preferred_skills", [])]

    if not required:
        return 50.0, list(candidate)[:5], [], "No specific requirements listed."

    matched_req = [s for s in required if s in candidate]
    matched_pref = [s for s in preferred if s in candidate]

    req_score = (len(matched_req) / max(len(required), 1)) * 80
    pref_score = (len(matched_pref) / max(len(preferred), 1)) * 20 if preferred else 0

    total = round(min(100, max(0, req_score + pref_score)), 1)

    matched = matched_req + matched_pref
    missing = [s for s in required if s not in candidate]
    explain = (
        f"Matched {len(matched_req)}/{len(required)} required skills"
        + (f" and {len(matched_pref)}/{len(preferred)} preferred skills." if preferred else ".")
    )

    return total, matched, missing, explain



async def search_jobs(candidate_skills: List[str], top_k: int = 3) -> List[Dict]:
    """
    RAG semantic search for top-K jobs from the Saudi dataset.

    This calls app.rag.pipeline.rag_pipeline, which uses OpenAI embeddings and
    Qdrant to retrieve semantically similar jobs.
    """
    from app.rag.pipeline import rag_pipeline

    query = "Jobs requiring: " + ", ".join(candidate_skills[:20])
    return await rag_pipeline.search_jobs(query, top_k=top_k)
