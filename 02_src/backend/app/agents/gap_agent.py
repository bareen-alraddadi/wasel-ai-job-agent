"""
Wasel — Agent 3: Gap Agent
Identifies skill gaps and builds a personalized career roadmap.
"""
import logging
from typing import Dict, List

from app.tools.gap_tools import (
    find_skill_gaps,
    recommend_learning_path,
    build_job_roadmap,
    generate_interview_questions,
)

logger = logging.getLogger(__name__)


class GapAgent:
    """
    Agent 3 — Gap Agent
    Responsible for:
    - Identifying prioritized skill gaps
    - Recommending learning resources per gap
    - Building phased career roadmap (30/90/180 days)
    - Generating interview questions
    """

    async def run(
        self,
        resume_analysis: Dict,
        job_matches: List[Dict],
    ) -> Dict:
        """
        Build a full career roadmap for the top job match.
        Returns roadmap dict.
        """
        if not job_matches:
            return {"error": "No job matches to build roadmap from"}

        # Use the best match as the target
        top_match = job_matches[0]
        job_profile = top_match.get("job", {})
        missing_skills = top_match.get("missing_skills", [])
        match_score = top_match.get("match_score", 0)
        resume_profile = resume_analysis.get("profile", {})

        logger.info(
            f"[GapAgent] Building roadmap for '{job_profile.get('title', 'role')}' "
            f"with {len(missing_skills)} gaps"
        )

        # Step 1: Structure gaps with priority
        gaps = find_skill_gaps(resume_profile, job_profile, missing_skills)

        # Step 2: Enrich gaps with learning resources (RAG + LLM)
        enriched_gaps = await recommend_learning_path(gaps)

        # Step 3: Build full roadmap with milestones
        roadmap = await build_job_roadmap(
            resume_profile, job_profile, enriched_gaps, match_score
        )

        logger.info(f"[GapAgent] Roadmap built. {len(enriched_gaps)} gaps addressed.")
        return roadmap
