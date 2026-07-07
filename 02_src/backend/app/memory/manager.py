"""
Wasel — Supabase memory manager
Handles all persistent storage: users, analyses, chat history, CV files

Uses AsyncClient to avoid blocking FastAPI's event loop on every DB call.
"""
import json
import uuid
import logging
from typing import Optional, List, Dict
from datetime import datetime
from cachetools import TTLCache

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_async_client():
    """Create an async Supabase client."""
    from supabase._async.client import AsyncClient, create_client as _create
    return await _create(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class SupabaseMemory:
    """Long-term memory backed by Supabase PostgreSQL (fully async)."""

    def __init__(self):
        self.client = None

    async def connect(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                self.client = await _get_async_client()
                logger.info("✅ Supabase async client connected")
            except Exception as e:
                logger.error(f"❌ Supabase connection failed: {e}")
                self.client = None
        else:
            logger.warning("⚠️  Supabase not configured — memory will not persist")

    # ── User management ──────────────────────────────────────

    async def upsert_user(self, user_id: str, email: str = "", name: str = "", is_guest: bool = True) -> Dict:
        if not self.client:
            return {"user_id": user_id}
        data = {
            "user_id": user_id,
            "email": email or None,
            "name": name or None,
            "is_guest": is_guest,
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = await self.client.table("users").upsert(data).execute()
        return result.data[0] if result.data else data

    async def get_user(self, user_id: str) -> Optional[Dict]:
        if not self.client:
            return None
        result = await self.client.table("users").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    async def get_user_by_auth_id(self, auth_id: str) -> Optional[Dict]:
        if not self.client:
            return None
        result = await self.client.table("users").select("*").eq("auth_user_id", auth_id).execute()
        return result.data[0] if result.data else None

    async def get_analyses_count(self, user_id: str) -> int:
        if not self.client:
            return 0
        try:
            result = await self.client.table("analyses").select("analysis_id", count="exact").eq("user_id", user_id).execute()
            # result.count contains the exact count of rows matching the query
            return result.count if result.count is not None else len(result.data)
        except Exception as e:
            logger.error(f"Error getting analyses count for user {user_id}: {e}")
            return 0

    async def claim_account(self, guest_id: str, auth_id: str, email: str, name: str) -> Dict:
        if not self.client:
            return {"user_id": guest_id}
        data = {
            "auth_user_id": auth_id,
            "email": email,
            "name": name,
            "is_guest": False,
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = await self.client.table("users").update(data).eq("user_id", guest_id).execute()
        return result.data[0] if result.data else data


    # ── CV file storage ───────────────────────────────────────

    async def upload_cv(self, user_id: str, file_bytes: bytes, filename: str) -> str:
        """
        Upload CV to Supabase Storage.
        Returns the storage PATH (not a URL) — store this path, not the URL.
        Call get_cv_signed_url(path) whenever you need a fresh link.
        """
        if not self.client:
            return ""
        path = f"{user_id}/{uuid.uuid4()}_{filename}"
        await self.client.storage.from_("cvs").upload(path, file_bytes)
        return path  # ← store path, not URL

    async def get_cv_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Generate a fresh signed URL for a CV path.
        Call this every time you need to display or download the CV.
        Default expiry: 1 hour (3600 seconds).
        """
        if not self.client or not path:
            return ""
        try:
            signed = await self.client.storage.from_("cvs").create_signed_url(path, expires_in=expires_in)
            return signed.get("signedURL", "")
        except Exception as e:
            logger.warning(f"Failed to generate signed URL for path '{path}': {e}")
            return ""

    # ── Analysis storage ──────────────────────────────────────

    async def save_analysis(self, user_id: str, session_id: str, result: Dict) -> str:
        """Save full analysis result to Supabase."""
        analysis_id = str(uuid.uuid4())
        if not self.client:
            return analysis_id
        data = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "session_id": session_id,
            "mode": result.get("mode", "cv_only"),
            "target_role": result.get("target_role", ""),
            "career_goal": result.get("career_goal", ""),
            "resume_score": result.get("resume_analysis", {}).get("score", 0),
            "skills": json.dumps(result.get("resume_analysis", {}).get("profile", {}).get("skills", [])),
            "job_matches": json.dumps(result.get("job_matches", [])),
            "roadmap": json.dumps(result.get("roadmap", {})),
            "cover_letter": result.get("cover_letter"),
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.client.table("analyses").insert(data).execute()
        # Update latest analysis on user
        await self.client.table("users").update(
            {"latest_analysis_id": analysis_id}
        ).eq("user_id", user_id).execute()
        return analysis_id

    async def get_latest_analysis(self, user_id: str) -> Optional[Dict]:
        """Retrieve most recent analysis for a user."""
        if not self.client:
            return None
        result = (
            await self.client.table("analyses")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]

        # Parse JSON fields
        job_matches = json.loads(row.get("job_matches", "[]"))
        roadmap     = json.loads(row.get("roadmap", "{}"))
        skills      = json.loads(row.get("skills", "[]"))

        # Re-assemble the full AnalysisResult shape the frontend expects
        return {
            "analysis_id":    row.get("analysis_id", ""),
            "user_id":        row.get("user_id", user_id),
            "session_id":     row.get("session_id", ""),
            "mode":           row.get("mode", "cv_only"),
            "target_role":    row.get("target_role", ""),
            "career_goal":    row.get("career_goal", ""),
            "resume_analysis": {
                "score": row.get("resume_score", 0),
                "score_breakdown": {},
                "suggestions": [],
                "profile": {
                    "name":           "",
                    "email":          "",
                    "phone":          "",
                    "location":       "",
                    "summary":        "",
                    "skills":         skills,
                    "experience":     [],
                    "education":      [],
                    "certifications": [],
                    "languages":      [],
                    "raw_text":       "",
                },
            },
            "job_matches": job_matches,
            "roadmap":     roadmap,
            "cover_letter": row.get("cover_letter"),
            # Keep raw fields too for backwards compat
            "skills":      skills,
        }

    # ── Chat history ──────────────────────────────────────────

    async def save_message(self, session_id: str, user_id: str, role: str, content: str):
        if not self.client:
            return
        await self.client.table("chat_messages").insert({
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

    async def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        if not self.client:
            return []
        result = (
            await self.client.table("chat_messages")
            .select("role,content,created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return result.data or []


# ── Short-term session memory (in-process) ───────────────────

class SessionMemory:
    """
    In-process short-term memory for active sessions.

    Uses TTLCache to prevent unbounded RAM growth:
      - max 500 concurrent sessions in memory
      - sessions auto-evict after 2 hours of inactivity
    """

    def __init__(self, max_sessions: int = 500, ttl_seconds: int = 7200):
        self._store: TTLCache = TTLCache(maxsize=max_sessions, ttl=ttl_seconds)

    def get_session(self, session_id: str) -> Dict:
        if session_id not in self._store:
            self._store[session_id] = {
                "messages": [],
                "resume_profile": None,
                "active_job": None,
                "analysis_result": None,
                "created_at": datetime.utcnow().isoformat(),
            }
        return self._store[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)
        session["messages"].append({"role": role, "content": content})
        # Keep only last 10 messages
        if len(session["messages"]) > 10:
            session["messages"] = session["messages"][-10:]

    def set_analysis(self, session_id: str, result: Dict):
        session = self.get_session(session_id)
        session["analysis_result"] = result
        if result.get("resume_analysis"):
            session["resume_profile"] = result["resume_analysis"].get("profile")
        if result.get("job_matches"):
            session["active_job"] = result["job_matches"][0]

    def get_context(self, session_id: str) -> Dict:
        return self.get_session(session_id)

    def clear_session(self, session_id: str):
        self._store.pop(session_id, None)


# Singletons
supabase_memory = SupabaseMemory()
session_memory = SessionMemory()
