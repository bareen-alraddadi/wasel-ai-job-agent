"""
Wasel — LangGraph Orchestrator Agent

This file replaces the old sequential pipeline orchestrator with a real LangGraph
StateGraph. LangGraph keeps the workflow state and routes the request based on
whether the user provided a job description or wants RAG-based job discovery.
"""
import logging
from typing import Dict, List, Optional, TypedDict, Any

from langgraph.graph import StateGraph, START, END

from app.agents.resume_agent import ResumeAgent
from app.agents.job_agent import JobAgent
from app.agents.gap_agent import GapAgent
from app.agents.chat_agent import ChatAgent
from app.agents.cover_letter_agent import CoverLetterAgent
from app.memory.manager import supabase_memory, session_memory

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """
    Shared LangGraph state.

    Every node reads from and writes to this dictionary. This is what makes the
    workflow an agentic graph instead of a simple hardcoded pipeline.
    """
    user_id: str
    session_id: str
    file_bytes: bytes
    filename: str
    job_description: Optional[str]
    mode: str
    target_role: Optional[str]
    career_goal: Optional[str]

    resume_analysis: Dict[str, Any]
    job_matches: List[Dict[str, Any]]
    roadmap: Dict[str, Any]
    cover_letter: Optional[str]
    error: str


class OrchestratorAgent:
    """
    Main agent orchestrator.

    LangGraph is used here to:
    1. Maintain shared state between agents.
    2. Route conditionally between JD analysis and RAG job discovery.
    3. Keep the workflow modular and easier to explain in the presentation.
    """

    def __init__(self):
        self.resume_agent = ResumeAgent()
        self.job_agent = JobAgent()
        self.gap_agent = GapAgent()
        self.chat_agent = ChatAgent()
        self.cover_letter_agent = CoverLetterAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build and compile the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Each node wraps one specialized agent.
        workflow.add_node("resume_node", self._resume_node)
        workflow.add_node("job_description_node", self._job_description_node)
        workflow.add_node("cover_letter_node", self._cover_letter_node)
        workflow.add_node("rag_job_search_node", self._rag_job_search_node)
        workflow.add_node("gap_node", self._gap_node)

        workflow.add_edge(START, "resume_node")

        # Conditional routing: this is the key LangGraph/agentic part.
        workflow.add_conditional_edges(
            "resume_node",
            self._route_after_resume,
            {
                "jd": "job_description_node",
                "rag": "rag_job_search_node",
                "error": END,
            },
        )

        workflow.add_edge("job_description_node", "cover_letter_node")
        workflow.add_edge("cover_letter_node", "gap_node")
        workflow.add_edge("rag_job_search_node", "gap_node")
        workflow.add_edge("gap_node", END)

        return workflow.compile()

    async def _resume_node(self, state: AgentState) -> Dict[str, Any]:
        """LangGraph node 1: parse and score the uploaded CV."""
        if not state.get("file_bytes") or not state.get("filename"):
            return {"error": "CV file is required for analysis"}

        resume_analysis = await self.resume_agent.run(
            state["file_bytes"],
            state["filename"],
        )
        if "error" in resume_analysis:
            return {"error": resume_analysis["error"]}

        logger.info("[LangGraph] Resume node completed")
        return {"resume_analysis": resume_analysis}

    def _route_after_resume(self, state: AgentState) -> str:
        """
        Decide which job-analysis path to use.

        jd  = user provided a specific job description.
        rag = no JD, so the agent searches jobs using the RAG pipeline.
        """
        if state.get("error"):
            return "error"
        if state.get("job_description") and state["job_description"].strip():
            return "jd"
        return "rag"

    async def _job_description_node(self, state: AgentState) -> Dict[str, Any]:
        """LangGraph node 2A: analyze the user's provided job description."""
        job_matches = await self.job_agent.run(
            resume_analysis=state["resume_analysis"],
            job_description=state.get("job_description"),
            top_k=3,
        )
        logger.info("[LangGraph] JD job matching node completed")
        return {"job_matches": job_matches}

    async def _cover_letter_node(self, state: AgentState) -> Dict[str, Any]:
        """LangGraph node 2A.1: Generate a cover letter for the JD."""
        if not state.get("job_description"):
            return {"cover_letter": None}
            
        profile = state.get("resume_analysis", {}).get("profile", {})
        cover_letter = await self.cover_letter_agent.generate(
            profile=profile,
            job_description=state["job_description"]
        )
        logger.info("[LangGraph] Cover Letter node completed")
        return {"cover_letter": cover_letter}

    async def _rag_job_search_node(self, state: AgentState) -> Dict[str, Any]:
        """LangGraph node 2B: use RAG to retrieve relevant jobs from Qdrant."""
        job_matches = await self.job_agent.run(
            resume_analysis=state["resume_analysis"],
            job_description=None,
            top_k=3,
        )
        logger.info("[LangGraph] RAG job search node completed")
        return {"job_matches": job_matches}

    async def _gap_node(self, state: AgentState) -> Dict[str, Any]:
        """LangGraph node 3: identify gaps and build the learning roadmap."""
        job_matches = state.get("job_matches", [])
        if not job_matches:
            return {"error": "No job matches to build roadmap from"}

        roadmap = await self.gap_agent.run(
            resume_analysis=state["resume_analysis"],
            job_matches=job_matches,
        )
        logger.info("[LangGraph] Gap node completed")
        return {"roadmap": roadmap}

    async def analyze(
        self,
        user_id: str,
        session_id: str,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        job_description: Optional[str] = None,
        mode: str = "cv_only",
        target_role: Optional[str] = None,
        career_goal: Optional[str] = None,
    ) -> Dict:
        """
        Run the complete LangGraph workflow and persist the final result.
        """
        logger.info(f"[LangGraph Orchestrator] Starting analysis. Mode: {mode}")

        initial_state: AgentState = {
            "user_id": user_id,
            "session_id": session_id,
            "file_bytes": file_bytes or b"",
            "filename": filename or "",
            "job_description": job_description,
            "mode": mode,
            "target_role": target_role,
            "career_goal": career_goal,
        }

        final_state = await self.graph.ainvoke(initial_state)

        if final_state.get("error"):
            return {"error": final_state["error"]}

        result = {
            "user_id": user_id,
            "session_id": session_id,
            "mode": mode,
            "resume_analysis": final_state.get("resume_analysis", {}),
            "job_matches": final_state.get("job_matches", []),
            "roadmap": final_state.get("roadmap", {}),
            "cover_letter": final_state.get("cover_letter"),
        }

        # Supabase is used here for persistent storage of the final analysis.
        analysis_id = await supabase_memory.save_analysis(user_id, session_id, result)
        result["analysis_id"] = analysis_id

        # Session memory keeps the latest analysis available for follow-up chat.
        session_memory.set_analysis(session_id, result)

        logger.info(f"[LangGraph Orchestrator] Analysis saved: {analysis_id}")
        return result

    async def chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
        analysis_id: Optional[str] = None,
    ) -> Dict:
        """Route follow-up questions to the Chat Agent with saved context."""
        ctx = session_memory.get_context(session_id)
        if not ctx.get("analysis_result"):
            persisted = await supabase_memory.get_latest_analysis(user_id)
            if persisted:
                session_memory.set_analysis(session_id, persisted)

        return await self.chat_agent.run(
            user_id=user_id,
            session_id=session_id,
            user_message=message,
            analysis_id=analysis_id,
        )


orchestrator = OrchestratorAgent()
