"""
NAYAM (नयम्) — Citizen Agent (Phase 2).

Handles queries about citizen records, complaints, issue tracking,
and public communication. Powered by Groq LLM.
"""

import logging

from app.agents.base import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class CitizenAgent(BaseAgent):
    """
    Specialised agent for citizen-related queries.

    Handles: citizen lookup, complaint status, issue summaries,
    ward-level analytics, and citizen communication.
    """

    @property
    def name(self) -> str:
        return "CitizenAgent"

    @property
    def description(self) -> str:
        return (
            "Specialises in citizen records, complaint tracking, issue management, "
            "and ward-level analytics for public administrators."
        )

    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Process a citizen-related query via Groq LLM.

        Falls back to a helpful stub if the LLM is unavailable.
        """
        logger.info("CitizenAgent executing for session %s", context.session_id)

        # Try LLM call
        llm_response = self._call_llm(context)

        if llm_response:
            message = llm_response
            confidence = 0.88
        else:
            rag_summary = ""
            if context.rag_context:
                rag_summary = (
                    " Retrieved citizen data context: "
                    + "; ".join(context.rag_context[:3])
                )
            message = (
                f"Processing citizen query: '{context.query}'.{rag_summary} "
                "Note: LLM integration requires a Groq API key. "
                "Please set GROQ_API_KEY in .env to enable AI-powered responses."
            )
            confidence = 0.50

        suggested_actions = []
        action_keywords = ["send", "notify", "escalate", "assign", "update status"]
        if any(kw in context.query.lower() for kw in action_keywords):
            suggested_actions.append({
                "action_type": "citizen_action",
                "description": f"Citizen-related action for: {context.query[:100]}",
                "payload": {"query": context.query, "agent": self.name},
            })

        return AgentResponse(
            agent_name=self.name,
            message=message,
            confidence=confidence,
            suggested_actions=suggested_actions,
            sources=context.rag_sources,
        )

    def _system_prompt(self) -> str:
        return (
            "You are CitizenAgent, a specialised AI within the NAYAM governance platform "
            "used by Indian municipal administrators. "
            "You handle citizen data, issue tracking, and complaint management.\n"
            "When answering:\n"
            "- Provide ward-level summaries, issue status updates, and actionable insights\n"
            "- Reference specific issue categories (Water Supply, Roads, Sanitation, etc.)\n"
            "- Suggest prioritisation based on severity and citizen impact\n"
            "- If the query requires a mutation (sending notifications, escalating issues), "
            "structure it as a suggested action for human approval\n"
            "- Keep answers practical and action-oriented\n"
            "- If document context is provided, use it to ground your answers"
        )
