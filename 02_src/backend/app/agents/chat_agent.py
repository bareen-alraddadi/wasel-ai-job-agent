"""
Wasel — Agent 4: Tool-Calling Chat Agent
"""

import logging
from typing import Dict, List

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.memory.manager import supabase_memory, session_memory
from app.tools.chat_tools import (
    get_latest_analysis,
    get_chat_history,
    get_latest_analysis_tool,
    search_learning_resources_tool,
)

logger = logging.getLogger(__name__)


class ChatAgent:
    async def run(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        analysis_id: str = None,
    ) -> Dict:
        logger.info(f"[ChatAgent] User {user_id}: '{user_message[:60]}...'")

        session_ctx = session_memory.get_context(session_id)

        if not session_ctx.get("analysis_result"):
            persisted = await get_latest_analysis(user_id)
            if persisted:
                session_ctx["analysis_result"] = persisted

        history = session_ctx.get("messages", [])
        if not history:
            history = await get_chat_history(session_id, limit=10)

        tools = [
            get_latest_analysis_tool,
            search_learning_resources_tool,
        ]

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                (
                    (
                        "system",
    """You are Wasel, an AI career coach specialized in Saudi tech jobs.

        ## User Context:
        - User ID: {user_id}
        - Always personalize responses using their CV/analysis data when available.

        ## Your Scope:
        Handle ONLY: CV analysis, job matching, skill gaps, learning paths, 
        interview prep, Saudi tech market, and career planning.

        ## Tool Usage Rules (STRICT):
        - ALWAYS call get_latest_analysis_tool first if the user asks about:
        their CV, matches, skills, gaps, roadmap, or "previous results"
        - If tool returns empty: tell the user to upload their CV first
        - If tool fails: apologize briefly and answer from conversation context

        ## Response Style:
        - Concise and actionable — no long paragraphs
        - Use bullet points for lists of skills/steps
        - Arabic or English based on user's message language
        - Never give generic advice — always tie it to their specific data
"""
                    )
                )
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        lc_history = []
        for msg in history[-6:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))

        agent_result = await agent_executor.ainvoke({
            "input": user_message,
            "user_id": user_id,
            "chat_history": lc_history,
        })

        response_text = agent_result.get("output", "")

        suggested_actions = _suggest_actions(user_message, session_ctx)

        session_memory.add_message(session_id, "user", user_message)
        session_memory.add_message(session_id, "assistant", response_text)

        await supabase_memory.save_message(session_id, user_id, "user", user_message)
        await supabase_memory.save_message(session_id, user_id, "assistant", response_text)

        return {
            "message": response_text,
            "sources": ["Tool calling: memory + learning resources"],
            "suggested_actions": suggested_actions,
        }


def _suggest_actions(message: str, context: Dict) -> List[str]:
    msg_lower = message.lower()
    suggestions = []

    if "gap" in msg_lower or "missing" in msg_lower:
        suggestions.append("View your skill gap roadmap")
    if "interview" in msg_lower:
        suggestions.append("Practice interview questions")
    if "resume" in msg_lower or "cv" in msg_lower:
        suggestions.append("Upload a new CV version")
    if "job" in msg_lower or "role" in msg_lower:
        suggestions.append("Explore more job matches")
    if not suggestions:
        suggestions = ["View full analysis", "Explore learning resources"]

    return suggestions[:3]