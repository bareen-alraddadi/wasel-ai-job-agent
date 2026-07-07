"""
Wasel — Chat Tools  (GPT-4 mini)
get_user_profile · get_latest_analysis · get_chat_history
search_learning_resources · generate_career_advice
"""
import json
from langchain_core.tools import tool
import logging
from typing import Dict, List, Optional

from app.memory.manager import supabase_memory, session_memory
from app.core.llm import chat_complete

logger = logging.getLogger(__name__)


async def get_user_profile(user_id: str) -> Optional[Dict]:
    return await supabase_memory.get_user(user_id)


async def get_latest_analysis(user_id: str) -> Optional[Dict]:
    return await supabase_memory.get_latest_analysis(user_id)


async def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    return await supabase_memory.get_chat_history(session_id, limit=limit)


async def search_learning_resources(query: str, top_k: int = 5) -> List[Dict]:
    from app.rag.pipeline import rag_pipeline
    return await rag_pipeline.search_resources(query, top_k=top_k)


async def generate_career_advice(
    user_message: str,
    session_context: Dict,
    chat_history: List[Dict],
) -> str:
    """GPT-4 mini career coach — uses full analysis context."""
    analysis  = session_context.get("analysis_result") or {}
    resume    = analysis.get("resume_analysis", {}).get("profile", {})
    matches   = analysis.get("job_matches", [])
    roadmap   = analysis.get("roadmap", {})

    # Build a compact context block for the system prompt
    ctx_parts = []
    if resume:
        ctx_parts.append(f"Candidate: {resume.get('name','User')}")
        ctx_parts.append(f"Skills: {', '.join(resume.get('skills',[])[:12])}")
    if matches:
        top = matches[0]
        ctx_parts.append(
            f"Top job match: {top.get('job',{}).get('title','')} at "
            f"{top.get('job',{}).get('company','')} — {top.get('match_score',0):.0f}% match"
        )
        ctx_parts.append(f"Missing skills: {', '.join(top.get('missing_skills',[])[:5])}")
    if roadmap:
        ctx_parts.append(f"Roadmap: {roadmap.get('summary','')[:200]}")

    system = (
        "You are Wasel, an expert AI career coach for tech professionals in Saudi Arabia. "
        "You are knowledgeable about the Saudi job market, Vision 2030 roles, and regional companies. "
        "Be specific, actionable, and encouraging. Reference the candidate's actual data when relevant. "
        "Keep responses concise (3-5 sentences) unless a detailed breakdown is needed.\n\n"
        + ("\n".join(ctx_parts) if ctx_parts else "No analysis data yet.")
    )

    # Build message history (last 6 turns)
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in chat_history[-6:]
    ]
    messages.append({"role": "user", "content": user_message})

    return await chat_complete(
        system=system,
        messages=messages,
        max_tokens=600,
        temperature=0.5,
    )
@tool
async def get_latest_analysis_tool(user_id: str) -> str:
    """
    Get the user's latest CV analysis, job matches, missing skills, and roadmap.
    Use this when the user asks about their CV, job matches, skill gaps, roadmap, or previous analysis.
    """
    analysis = await get_latest_analysis(user_id)
    return json.dumps(analysis or {}, ensure_ascii=False)


@tool
async def search_learning_resources_tool(query: str) -> str:
    """
    Search learning resources using RAG.
    Use this when the user asks about learning, courses, resources, tutorials, study plans, or missing skills.
    """
    resources = await search_learning_resources(query, top_k=3)
    return json.dumps(resources or [], ensure_ascii=False)