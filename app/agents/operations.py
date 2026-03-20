"""
NAYAM (नयम्) — Operations Agent (Phase 2).

Handles queries about departmental operations, resource allocation,
task assignment, and administrative workflow. Powered by Groq LLM.
"""

import logging

from app.agents.base import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class OperationsAgent(BaseAgent):
    """
    Specialised agent for operations-related queries.

    Handles: departmental workload, resource allocation, task assignment,
    workflow status, and operational efficiency analysis.
    """

    @property
    def name(self) -> str:
        return "OperationsAgent"

    @property
    def description(self) -> str:
        return (
            "Specialises in departmental operations, resource allocation, "
            "task assignment, and administrative workflow management."
        )

    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Process an operations-related query via Groq LLM.

        Falls back to a helpful stub if the LLM is unavailable.
        """
        logger.info("OperationsAgent executing for session %s", context.session_id)

        # Try LLM call
        llm_response = self._call_llm(context)

        if llm_response:
            message = llm_response
            confidence = 0.87
        else:
            rag_summary = ""
            if context.rag_context:
                rag_summary = (
                    " Retrieved operational context: "
                    + "; ".join(context.rag_context[:3])
                )
            message = (
                f"Analysing operational query: '{context.query}'.{rag_summary} "
                "Note: LLM integration requires a Groq API key. "
                "Please set GROQ_API_KEY in .env to enable AI-powered responses."
            )
            confidence = 0.50

        suggested_actions = []
        action_keywords = [
            "assign", "allocate", "transfer", "schedule", "deploy",
            "reassign", "change department",
        ]
        if any(kw in context.query.lower() for kw in action_keywords):
            suggested_actions.append({
                "action_type": "operations_action",
                "description": f"Operational action for: {context.query[:100]}",
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
            "You are OperationsAgent, a specialised AI within the NAYAM governance platform "
            "used by Indian municipal administrators. "
            "You handle departmental operations, resource management, task assignment, "
            "and workflow optimisation.\n"
            "When answering:\n"
            "- Provide data-driven recommendations for resource allocation\n"
            "- Analyse departmental workloads and suggest optimisations\n"
            "- Reference KPIs, staffing metrics, and efficiency benchmarks\n"
            "- Structure any state-changing suggestions as actions for human approval\n"
            "- Keep answers practical with concrete next steps\n"
            "- If document context is provided, use it to ground your answers"
        )
