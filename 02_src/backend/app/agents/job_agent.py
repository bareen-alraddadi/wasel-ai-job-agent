"""
Wasel — Agent 2: Job Agent
Matches candidate to jobs via LLM JD parsing or RAG job discovery.
"""
import logging
from typing import Dict, List, Optional

from app.tools.job_tools import analyze_job_posting_llm, match_resume_to_job, search_jobs

logger = logging.getLogger(__name__)


class JobAgent:
    """
    Agent 2 — Job Agent

    Mode A: If the user provides a job description, the agent uses the LLM to
    extract accurate job requirements, then compares them with the CV.

    Mode B: If the user does not provide a job description, the agent uses the
    RAG pipeline to retrieve similar jobs from the Qdrant job index.
    """

    async def run(
        self,
        resume_analysis: Dict,
        job_description: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict]:
        profile = resume_analysis.get("profile", {})
        candidate_skills = profile.get("skills", [])

        if job_description and job_description.strip():
            logger.info("[JobAgent] Mode A — LLM analysis of provided JD")
            return await self._mode_a(profile, job_description)

        logger.info("[JobAgent] Mode B — RAG job discovery")
        return await self._mode_b(profile, candidate_skills, top_k)

    async def _mode_a(self, profile: Dict, job_description: str) -> List[Dict]:
        """Analyze a single provided job description using the LLM parser."""
        job_profile = await analyze_job_posting_llm(job_description)
        score, matched, missing, explanation = match_resume_to_job(profile, job_profile)

        return [{
            "job": job_profile,
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing,
            "match_explanation": explanation,
        }]

    async def _mode_b(self, profile: Dict, candidate_skills: List[str], top_k: int) -> List[Dict]:
        """Semantic job search through RAG, then score each retrieved job."""
        # Fetch 3× candidates so deduplication still leaves enough unique results
        raw_jobs = await search_jobs(candidate_skills, top_k=top_k * 3)

        results = []
        for raw_job in raw_jobs:
            score, matched, missing, explanation = match_resume_to_job(profile, raw_job)
            results.append({
                "job": {
                    "title": raw_job.get("title", ""),
                    "company": raw_job.get("company", ""),
                    "location": raw_job.get("location", ""),
                    "description": raw_job.get("description", ""),
                    "required_skills": raw_job.get("required_skills", []),
                    "preferred_skills": raw_job.get("preferred_skills", []),
                    "job_type": raw_job.get("job_type", ""),
                    "salary_range": raw_job.get("salary_range", ""),
                    "apply_link": raw_job.get("apply_link", ""),
                    "similarity": raw_job.get("_similarity"),
                },
                "match_score": score,
                "matched_skills": matched,
                "missing_skills": missing,
                "match_explanation": explanation,
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        results = results[:top_k]  # Keep only the best top_k unique results
        logger.info(f"[JobAgent] Found {len(results)} job matches")
        return results
