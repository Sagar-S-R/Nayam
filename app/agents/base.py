"""
NAYAM (नयम्) — Agent Base Framework (Phase 2).

Defines the BaseAgent abstract class and the AgentContext dataclass
that flows through the agent execution pipeline.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    Immutable context object passed into every agent execution.

    Attributes:
        session_id: Conversation session UUID.
        user_id: Authenticated user UUID.
        query: The user's current query text.
        conversation_history: Prior messages in this session.
        rag_context: Retrieved document chunks from RAG pipeline.
        metadata: Arbitrary extra data agents may need.
    """

    session_id: UUID
    user_id: UUID
    query: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    rag_context: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """
    Structured response returned by every agent.

    Attributes:
        agent_name: Which agent produced this response.
        message: The natural-language response text.
        confidence: Agent's self-assessed confidence (0.0 – 1.0).
        suggested_actions: Actions the agent proposes (require HITL approval).
        metadata: Arbitrary extra data for downstream consumers.
    """

    agent_name: str
    message: str
    confidence: float = 1.0
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all NAYAM agents.

    Every specialized agent must implement:
      • ``name``  — unique identifier string
      • ``description`` — what the agent does (used by the router)
      • ``execute(context)`` — core logic
    """

    _groq_client = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the agent's capabilities."""
        ...

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute the agent's core logic.

        Args:
            context: AgentContext with query, history, and RAG data.

        Returns:
            AgentResponse with the agent's output.
        """
        ...

    # ── LLM Integration ──────────────────────────────────────────

    @classmethod
    def _get_groq_client(cls):
        """Lazy-initialised Groq client singleton."""
        if cls._groq_client is None:
            from app.core.config import get_settings
            settings = get_settings()
            if not settings.GROQ_API_KEY:
                return None
            try:
                from groq import Groq
                cls._groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as exc:
                logger.error("Failed to create Groq client: %s", exc)
                return None
        return cls._groq_client

    def _call_llm(self, context: AgentContext) -> Optional[str]:
        """
        Call Groq LLM with the built prompt messages.

        Returns the response text, or None if the LLM is unavailable.
        """
        client = self._get_groq_client()
        if client is None:
            return None

        from app.core.config import get_settings
        settings = get_settings()

        messages = self._build_prompt_messages(context)

        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq LLM call failed for %s: %s", self.name, exc)
            return None

    def _build_prompt_messages(self, context: AgentContext) -> List[Dict[str, str]]:
        """
        Helper to build a chat-style message list from context.

        Returns a list of {"role": ..., "content": ...} dicts suitable
        for an LLM chat completion call.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._system_prompt()},
        ]

        # Append conversation history
        for msg in context.conversation_history:
            messages.append(msg)

        # Append RAG context as a system-level injection
        if context.rag_context:
            rag_block = "\n\n---\n".join(context.rag_context)
            messages.append({
                "role": "system",
                "content": (
                    "The following documents were retrieved as relevant context. "
                    "Use them to inform your answer:\n\n" + rag_block
                ),
            })

        # Append the current user query
        messages.append({"role": "user", "content": context.query})
        return messages

    def _system_prompt(self) -> str:
        """
        Default system prompt.  Override in subclasses for specialization.
        """
        return (
            f"You are {self.name}, an AI agent in the NAYAM governance platform. "
            f"{self.description} "
            "Answer clearly, concisely, and cite data when available. "
            "If you recommend an action that changes system state, structure it as "
            "a suggested_action so it can go through approval."
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
