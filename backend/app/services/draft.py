"""
NAYAM (नयम्) — Draft Generation Service.

LLM-powered content generation with template prompts for
speeches, official responses, press releases, etc.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.draft import Draft, DraftType, DraftStatus
from app.repositories.draft import DraftRepository
from app.schemas.draft import (
    DraftGenerateRequest,
    DraftUpdateRequest,
    DraftResponse,
    DraftListResponse,
)

logger = logging.getLogger(__name__)

from app.compliance.audit_writer import write_audit
from app.observability.models import AuditAction

# ── Template System Prompts ──────────────────────────────────────────

DRAFT_SYSTEM_PROMPTS: dict[str, str] = {
    "Speech": (
        "You are a professional speechwriter for a senior public administrator in India. "
        "Write a compelling, well-structured speech in a {tone} tone for {audience}. "
        "The speech should be 3-5 minutes when read aloud (~500-800 words). "
        "Include a strong opening, clear talking points, and a memorable closing. "
        "Use clear, accessible language appropriate for government communication."
    ),
    "Official Response": (
        "You are a government communications officer drafting an official response. "
        "Write in a {tone} tone addressed to {audience}. "
        "The response should be clear, authoritative, and action-oriented. "
        "Include reference numbers where appropriate, specific commitments, "
        "and expected timelines. Follow Indian government communication standards."
    ),
    "Press Release": (
        "You are a government PR officer drafting a press release. "
        "Write in standard press release format with headline, dateline, lead paragraph, "
        "body quotes, and boilerplate. Tone: {tone}. Target media: {audience}. "
        "Follow Indian government press release conventions."
    ),
    "Policy Brief": (
        "You are a policy analyst writing a concise policy brief for {audience}. "
        "Structure: Executive Summary, Background, Key Findings, Policy Options, "
        "Recommendation. Tone: {tone}. Keep it to 1-2 pages (~600-1000 words)."
    ),
    "Meeting Agenda": (
        "You are an administrative assistant preparing a meeting agenda. "
        "Format with numbered items, time allocations, responsible persons, "
        "and expected outcomes. Tone: {tone}. Participants: {audience}."
    ),
    "Public Notice": (
        "You are a municipal official drafting a public notice. "
        "Write in clear, accessible language for {audience}. "
        "Include effective date, applicable rules, compliance requirements, "
        "and contact information. Tone: {tone}. Follow Indian gazette format."
    ),
    "Formal Letter": (
        "You are drafting a formal government letter in Indian administrative style. "
        "Include proper salutation, reference line, subject, body paragraphs, "
        "and formal closing. Tone: {tone}. Addressed to: {audience}."
    ),
    "RTI Response": (
        "You are a Public Information Officer drafting a response under the "
        "Right to Information Act, 2005. Address the query transparently, "
        "cite relevant sections, and provide the requested information or "
        "reason for exemption. Tone: {tone}. Applicant: {audience}."
    ),
    "Government Circular": (
        "You are drafting an internal government circular for {audience}. "
        "Include circular number, date, subject, detailed instructions, "
        "compliance deadline, and issuing authority. Tone: {tone}."
    ),
}


class DraftService:
    """Service layer for AI draft generation and management."""

    def __init__(self, db: Session) -> None:
        self.repo = DraftRepository(db)
        self._settings = get_settings()
        self._db = db

    # ── LLM Generation ───────────────────────────────────────────

    def _generate_with_llm(
        self,
        draft_type: str,
        topic: str,
        tone: str,
        audience: str,
        additional_context: str,
    ) -> str:
        """Generate draft content using Groq LLM."""
        system_template = DRAFT_SYSTEM_PROMPTS.get(draft_type, DRAFT_SYSTEM_PROMPTS["Speech"])
        system_prompt = system_template.format(tone=tone, audience=audience)

        user_prompt = f"Topic / Subject: {topic}"
        if additional_context:
            user_prompt += f"\n\nAdditional context and instructions:\n{additional_context}"

        try:
            from groq import Groq

            api_key = getattr(self._settings, "GROQ_API_KEY", None)
            if not api_key:
                logger.warning("No GROQ_API_KEY — using template fallback")
                return self._fallback_generate(draft_type, topic, tone, audience)

            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response.choices[0].message.content or ""
            logger.info("LLM generated %d chars for %s draft", len(content), draft_type)
            return content.strip()

        except Exception as e:
            logger.error("LLM draft generation failed: %s — using fallback", e)
            return self._fallback_generate(draft_type, topic, tone, audience)

    def _fallback_generate(self, draft_type: str, topic: str, tone: str, audience: str) -> str:
        """Template-based fallback when LLM is unavailable."""
        templates = {
            "Speech": (
                f"# {topic}\n\n"
                f"Respected dignitaries, officials, and citizens,\n\n"
                f"I am honored to address you today on the subject of {topic}.\n\n"
                f"[Opening remarks setting the context]\n\n"
                f"## Key Points\n\n"
                f"1. [First key point]\n2. [Second key point]\n3. [Third key point]\n\n"
                f"## Our Commitment\n\n"
                f"[Action items and commitments]\n\n"
                f"## Conclusion\n\n"
                f"Together, we shall work towards the betterment of our community. "
                f"Thank you.\n\n"
                f"---\n*Tone: {tone} | Audience: {audience}*"
            ),
            "Official Response": (
                f"# Official Response\n\n"
                f"**Subject:** {topic}\n"
                f"**Reference:** [Ref. No.]\n"
                f"**Date:** [Current Date]\n\n"
                f"Dear [Recipient],\n\n"
                f"With reference to your communication regarding {topic}, "
                f"this is to inform you that [response].\n\n"
                f"[Detailed response paragraphs]\n\n"
                f"Yours faithfully,\n[Name & Designation]"
            ),
        }
        return templates.get(draft_type, templates["Speech"])

    # ── Public API ───────────────────────────────────────────────

    def generate_draft(self, payload: DraftGenerateRequest, user_id: Optional[UUID] = None) -> Draft:
        """Generate a new draft using AI."""
        content = self._generate_with_llm(
            draft_type=payload.draft_type.value,
            topic=payload.topic,
            tone=payload.tone,
            audience=payload.audience,
            additional_context=payload.additional_context or "",
        )

        # Create title from topic
        title = f"{payload.draft_type.value}: {payload.topic[:80]}"

        word_count = len(content.split())

        draft = Draft(
            title=title,
            draft_type=payload.draft_type,
            status=DraftStatus.DRAFT,
            content=content,
            prompt_context=payload.topic,
            tone=payload.tone,
            audience=payload.audience,
            department=payload.department or "",
            version=1,
            extra_metadata={"word_count": word_count, "ai_generated": True},
            created_by=user_id,
        )
        created = self.repo.create(draft)
        write_audit(
            self._db,
            action=AuditAction.CREATE,
            resource_type="draft",
            resource_id=str(created.id),
            description=f"AI draft generated: '{title}' ({payload.draft_type.value})",
            user_id=user_id,
            metadata={"ai_generated": True, "word_count": word_count},
        )
        return created

    def list_drafts(
        self,
        skip: int = 0,
        limit: int = 50,
        draft_type: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
    ) -> DraftListResponse:
        type_enum = DraftType(draft_type) if draft_type else None
        status_enum = DraftStatus(status) if status else None
        drafts, total = self.repo.get_all(
            skip=skip,
            limit=limit,
            draft_type=type_enum,
            status=status_enum,
            department=department,
        )
        return DraftListResponse(
            total=total,
            drafts=[DraftResponse.model_validate(d) for d in drafts],
        )

    def get_draft(self, draft_id: UUID) -> Draft:
        draft = self.repo.get_by_id(draft_id)
        if not draft:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        return draft

    def update_draft(self, draft_id: UUID, payload: DraftUpdateRequest) -> Draft:
        draft = self.get_draft(draft_id)
        updates = payload.model_dump(exclude_unset=True)

        if "content" in updates:
            draft.version += 1
            meta = draft.extra_metadata or {}
            meta["word_count"] = len(updates["content"].split())
            draft.extra_metadata = meta

        for field, value in updates.items():
            setattr(draft, field, value)

        updated = self.repo.update(draft)
        if updates.get("status") == "published":
            write_audit(
                self._db,
                action=AuditAction.UPDATE,
                resource_type="draft",
                resource_id=str(draft_id),
                description=f"Draft published: '{draft.title}' (v{draft.version})",
            )
        return updated

    def delete_draft(self, draft_id: UUID) -> None:
        draft = self.get_draft(draft_id)
        self.repo.delete(draft)
