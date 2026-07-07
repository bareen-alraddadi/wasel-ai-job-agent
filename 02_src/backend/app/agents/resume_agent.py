"""
Wasel — Agent 1: Resume Agent
Parses, extracts, and scores the candidate's CV.
"""
import logging
from typing import Dict, Tuple

from app.tools.resume_tools import parse_resume, extract_skills, score_resume

logger = logging.getLogger(__name__)


class ResumeAgent:
    """
    Agent 1 — Resume Agent
    Responsible for:
    - Parsing CV (PDF/DOCX → structured profile)
    - Extracting skills
    - Scoring resume quality
    - Generating improvement suggestions
    """

    async def run(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Main entry point. Returns full resume analysis.
        """
        logger.info(f"[ResumeAgent] Parsing: {filename}")

        # Step 1: Parse resume
        profile = parse_resume(file_bytes, filename)
        if "error" in profile:
            return {"error": profile["error"], "profile": {}, "score": 0, "suggestions": []}

        # Step 2: Extract skills (already done in parse_resume but ensure completeness)
        if not profile.get("skills"):
            profile["skills"] = extract_skills(profile.get("raw_text", ""))

        # Step 3: Score resume
        score, breakdown, suggestions = score_resume(profile)

        logger.info(
            f"[ResumeAgent] Done. Score: {score} | Skills: {len(profile.get('skills', []))}"
        )

        return {
            "profile": profile,
            "score": score,
            "score_breakdown": breakdown,
            "suggestions": suggestions,
        }
