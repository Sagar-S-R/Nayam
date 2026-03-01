"""
NAYAM (नयम्) — Policy Agent (Phase 2).

Handles queries about government policies, schemes, regulations,
and procedural guidance. Powered by Groq LLM.
"""

import logging

from app.agents.base import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class PolicyAgent(BaseAgent):
    """
    Specialised agent for policy-related queries.

    Handles: scheme eligibility, government orders, regulatory queries,
    procedural guidance, and policy comparison.
    """

    @property
    def name(self) -> str:
        return "PolicyAgent"

    @property
    def description(self) -> str:
        return (
            "Specialises in government policies, schemes, regulations, "
            "and procedural guidance for public administrators."
        )

    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Process a policy-related query via Groq LLM.

        Falls back to a helpful stub if the LLM is unavailable.
        """
        logger.info("PolicyAgent executing for session %s", context.session_id)

        # Try LLM call
        llm_response = self._call_llm(context)

        if llm_response:
            message = llm_response
            confidence = 0.90
        else:
            # Fallback when LLM key not configured
            rag_summary = ""
            if context.rag_context:
                rag_summary = (
                    " Based on retrieved policy documents: "
                    + "; ".join(context.rag_context[:3])
                )
            message = (
                f"Analysing your policy query: '{context.query}'.{rag_summary} "
                "Note: LLM integration requires a Groq API key. "
                "Please set GROQ_API_KEY in .env to enable AI-powered responses."
            )
            confidence = 0.50

        # If the query implies a state-change, suggest an action
        suggested_actions = []
        action_keywords = ["update", "change", "modify", "issue order", "notify"]
        if any(kw in context.query.lower() for kw in action_keywords):
            suggested_actions.append({
                "action_type": "policy_recommendation",
                "description": f"Policy action recommended based on query: {context.query[:100]}",
                "payload": {"query": context.query, "agent": self.name},
            })

        return AgentResponse(
            agent_name=self.name,
            message=message,
            confidence=confidence,
            suggested_actions=suggested_actions,
        )

    def _system_prompt(self) -> str:
        return (
            "You are PolicyAgent, a specialised AI within the NAYAM governance platform "
            "used by Indian municipal administrators. "
            "You have deep knowledge of government policies, schemes, regulations, "
            "and administrative procedures. When answering:\n"
            "- Cite specific policy names, section numbers, and eligibility criteria where possible\n"
            "- Reference relevant government schemes (PM-KISAN, MGNREGA, Swachh Bharat, etc.)\n"
            "- Provide actionable guidance with clear steps\n"
            "- If the query requires a state change (updating a policy, issuing a notification), "
            "structure it as a suggested action for human approval\n"
            "- Keep answers concise but thorough, aim for 2-4 paragraphs\n"
            "- If document context is provided, use it to ground your answers"
        )
