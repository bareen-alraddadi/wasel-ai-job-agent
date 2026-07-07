"""
Wasel — Pydantic data models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisMode(str, Enum):
    CV_AND_JD = "cv_and_jd"      # Scenario A
    CV_ONLY = "cv_only"           # Scenario B


# ─── Resume Models ───────────────────────────────────────────

class ResumeProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[str] = []
    languages: List[str] = []
    raw_text: str = ""


class ResumeAnalysis(BaseModel):
    profile: ResumeProfile
    score: float = Field(ge=0, le=100)
    score_breakdown: Dict[str, float] = {}
    suggestions: List[str] = []


# ─── Job Models ──────────────────────────────────────────────

class JobPosting(BaseModel):
    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_years: Optional[int] = None
    education_level: str = ""
    job_type: str = ""
    salary_range: str = ""
    apply_link: str = ""


class MatchResult(BaseModel):
    job: JobPosting
    match_score: float = Field(ge=0, le=100)
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    match_explanation: str = ""


# ─── Gap & Roadmap Models ────────────────────────────────────

class LearningResource(BaseModel):
    title: str
    provider: str = ""
    url: str = ""
    duration: str = ""
    level: str = ""
    skill: str = ""


class SkillGap(BaseModel):
    skill: str
    priority: str = "medium"       # high / medium / low
    description: str = ""
    resources: List[LearningResource] = []
    estimated_time: str = ""


class RoadmapMilestone(BaseModel):
    phase: str                     # "30 days" / "90 days" / "6 months"
    title: str
    goals: List[str] = []
    skills: List[str] = []


class CareerRoadmap(BaseModel):
    target_role: str
    total_gap_score: float = 0.0
    skill_gaps: List[SkillGap] = []
    milestones: List[RoadmapMilestone] = []
    interview_questions: List[str] = []
    summary: str = ""


# ─── Analysis Output ─────────────────────────────────────────

class FullAnalysisResult(BaseModel):
    user_id: str
    session_id: str
    mode: AnalysisMode
    resume_analysis: ResumeAnalysis
    job_matches: List[MatchResult] = []
    roadmap: Optional[CareerRoadmap] = None
    cover_letter: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Chat Models ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str                      # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    analysis_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    sources: List[str] = []
    suggested_actions: List[str] = []


# ─── API Request/Response ────────────────────────────────────

class AnalyzeRequest(BaseModel):
    user_id: str
    session_id: str
    job_description: Optional[str] = None   # None → Scenario B


class AnalyzeResponse(BaseModel):
    success: bool
    analysis_id: str
    result: FullAnalysisResult
    message: str = ""


class UserProfile(BaseModel):
    user_id: str
    email: str = ""
    name: str = ""
    created_at: Optional[datetime] = None
    latest_analysis_id: Optional[str] = None


class UserSignup(BaseModel):
    email: str
    password: str
    name: str
    guest_user_id: str  # The client's localStorage guest UUID to be claimed


class UserLogin(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

