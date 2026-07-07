"""
Wasel — Cover Letter Agent
Generates a tailored, professional cover letter based on the candidate's
resume profile and a target job description.
"""
import logging
from typing import Dict, List

from app.core.llm import chat_complete

logger = logging.getLogger(__name__)


class CoverLetterAgent:
    """
    Agent responsible for generating a tailored cover letter.
    Uses the same chat_complete pattern as the other agents in the project.
    """

    async def generate(self, profile: Dict, job_description: str) -> str:
        """
        Generates a professional cover letter.
        Returns the cover letter text as a string.
        """
        logger.info("[CoverLetterAgent] Generating tailored cover letter...")

        profile_text = self._format_profile(profile)

        try:
            response = await chat_complete(
                system=(
                    "You are an expert Career Coach and Executive Resume Writer. "
                    "Write highly professional, compelling, and concise cover letters. "
                    "Output only the cover letter text — no extra commentary, no markdown code blocks."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Write a tailored cover letter based on the following candidate profile and job description.\n\n"
                        f"Candidate Profile:\n{profile_text}\n\n"
                        f"Job Description:\n{job_description}\n\n"
                        f"Rules:\n"
                        f"1. Do NOT use placeholders like [Company Name] — adapt gracefully if info is missing.\n"
                        f"2. Highlight the intersection between the candidate's skills/experience and the job requirements.\n"
                        f"3. Keep it to 3-4 paragraphs maximum.\n"
                        f"4. Write in a professional, confident, and enthusiastic tone."
                    ),
                }],
                max_tokens=700,
            )
            return response.strip()
        except Exception as e:
            logger.error(f"[CoverLetterAgent] Failed to generate cover letter: {e}")
            return ""

    def _format_profile(self, profile: Dict) -> str:
        """Format the resume profile into readable text for the prompt."""
        lines = []

        name = profile.get("name", "")
        if name:
            lines.append(f"Name: {name}")

        if profile.get("summary"):
            lines.append(f"Professional Summary: {profile['summary']}")

        skills: List[str] = profile.get("skills", [])
        if skills:
            lines.append(f"Skills: {', '.join(skills[:20])}")

        experience = profile.get("experience", [])
        if experience:
            lines.append("Experience:")
            for exp in experience[:3]:  # limit to latest 3 roles
                title   = exp.get("title", "")
                company = exp.get("company", "")
                desc    = exp.get("description", "")
                lines.append(f"  - {title} at {company}: {desc[:150]}")

        education = profile.get("education", [])
        if education:
            lines.append("Education:")
            for edu in education[:2]:
                degree = edu.get("degree", "")
                field  = edu.get("field_of_study", "")
                school = edu.get("institution", "")
                lines.append(f"  - {degree} in {field} from {school}")

        return "\n".join(lines) if lines else "CV data not available."
