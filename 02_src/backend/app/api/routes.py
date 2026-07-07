"""
Wasel — API Routes
"""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.agents.orchestrator import orchestrator
from app.memory.manager import supabase_memory
from app.models.schemas import ChatRequest, ChatResponse, AnalyzeResponse
from app.agents.cv_improvement_agent import CVImprovementAgent

logger = logging.getLogger(__name__)

router = APIRouter()

_cv_improvement_agent = CVImprovementAgent()

# ── Health ──────────────────────────────────────────────────

@router.get("/ping")
async def ping():
    return {"status": "ok"}

# ── Analysis ────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(
    user_id: str = Form(...),
    session_id: str = Form(None),
    job_description: Optional[str] = Form(None),
    cv_file: UploadFile = File(...),
    target_role: Optional[str] = Form(None),
    career_goal: Optional[str] = Form(None),
):
    """
    Main analysis endpoint.
    - Scenario A: cv_file + job_description → full match analysis
    - Scenario B: cv_file only → top 3 job matches via RAG
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    # Validate file type
    filename = cv_file.filename or "resume.pdf"
    if not filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(400, "Only PDF and DOCX files are supported")

    file_bytes = await cv_file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(400, "File too large. Maximum size is 10MB")

    mode = "cv_and_jd" if (job_description and job_description.strip()) else "cv_only"

    try:
        # Check guest mode limit (max 2 analyses)
        user = await supabase_memory.get_user(user_id)
        if not user or user.get("is_guest", True):
            analyses_count = await supabase_memory.get_analyses_count(user_id)
            if analyses_count >= 2:
                raise HTTPException(
                    status_code=403,
                    detail="Guest limit reached. You can only analyze 2 CVs as a guest. Please sign up to analyze unlimited CVs and save your progress."
                )

        # Upsert user record
        await supabase_memory.upsert_user(
            user_id, 
            is_guest=(user.get("is_guest", True) if user else True)
        )

        # Upload CV to Supabase Storage (async, non-blocking for analysis)
        cv_url = await supabase_memory.upload_cv(user_id, file_bytes, filename)

        # Run full pipeline via orchestrator
        result = await orchestrator.analyze(
            user_id=user_id,
            session_id=session_id,
            file_bytes=file_bytes,
            filename=filename,
            job_description=job_description,
            mode=mode,
            target_role=target_role,
            career_goal=career_goal,
        )

        if "error" in result:
            raise HTTPException(422, result["error"])

        # Attach cv_path to result so frontend can request fresh signed URLs later
        result["cv_path"] = cv_url  # cv_url is now the storage path (Option B)

        return {
            "success": True,
            "analysis_id": result.get("analysis_id", ""),
            "session_id": session_id,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Analysis failed for user {user_id}: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


# ── CV Improvement Tips ──────────────────────────────────────

@router.post("/cv-tips")
async def get_cv_tips(request: dict):
    """
    Generate section-by-section CV improvement tips for a specific job.
    Accepts: user_id, job_title, job_company, required_skills, missing_skills, match_score
    """
    try:
        # Get the user's profile for context
        user_id = request.get("user_id", "")
        analysis = await supabase_memory.get_latest_analysis(user_id)
        profile = {}
        if analysis:
            profile = analysis.get("resume_analysis", {}).get("profile", {})

        tips = await _cv_improvement_agent.generate(
            profile=profile,
            job_title=request.get("job_title", ""),
            job_company=request.get("job_company", ""),
            required_skills=request.get("required_skills", []),
            missing_skills=request.get("missing_skills", []),
            match_score=request.get("match_score", 0),
        )
        return {"tips": tips}
    except Exception as e:
        logger.exception(f"CV tips generation failed: {e}")
        raise HTTPException(500, f"Failed to generate tips: {str(e)}")


# ── Chat ────────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Conversational chat endpoint.
    Routes to Chat Agent with full session and analysis context.
    """
    try:
        response = await orchestrator.chat(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            analysis_id=request.analysis_id,
        )
        return ChatResponse(**response)
    except Exception as e:
        logger.exception(f"Chat error: {e}")
        raise HTTPException(500, f"Chat failed: {str(e)}")


# ── User / Analysis History ──────────────────────────────────

@router.get("/users/{user_id}/profile")
async def get_profile(user_id: str):
    """Retrieve stored user profile."""
    profile = await supabase_memory.get_user(user_id)
    if not profile:
        raise HTTPException(404, "User not found")
    return profile


@router.get("/users/{user_id}/analysis/latest")
async def get_latest_analysis(user_id: str):
    """Retrieve most recent analysis for a user."""
    analysis = await supabase_memory.get_latest_analysis(user_id)
    if not analysis:
        raise HTTPException(404, "No analysis found for this user")
    return analysis


@router.get("/users/{user_id}/chat/{session_id}")
async def get_chat_history(user_id: str, session_id: str, limit: int = 20):
    """Retrieve chat history for a session."""
    history = await supabase_memory.get_chat_history(session_id, limit=limit)
    return {"messages": history, "session_id": session_id}


@router.get("/cv-url")
async def get_cv_signed_url(path: str):
    """
    Generate a fresh 1-hour signed URL for a CV storage path.
    Call this whenever you need to display or download a CV,
    instead of caching the URL (which expires after 1 hour).
    """
    if not path:
        raise HTTPException(400, "path is required")
    url = await supabase_memory.get_cv_signed_url(path)
    if not url:
        raise HTTPException(404, "CV not found or storage unavailable")
    return {"signed_url": url, "expires_in": 3600}
