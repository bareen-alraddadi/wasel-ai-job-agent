"""
Wasel — Gap & Roadmap Tools  (GPT-4 mini)
find_skill_gaps · recommend_learning_path · build_job_roadmap · generate_interview_questions
"""
import json, re, logging
from typing import Dict, List

from app.core.llm import chat_complete

logger = logging.getLogger(__name__)


def find_skill_gaps(resume_profile: Dict, job_profile: Dict, missing_skills: List[str]) -> List[Dict]:
    """Identify and prioritise skill gaps between candidate and target job."""
    required_skills = {s.lower() for s in job_profile.get("required_skills", [])}
    gaps = []
    for skill in missing_skills:
        priority = "high" if skill.lower() in required_skills else "medium"
        gaps.append({
            "skill": skill,
            "priority": priority,
            "description": (
                f"'{skill}' is {'required' if priority == 'high' else 'preferred'} "
                f"for {job_profile.get('title', 'this role')}."
            ),
            "estimated_time": _estimate_time(skill),
        })
    gaps.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
    return gaps


def _estimate_time(skill: str) -> str:
    s = skill.lower()
    if any(k in s for k in ["git","sql","html","css","linux","bash"]):      return "1-2 weeks"
    if any(k in s for k in ["machine learning","deep learning","pytorch","kubernetes","aws","tensorflow"]): return "2-4 months"
    if any(k in s for k in ["python","javascript","react","docker","fastapi","pandas"]): return "3-6 weeks"
    return "2-4 weeks"


async def recommend_learning_path(gaps: List[Dict], top_resources: int = 2) -> List[Dict]:
    """Enrich each gap with real learning resources — all lookups run in parallel."""
    import asyncio
    from app.rag.pipeline import rag_pipeline

    async def _enrich_gap(gap: Dict) -> Dict:
        skill = gap["skill"]
        rag = await rag_pipeline.search_resources(skill, top_k=2)
        if rag:
            resources = rag[:top_resources]
        else:
            resources = await _llm_resources(skill)
        return {**gap, "resources": resources}

    # Run all gap enrichments in parallel instead of sequentially
    tasks = [_enrich_gap(gap) for gap in gaps[:8]]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out any failed tasks gracefully
    enriched = []
    for gap, result in zip(gaps[:8], results):
        if isinstance(result, Exception):
            logger.warning(f"Gap enrichment failed for '{gap['skill']}': {result}")
            enriched.append({**gap, "resources": []})
        else:
            enriched.append(result)
    return enriched


async def _llm_resources(skill: str) -> List[Dict]:
    """GPT-4 mini fallback for learning resource suggestions."""
    try:
        raw = await chat_complete(
            system="You are a career learning advisor. Respond ONLY with valid JSON — no markdown fences.",
            messages=[{
                "role": "user",
                "content": (
                    f"Suggest 2 real online learning resources for the skill: '{skill}'.\n"
                    "Return a JSON array exactly like:\n"
                    '[{"title":"...","provider":"...","url":"https://...","duration":"...","level":"beginner|intermediate|advanced"}]'
                ),
            }],
            max_tokens=300,
            json_mode=True,
        )
        # json_mode returns a JSON object; wrap list if needed
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        # GPT sometimes wraps in {"resources": [...]}
        for v in parsed.values():
            if isinstance(v, list):
                return v
        return []
    except Exception as e:
        logger.warning(f"LLM resource lookup failed for '{skill}': {e}")
        return [{
            "title": f"Learn {skill.title()}",
            "provider": "Coursera",
            "url": f"https://www.coursera.org/search?query={skill.replace(' ','+')}",
            "duration": "4-6 weeks",
            "level": "intermediate",
        }]


async def build_job_roadmap(
    resume_profile: Dict,
    job_profile: Dict,
    enriched_gaps: List[Dict],
    match_score: float,
) -> Dict:
    """Build phased 30/90/180-day career roadmap via GPT-4 mini."""
    high  = [g for g in enriched_gaps if g.get("priority") == "high"]
    medium = [g for g in enriched_gaps if g.get("priority") == "medium"]

    milestones = [
        {
            "phase": "30 days",
            "title": "Quick wins & foundation",
            "goals": [
                "Update LinkedIn profile and list all current skills",
                f"Start learning: {', '.join(g['skill'] for g in high[:2]) or 'top priority skills'}",
                "Build or update 1 portfolio project",
            ],
            "skills": [g["skill"] for g in high[:2]],
        },
        {
            "phase": "90 days",
            "title": "Core skills & projects",
            "goals": [
                "Complete courses for all high-priority skills",
                "Build 2 portfolio projects showcasing required skills",
                f"Target roles matching 60-70%: {job_profile.get('title','')}",
            ],
            "skills": [g["skill"] for g in high],
        },
        {
            "phase": "6 months",
            "title": "Job-ready & application",
            "goals": [
                "Complete preferred skills learning",
                "Apply to 5+ target roles per week",
                "Practice mock interviews weekly",
                "Network at 2+ tech meetups or online communities",
            ],
            "skills": [g["skill"] for g in medium],
        },
    ]

    interview_qs = await generate_interview_questions(
        job_profile.get("title", "Software Engineer"),
        job_profile.get("required_skills", [])[:8],
    )

    readiness = "1-2 months" if match_score >= 70 else "3-6 months"
    return {
        "target_role": job_profile.get("title", "Target Role"),
        "target_company": job_profile.get("company", ""),
        "total_gap_score": round(100 - match_score, 1),
        "skill_gaps": enriched_gaps,
        "milestones": milestones,
        "interview_questions": interview_qs,
        "summary": (
            f"You currently match {match_score:.0f}% of the requirements for "
            f"{job_profile.get('title','this role')} at {job_profile.get('company','')}. "
            f"With {len(high)} critical skill(s) to develop and {len(medium)} preferred skill(s) "
            f"to strengthen, you can be job-ready in approximately {readiness}."
        ),
    }


async def generate_interview_questions(role: str, skills: List[str]) -> List[str]:
    """Generate tailored interview questions using GPT-4 mini."""
    try:
        skills_str = ", ".join(skills[:8])
        raw = await chat_complete(
            system="You are a technical interviewer. Respond ONLY with valid JSON — no markdown.",
            messages=[{
                "role": "user",
                "content": (
                    f"Generate 8 interview questions for a '{role}' role requiring: {skills_str}.\n"
                    "Mix 4 technical and 4 behavioral questions.\n"
                    'Return JSON: {"questions": ["q1","q2",...]}'
                ),
            }],
            max_tokens=500,
            json_mode=True,
        )
        data = json.loads(raw)
        qs = data.get("questions", [])
        if isinstance(qs, list) and qs:
            return qs
        # fallback: any list value
        for v in data.values():
            if isinstance(v, list):
                return v
        return _default_questions(role, skills)
    except Exception as e:
        logger.warning(f"Interview Q generation failed: {e}")
        return _default_questions(role, skills)


def _default_questions(role: str, skills: List[str]) -> List[str]:
    s0 = skills[0] if skills else "your main technology"
    s1 = skills[1] if len(skills) > 1 else "a new tool"
    return [
        f"Walk me through a project where you used {s0}.",
        "Describe the most challenging technical problem you have solved.",
        f"How would you approach learning {s1} quickly?",
        "How do you ensure code quality in a fast-moving team?",
        "Tell me about a time you disagreed with a technical decision.",
        "How do you stay current with developments in your field?",
        "Describe a situation where you had to work under a tight deadline.",
        f"Where do you see yourself in 2-3 years as a {role}?",
    ]
