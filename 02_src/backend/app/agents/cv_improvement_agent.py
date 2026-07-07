"""
Wasel — CV Improvement Agent
Generates specific, actionable CV improvement tips for a target job role.
Each tip is tied to a concrete CV section (Summary, Skills, Experience, Projects).
"""
import json
import logging
from typing import Dict, List

from app.core.llm import chat_complete

logger = logging.getLogger(__name__)


class CVImprovementAgent:
    """
    Analyzes the gap between a candidate's CV and a specific job posting,
    then produces structured, section-by-section CV improvement advice.
    """

    async def generate(
        self,
        profile: Dict,
        job_title: str,
        job_company: str,
        required_skills: List[str],
        missing_skills: List[str],
        match_score: float,
    ) -> List[Dict]:
        """
        Returns a list of actionable CV improvement tips, each with:
        - section: which CV section to improve (e.g. "Summary", "Skills")
        - action:  what to do ("Add", "Edit", "Rewrite", "Create New Section")
        - tip:     the specific, detailed instruction
        """
        logger.info(f"[CVImprovementAgent] Generating tips for '{job_title}' at '{job_company}'")

        profile_text = self._format_profile(profile)

        try:
            raw = await chat_complete(
                system=(
                    "You are an expert CV coach. You give specific, actionable, and realistic advice "
                    "on how to improve a CV for a specific job. You ALWAYS respond with valid JSON only."
                ),
                messages=[{
                    "role": "user",
                    "content": f"""
A candidate is applying for: **{job_title}** at **{job_company}**
Current match score: {match_score:.0f}%
Missing skills: {', '.join(missing_skills) if missing_skills else 'None'}
Required skills for role: {', '.join(required_skills[:10]) if required_skills else 'Not specified'}

Candidate's current CV profile:
{profile_text}

Generate 4-6 specific CV improvement tips. Each tip must reference a specific CV section.
Return ONLY a JSON array with this exact structure:
[
  {{
    "section": "Summary",
    "action": "Edit",
    "tip": "Rewrite your opening sentence to say 'Full Stack Developer specializing in React and Node.js' to directly match the job title."
  }},
  {{
    "section": "Skills",
    "action": "Add",
    "tip": "Add Docker and Kubernetes to your technical skills section, as they are required for this role."
  }},
  {{
    "section": "Experience",
    "action": "Edit",
    "tip": "In your role at [Company], add a bullet point mentioning any cloud infrastructure work (AWS, GCP) even if brief."
  }},
  {{
    "section": "Projects",
    "action": "Create New Section",
    "tip": "Add a Projects section with at least one project that demonstrates REST API development or microservices architecture."
  }}
]

Allowed actions: "Add", "Edit", "Rewrite", "Create New Section", "Remove"
Allowed sections: "Summary", "Skills", "Experience", "Education", "Projects", "Certifications", "Languages"
""",
                }],
                max_tokens=800,
                json_mode=True,
            )

            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            # Sometimes LLM wraps in an object
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return []

        except Exception as e:
            logger.error(f"[CVImprovementAgent] Failed: {e}")
            # Return safe fallback tips based on missing skills
            return self._fallback_tips(missing_skills, job_title)

    def _format_profile(self, profile: Dict) -> str:
        lines = []
        if profile.get("name"):
            lines.append(f"Name: {profile['name']}")
        if profile.get("summary"):
            lines.append(f"Summary: {profile['summary'][:300]}")
        skills = profile.get("skills", [])
        if skills:
            lines.append(f"Current Skills: {', '.join(skills[:15])}")
        experience = profile.get("experience", [])
        if experience:
            lines.append("Experience:")
            for exp in experience[:3]:
                lines.append(f"  - {exp.get('title', '')} at {exp.get('company', '')}")
        education = profile.get("education", [])
        if education:
            lines.append("Education:")
            for edu in education[:2]:
                lines.append(f"  - {edu.get('degree', '')} from {edu.get('institution', '')}")
        return "\n".join(lines) if lines else "CV data not fully parsed."

    def _fallback_tips(self, missing_skills: List[str], job_title: str) -> List[Dict]:
        tips = []
        if missing_skills:
            tips.append({
                "section": "Skills",
                "action": "Add",
                "tip": f"Add these missing skills to your Skills section: {', '.join(missing_skills[:5])}."
            })
        tips.append({
            "section": "Summary",
            "action": "Edit",
            "tip": f"Rewrite your Summary to mention the target role '{job_title}' explicitly in the first sentence."
        })
        tips.append({
            "section": "Projects",
            "action": "Create New Section",
            "tip": "Add a Projects section with 2-3 relevant projects that showcase your technical abilities."
        })
        return tips
