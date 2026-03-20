"""
NAYAM (नयम्) — Agent Router (Phase 2).

Intent-based routing that selects the best agent for a user query.
Uses keyword scoring as the initial classifier; the LLM-based
classifier will be plugged in during the integration phase.
"""

import logging
from typing import Dict, List, Optional, Tuple

from app.agents.base import BaseAgent
from app.agents.policy import PolicyAgent
from app.agents.citizen import CitizenAgent
from app.agents.operations import OperationsAgent

logger = logging.getLogger(__name__)

# ── Keyword-based intent signals ─────────────────────────────────
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "PolicyAgent": [
        "policy", "scheme", "regulation", "law", "act", "rule",
        "guideline", "eligibility", "subsidy", "budget", "ordinance",
        "notification", "circular", "government order", "GO",
        "compliance", "procedure", "protocol",
    ],
    "CitizenAgent": [
        "citizen", "complaint", "issue", "grievance", "ward",
        "water supply", "sanitation", "electricity", "road",
        "garbage", "pothole", "status", "track", "resident",
        "public", "service delivery", "feedback",
    ],
    "OperationsAgent": [
        "department", "staff", "resource", "assign", "allocate",
        "workload", "schedule", "transfer", "deploy", "operations",
        "efficiency", "workflow", "task", "capacity", "performance",
        "KPI", "metric", "dashboard",
    ],
}


class AgentRouter:
    """
    Routes user queries to the most appropriate specialised agent.

    Uses a keyword scoring approach with fallback to a default agent.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {
            "PolicyAgent": PolicyAgent(),
            "CitizenAgent": CitizenAgent(),
            "OperationsAgent": OperationsAgent(),
        }
        self._default_agent_name = "CitizenAgent"

    @property
    def available_agents(self) -> List[str]:
        """List of registered agent names."""
        return list(self._agents.keys())

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Retrieve a specific agent by name.

        Args:
            name: Agent identifier.

        Returns:
            BaseAgent instance or None.
        """
        return self._agents.get(name)

    def route(self, query: str) -> Tuple[BaseAgent, str, float]:
        """
        Determine the best agent for a given query.

        Args:
            query: The user's natural-language query.

        Returns:
            Tuple of (selected agent, intent label, confidence score).
        """
        scores = self._score_intents(query)

        if not scores or scores[0][1] == 0:
            # No signal — fall back to default
            logger.info("No intent signal detected, defaulting to %s", self._default_agent_name)
            agent = self._agents[self._default_agent_name]
            return agent, self._default_agent_name, 0.5

        best_name, best_score = scores[0]
        second_score = scores[1][1] if len(scores) > 1 else 0

        # Confidence = margin between top-2 normalised by total
        total = sum(s for _, s in scores)
        confidence = (best_score / total) if total > 0 else 0.5

        agent = self._agents[best_name]
        logger.info(
            "Routed query to %s (score=%d, confidence=%.2f)",
            best_name, best_score, confidence,
        )
        return agent, best_name, round(confidence, 3)

    def _score_intents(self, query: str) -> List[Tuple[str, int]]:
        """
        Score each agent based on keyword overlap with the query.

        Returns:
            List of (agent_name, score) sorted descending by score.
        """
        query_lower = query.lower()
        scores: List[Tuple[str, int]] = []

        for agent_name, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in query_lower)
            scores.append((agent_name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an additional agent at runtime.

        Args:
            agent: BaseAgent instance to register.
        """
        self._agents[agent.name] = agent
        logger.info("Registered agent: %s", agent.name)

    def __repr__(self) -> str:
        return f"<AgentRouter agents={list(self._agents.keys())}>"
