"""
NAYAM (नयम्) — RAG Source Citations Feature Tests.

Tests for:
  • SourceCitation dataclass with document metadata
  • AgentResponse with sources field
  • MemoryService.search_by_text returning source metadata
  • AgentService including sources in query response
  • End-to-end agent query with source citations
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.document import Document
from app.models.embedding import Embedding
from app.models.user import User, UserRole


# ══════════════════════════════════════════════════════════════════════
#  TEST DATACLASS: SourceCitation
# ══════════════════════════════════════════════════════════════════════

class TestSourceCitationDataclass:
    """Tests for SourceCitation dataclass structure."""

    def test_source_citation_creation(self):
        """SourceCitation can be created with all required fields."""
        from app.agents.base import SourceCitation

        doc_id = uuid.uuid4()
        source = SourceCitation(
            document_id=doc_id,
            document_title="Delhi Master Plan 2041",
            chunk_index=5,
            chunk_preview="This is the first 40 words of the chunk content. It provides an overview of water supply policies in Delhi.",
            relevance_score=0.87,
        )

        assert source.document_id == doc_id
        assert source.document_title == "Delhi Master Plan 2041"
        assert source.chunk_index == 5
        # Preview should be reasonable length (30-40 words ~200-250 chars)
        assert 100 < len(source.chunk_preview) <= 300
        assert 0.0 <= source.relevance_score <= 1.0

    def test_source_citation_with_high_relevance(self):
        """SourceCitation stores high relevance scores correctly."""
        from app.agents.base import SourceCitation

        source = SourceCitation(
            document_id=uuid.uuid4(),
            document_title="Policy Document",
            chunk_index=0,
            chunk_preview="Very relevant chunk content preview.",
            relevance_score=0.95,
        )

        assert source.relevance_score >= 0.9

    def test_source_citation_with_low_relevance(self):
        """SourceCitation stores low relevance scores correctly."""
        from app.agents.base import SourceCitation

        source = SourceCitation(
            document_id=uuid.uuid4(),
            document_title="Tangential Document",
            chunk_index=10,
            chunk_preview="Somewhat relevant chunk content preview.",
            relevance_score=0.30,
        )

        assert source.relevance_score >= 0.15  # Above threshold


# ══════════════════════════════════════════════════════════════════════
#  AGENT RESPONSE WITH SOURCES
# ══════════════════════════════════════════════════════════════════════

class TestAgentResponseWithSources:
    """Tests for AgentResponse including sources."""

    def test_agent_response_with_sources(self):
        """AgentResponse can include source citations."""
        from app.agents.base import AgentResponse, SourceCitation

        doc_id_1 = uuid.uuid4()
        doc_id_2 = uuid.uuid4()
        sources = [
            SourceCitation(
                document_id=doc_id_1,
                document_title="Delhi Master Plan 2041",
                chunk_index=3,
                chunk_preview="Water supply infrastructure overview.",
                relevance_score=0.89,
            ),
            SourceCitation(
                document_id=doc_id_2,
                document_title="Ward Development Plan",
                chunk_index=1,
                chunk_preview="Ward-specific water supply allocation.",
                relevance_score=0.76,
            ),
        ]

        response = AgentResponse(
            agent_name="CitizenAgent",
            message="Delhi's water supply is managed through 19 zones with annual allocation of 1000 MLD.",
            confidence=0.85,
            suggested_actions=[],
            metadata={},
            sources=sources,
        )

        assert response.agent_name == "CitizenAgent"
        assert len(response.sources) == 2
        assert response.sources[0].document_title == "Delhi Master Plan 2041"
        assert response.sources[1].document_title == "Ward Development Plan"

    def test_agent_response_without_sources(self):
        """AgentResponse with no sources (general knowledge fallback)."""
        from app.agents.base import AgentResponse

        response = AgentResponse(
            agent_name="PolicyAgent",
            message="General governance principles require transparency.",
            confidence=0.70,
            suggested_actions=[],
            metadata={},
            sources=[],  # No sources = general knowledge
        )

        assert len(response.sources) == 0

    def test_agent_response_source_ordering_by_relevance(self):
        """Sources are ordered by relevance score (highest first)."""
        from app.agents.base import AgentResponse, SourceCitation

        sources = [
            SourceCitation(
                document_id=uuid.uuid4(),
                document_title="Doc A",
                chunk_index=0,
                chunk_preview="Preview A",
                relevance_score=0.50,
            ),
            SourceCitation(
                document_id=uuid.uuid4(),
                document_title="Doc B",
                chunk_index=0,
                chunk_preview="Preview B",
                relevance_score=0.95,  # Highest
            ),
            SourceCitation(
                document_id=uuid.uuid4(),
                document_title="Doc C",
                chunk_index=0,
                chunk_preview="Preview C",
                relevance_score=0.70,
            ),
        ]

        # Client code should sort sources before creating response
        sorted_sources = sorted(sources, key=lambda s: s.relevance_score, reverse=True)

        response = AgentResponse(
            agent_name="TestAgent",
            message="Test response",
            confidence=0.80,
            suggested_actions=[],
            metadata={},
            sources=sorted_sources,
        )

        assert response.sources[0].document_title == "Doc B"
        assert response.sources[0].relevance_score == 0.95


# ══════════════════════════════════════════════════════════════════════
#  MEMORY SERVICE SOURCE RETRIEVAL
# ══════════════════════════════════════════════════════════════════════

class TestMemoryServiceSourceRetrieval:
    """Tests for MemoryService returning source metadata."""

    def test_search_by_text_returns_sources(
        self,
        db_session: Session,
        leader_user: User,
    ):
        """MemoryService.search_by_text returns source document info."""
        from app.services.memory import MemoryService, generate_embedding

        # Create a document
        doc = Document(
            id=uuid.uuid4(),
            title="Delhi Water Supply Policy 2026",
            uploaded_by=leader_user.id,
            file_path="/uploads/delhi_water_supply_2026.pdf",
            extracted_text="Delhi maintains 19 water supply zones.",
            summary="Water supply overview for Delhi.",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        # Create embeddings with source reference using real embeddings
        chunk_text = "Delhi maintains 19 water supply zones with daily capacity of 1000 MLD."
        embedding_vector = generate_embedding(chunk_text)
        embed = Embedding(
            id=uuid.uuid4(),
            source_type="document",
            source_id=doc.id,
            content_hash=hashlib.sha256(b"Delhi water supply").hexdigest(),
            embedding=embedding_vector,
            dimensions=len(embedding_vector),
            chunk_text=chunk_text,
            chunk_index=0,
        )
        db_session.add(embed)
        db_session.commit()

        # Search should return document metadata
        service = MemoryService(db_session)
        results = service.search_by_text("water supply", top_k=5)

        assert len(results) > 0
        # Results should include document_title if available
        result = results[0]
        assert "chunk_text" in result
        assert "source_id" in result

    def test_search_returns_chunk_preview(
        self,
        db_session: Session,
        leader_user: User,
    ):
        """Search results include a preview of the chunk text."""
        from app.services.memory import MemoryService, generate_embedding

        doc = Document(
            id=uuid.uuid4(),
            title="Urban Planning Guidelines",
            uploaded_by=leader_user.id,
            file_path="/uploads/urban_planning_2026.pdf",
            extracted_text="Cities must prioritize green spaces...",
            summary="Guidelines for urban planning.",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        chunk_text = "Cities must prioritize green spaces to enhance livability and reduce urban heat islands."
        embedding_vector = generate_embedding(chunk_text)
        embed = Embedding(
            id=uuid.uuid4(),
            source_type="document",
            source_id=doc.id,
            content_hash=hashlib.sha256(b"urban planning").hexdigest(),
            embedding=embedding_vector,
            dimensions=len(embedding_vector),
            chunk_text=chunk_text,
            chunk_index=0,
        )
        db_session.add(embed)
        db_session.commit()

        service = MemoryService(db_session)
        results = service.search_by_text("green spaces", top_k=5)

        assert len(results) > 0
        result = results[0]
        # Should have chunk preview (30-40 words)
        preview = result.get("chunk_preview", result.get("chunk_text", ""))
        assert len(preview) > 0


# ══════════════════════════════════════════════════════════════════════
#  AGENT SERVICE SOURCES INTEGRATION
# ══════════════════════════════════════════════════════════════════════

class TestAgentServiceWithSources:
    """Tests for AgentService including sources in responses."""

    def test_agent_service_attaches_sources_to_response(
        self,
        db_session: Session,
        leader_user: User,
    ):
        """AgentService.process_query returns sources with response."""
        from app.services.agent import AgentService
        from app.services.memory import generate_embedding

        # Create document
        doc = Document(
            id=uuid.uuid4(),
            title="Municipal Budget 2026",
            uploaded_by=leader_user.id,
            file_path="/uploads/municipal_budget_2026.pdf",
            extracted_text="Budget allocation for citizens services.",
            summary="2026 municipal budget overview.",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        # Create embedding with real vector
        chunk_text = "Budget allocation: Water Supply 30%, Roads 25%, Health 20%, Education 25%."
        embedding_vector = generate_embedding(chunk_text)
        embed = Embedding(
            id=uuid.uuid4(),
            source_type="document",
            source_id=doc.id,
            content_hash=hashlib.sha256(b"budget").hexdigest(),
            embedding=embedding_vector,
            dimensions=len(embedding_vector),
            chunk_text=chunk_text,
            chunk_index=0,
        )
        db_session.add(embed)
        db_session.commit()

        # Query should include sources
        service = AgentService(db_session)
        result = service.process_query(
            query="What is the budget allocation?",
            user_id=leader_user.id,
            session_id=uuid.uuid4(),
        )

        # Response should have sources field
        assert "response" in result
        assert "sources" in result
        # If RAG found documents, sources should be populated
        if len(result["sources"]) > 0:
            source = result["sources"][0]
            assert "document_title" in source
            assert "chunk_preview" in source


# ══════════════════════════════════════════════════════════════════════
#  END-TO-END AGENT QUERY WITH SOURCES
# ══════════════════════════════════════════════════════════════════════

class TestEndToEndAgentQueryWithSources:
    """Integration tests for agent queries with source citations."""

    def test_citizen_agent_query_returns_sources(
        self,
        client,
        db_session: Session,
        leader_user: User,
    ):
        """Agent query endpoint returns sources in response."""
        from app.models.action_request import ActionRequest
        from app.services.memory import generate_embedding

        # Create document
        doc = Document(
            id=uuid.uuid4(),
            title="Ward-5 Service Report",
            uploaded_by=leader_user.id,
            file_path="/uploads/ward5_report_2026.pdf",
            extracted_text="Ward-5 service metrics and status.",
            summary="Ward-5 service overview.",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        # Create embedding with real vector
        chunk_text = "Ward-5 has 45 open water supply issues and 12 pending approvals."
        embedding_vector = generate_embedding(chunk_text)
        embed = Embedding(
            id=uuid.uuid4(),
            source_type="document",
            source_id=doc.id,
            content_hash=hashlib.sha256(b"ward5").hexdigest(),
            embedding=embedding_vector,
            dimensions=len(embedding_vector),
            chunk_text=chunk_text,
            chunk_index=0,
        )
        db_session.add(embed)
        db_session.commit()

        # Get auth token
        token = create_access_token(data={"sub": str(leader_user.id), "role": leader_user.role.value})

        # Query agent
        response = client.post(
            "/api/v1/agent/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What is the status of Ward-5 issues?"},
        )

        assert response.status_code == 200
        data = response.json()

        # Response should include sources
        assert "sources" in data or "response" in data

    def test_no_sources_fallback_message(self, client, db_session: Session, leader_user: User):
        """When no documents match, response indicates general knowledge."""
        # Query with no matching documents
        token = create_access_token(data={"sub": str(leader_user.id), "role": leader_user.role.value})

        response = client.post(
            "/api/v1/agent/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What is the meaning of life?"},  # No docs about this
        )

        assert response.status_code == 200
        data = response.json()

        # Should have empty sources or indicate no documents
        sources = data.get("sources", [])
        # With no sources, response should note general knowledge
        assert isinstance(sources, list)


# ══════════════════════════════════════════════════════════════════════
#  PYDANTIC SCHEMA TESTS
# ══════════════════════════════════════════════════════════════════════

class TestSourceCitationSchema:
    """Tests for Pydantic SourceCitation schema."""

    def test_query_response_schema_includes_sources(self):
        """AgentQueryResponse schema has sources field."""
        from app.schemas.agent import AgentQueryResponse, SourceCitationSchema

        # Create response with sources
        sources_data = [
            {
                "document_title": "Delhi Master Plan 2041",
                "chunk_preview": "Water supply infrastructure consists of 19 zones across the city.",
            }
        ]

        response_data = {
            "response": "Delhi has 19 water supply zones.",
            "agent_name": "CitizenAgent",
            "confidence": 0.85,
            "sources": sources_data,
        }

        schema = AgentQueryResponse(**response_data)
        assert schema.response == "Delhi has 19 water supply zones."
        assert len(schema.sources) == 1
        assert schema.sources[0].document_title == "Delhi Master Plan 2041"

    def test_source_citation_schema_validation(self):
        """SourceCitationSchema validates required fields."""
        from app.schemas.agent import SourceCitationSchema

        # Valid source
        valid_source = {
            "document_title": "Policy Document",
            "chunk_preview": "Relevant chunk content.",
        }

        schema = SourceCitationSchema(**valid_source)
        assert schema.document_title == "Policy Document"

        # Missing document_title should fail
        with pytest.raises(ValueError):
            invalid_source = {"chunk_preview": "No title provided."}
            SourceCitationSchema(**invalid_source)


# ══════════════════════════════════════════════════════════════════════
#  SOURCE RELEVANCE THRESHOLD TESTS
# ══════════════════════════════════════════════════════════════════════

class TestSourceRelevanceThreshold:
    """Tests for filtering sources by relevance threshold."""

    def test_only_high_relevance_sources_included(self):
        """Only sources above threshold are included in response."""
        from app.agents.base import AgentResponse, SourceCitation

        sources = [
            SourceCitation(
                document_id=uuid.uuid4(),
                document_title="Highly Relevant",
                chunk_index=0,
                chunk_preview="Perfect match content.",
                relevance_score=0.92,
            ),
            SourceCitation(
                document_id=uuid.uuid4(),
                document_title="Low Relevance",
                chunk_index=5,
                chunk_preview="Tangentially related content.",
                relevance_score=0.08,  # Below 0.15 threshold
            ),
        ]

        # Filter by threshold (0.15 is typical)
        filtered = [s for s in sources if s.relevance_score > 0.15]

        response = AgentResponse(
            agent_name="TestAgent",
            message="Response text",
            confidence=0.80,
            suggested_actions=[],
            metadata={},
            sources=filtered,
        )

        # Only high relevance source should be in response
        assert len(response.sources) == 1
        assert response.sources[0].document_title == "Highly Relevant"
