"""
NAYAM (नयम्) — Phase 2 Repository Unit Tests.

Covers:
  • ConversationRepository — store, session history, user sessions, delete
  • EmbeddingRepository    — store, source lookup, dedup hash, cosine search, delete
  • ActionRequestRepository — create, review, pending list, filters, aggregation
"""

import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, MessageRole
from app.models.embedding import Embedding
from app.models.action_request import ActionRequest, ActionStatus
from app.models.user import User

from app.repositories.conversation import ConversationRepository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.action_request import ActionRequestRepository


# ══════════════════════════════════════════════════════════════════════
#  CONVERSATION REPOSITORY
# ══════════════════════════════════════════════════════════════════════

class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_create_and_retrieve(self, db_session: Session, leader_user: User):
        """Store a message and retrieve it by ID."""
        repo = ConversationRepository(db_session)
        msg = Conversation(
            session_id=uuid.uuid4(),
            user_id=leader_user.id,
            role=MessageRole.USER,
            content="Hello agent",
        )
        created = repo.create(msg)

        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.content == "Hello agent"
        assert fetched.role == MessageRole.USER

    def test_create_many(self, db_session: Session, leader_user: User):
        """Batch-insert multiple messages."""
        repo = ConversationRepository(db_session)
        session_id = uuid.uuid4()
        msgs = [
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content="Q1"),
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.ASSISTANT, content="A1", agent_name="PolicyAgent"),
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content="Q2"),
        ]
        result = repo.create_many(msgs)
        assert len(result) == 3
        assert all(m.id is not None for m in result)

    def test_get_session_history(self, db_session: Session, leader_user: User):
        """Retrieve full session history ordered by time."""
        repo = ConversationRepository(db_session)
        session_id = uuid.uuid4()
        repo.create_many([
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content="First"),
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.ASSISTANT, content="Second"),
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content="Third"),
        ])

        history = repo.get_session_history(session_id)
        assert len(history) == 3
        assert history[0].content == "First"
        assert history[2].content == "Third"

    def test_get_session_history_with_limit(self, db_session: Session, leader_user: User):
        """Limit returns the last N messages."""
        repo = ConversationRepository(db_session)
        session_id = uuid.uuid4()
        repo.create_many([
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content=f"Msg {i}")
            for i in range(10)
        ])

        recent = repo.get_session_history(session_id, limit=3)
        assert len(recent) == 3
        # Should be the last 3 in chronological order
        assert recent[0].content == "Msg 7"
        assert recent[2].content == "Msg 9"

    def test_count_session_messages(self, db_session: Session, leader_user: User):
        """Count messages in a session."""
        repo = ConversationRepository(db_session)
        session_id = uuid.uuid4()
        repo.create_many([
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content=f"M{i}")
            for i in range(5)
        ])
        assert repo.count_session_messages(session_id) == 5

    def test_get_user_sessions(self, db_session: Session, leader_user: User):
        """Retrieve distinct session IDs for a user."""
        repo = ConversationRepository(db_session)
        s1, s2 = uuid.uuid4(), uuid.uuid4()
        repo.create(Conversation(session_id=s1, user_id=leader_user.id, role=MessageRole.USER, content="A"))
        repo.create(Conversation(session_id=s2, user_id=leader_user.id, role=MessageRole.USER, content="B"))
        repo.create(Conversation(session_id=s1, user_id=leader_user.id, role=MessageRole.USER, content="C"))

        sessions = repo.get_user_sessions(leader_user.id)
        assert len(sessions) == 2
        assert s1 in sessions
        assert s2 in sessions

    def test_delete_session(self, db_session: Session, leader_user: User):
        """Delete all messages in a session."""
        repo = ConversationRepository(db_session)
        session_id = uuid.uuid4()
        repo.create_many([
            Conversation(session_id=session_id, user_id=leader_user.id, role=MessageRole.USER, content=f"M{i}")
            for i in range(4)
        ])
        assert repo.count_session_messages(session_id) == 4

        deleted = repo.delete_session(session_id)
        assert deleted == 4
        assert repo.count_session_messages(session_id) == 0

    def test_get_by_id_not_found(self, db_session: Session):
        """Return None for non-existent message."""
        repo = ConversationRepository(db_session)
        assert repo.get_by_id(uuid.uuid4()) is None


# ══════════════════════════════════════════════════════════════════════
#  EMBEDDING REPOSITORY
# ══════════════════════════════════════════════════════════════════════

class TestEmbeddingRepository:
    """Tests for EmbeddingRepository."""

    @staticmethod
    def _make_vector(dim: int = 8, seed: float = 0.1) -> list:
        """Create a simple deterministic vector for testing."""
        return [seed * (i + 1) for i in range(dim)]

    def _make_embedding(self, source_id: uuid.UUID, text: str = "sample", chunk: int = 0, dim: int = 8) -> Embedding:
        """Helper to build an Embedding instance."""
        vec = self._make_vector(dim)
        return Embedding(
            source_type="document",
            source_id=source_id,
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
            chunk_index=chunk,
            chunk_text=text,
            embedding=vec,
            dimensions=dim,
            model_name="test-model",
        )

    def test_create_and_retrieve(self, db_session: Session):
        """Store an embedding and retrieve it by ID."""
        repo = EmbeddingRepository(db_session)
        emb = self._make_embedding(uuid.uuid4())
        created = repo.create(emb)

        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.source_type == "document"
        assert len(fetched.embedding) == 8

    def test_create_many(self, db_session: Session):
        """Batch-insert multiple embeddings."""
        repo = EmbeddingRepository(db_session)
        source_id = uuid.uuid4()
        embs = [self._make_embedding(source_id, f"chunk {i}", chunk=i) for i in range(3)]
        result = repo.create_many(embs)
        assert len(result) == 3

    def test_get_by_source(self, db_session: Session):
        """Retrieve all chunks for a specific source."""
        repo = EmbeddingRepository(db_session)
        src = uuid.uuid4()
        repo.create_many([self._make_embedding(src, f"c{i}", chunk=i) for i in range(3)])

        results = repo.get_by_source("document", src)
        assert len(results) == 3
        assert [r.chunk_index for r in results] == [0, 1, 2]

    def test_exists_by_content_hash(self, db_session: Session):
        """Check dedup via content hash."""
        repo = EmbeddingRepository(db_session)
        text = "unique text for hashing"
        emb = self._make_embedding(uuid.uuid4(), text)
        repo.create(emb)

        assert repo.exists_by_content_hash(hashlib.sha256(text.encode()).hexdigest()) is True
        assert repo.exists_by_content_hash("0000" * 16) is False

    def test_cosine_similarity_search(self, db_session: Session):
        """Search returns results sorted by similarity."""
        repo = EmbeddingRepository(db_session)

        # Insert 3 embeddings with known vectors
        src = uuid.uuid4()
        vecs = [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # pure x-axis
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # pure y-axis
            [0.7, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # between x and y
        ]
        for i, vec in enumerate(vecs):
            e = Embedding(
                source_type="document", source_id=src,
                content_hash=hashlib.sha256(f"v{i}".encode()).hexdigest(),
                chunk_index=i, chunk_text=f"vector {i}",
                embedding=vec, dimensions=8, model_name="test",
            )
            repo.create(e)

        # Query: close to x-axis
        query_vec = [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        results = repo.search_similar(query_vec, top_k=3)

        assert len(results) == 3
        # First result should be pure x-axis (most similar)
        assert results[0][0].chunk_text == "vector 0"
        assert results[0][1] > results[1][1]  # score descending

    def test_cosine_similarity_filter_by_source_type(self, db_session: Session):
        """Search can be filtered by source_type."""
        repo = EmbeddingRepository(db_session)

        vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        for stype in ["document", "conversation"]:
            e = Embedding(
                source_type=stype, source_id=uuid.uuid4(),
                content_hash=hashlib.sha256(stype.encode()).hexdigest(),
                chunk_index=0, chunk_text=stype,
                embedding=vec, dimensions=8, model_name="test",
            )
            repo.create(e)

        results = repo.search_similar(vec, source_type="document", top_k=10)
        assert len(results) == 1
        assert results[0][0].source_type == "document"

    def test_delete_by_source(self, db_session: Session):
        """Delete all embeddings for a source."""
        repo = EmbeddingRepository(db_session)
        src = uuid.uuid4()
        repo.create_many([self._make_embedding(src, f"c{i}", chunk=i) for i in range(3)])
        assert repo.total_count() == 3

        deleted = repo.delete_by_source("document", src)
        assert deleted == 3
        assert repo.total_count() == 0

    def test_total_count(self, db_session: Session):
        """Total count reflects all records."""
        repo = EmbeddingRepository(db_session)
        assert repo.total_count() == 0
        repo.create(self._make_embedding(uuid.uuid4()))
        assert repo.total_count() == 1


# ══════════════════════════════════════════════════════════════════════
#  ACTION REQUEST REPOSITORY
# ══════════════════════════════════════════════════════════════════════

class TestActionRequestRepository:
    """Tests for ActionRequestRepository."""

    @staticmethod
    def _make_action(user_id: uuid.UUID, **kwargs) -> ActionRequest:
        """Helper to build an ActionRequest with sensible defaults."""
        defaults = dict(
            session_id=uuid.uuid4(),
            agent_name="PolicyAgent",
            action_type="update_issue_status",
            description="Change issue status",
            payload={"issue_id": str(uuid.uuid4()), "new_status": "In Progress"},
            requested_by=user_id,
        )
        defaults.update(kwargs)
        return ActionRequest(**defaults)

    def test_create_and_retrieve(self, db_session: Session, leader_user: User):
        """Create an action request and retrieve it by ID."""
        repo = ActionRequestRepository(db_session)
        action = self._make_action(leader_user.id)
        created = repo.create(action)

        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.status == ActionStatus.PENDING
        assert fetched.agent_name == "PolicyAgent"

    def test_approve_action(self, db_session: Session, leader_user: User, staff_user: User):
        """Review an action request as approved."""
        repo = ActionRequestRepository(db_session)
        action = repo.create(self._make_action(leader_user.id))

        reviewed = repo.review(action, ActionStatus.APPROVED, staff_user.id, review_note="LGTM")

        assert reviewed.status == ActionStatus.APPROVED
        assert reviewed.reviewed_by == staff_user.id
        assert reviewed.review_note == "LGTM"
        assert reviewed.reviewed_at is not None

    def test_reject_action(self, db_session: Session, leader_user: User, staff_user: User):
        """Review an action request as rejected."""
        repo = ActionRequestRepository(db_session)
        action = repo.create(self._make_action(leader_user.id))

        reviewed = repo.review(action, ActionStatus.REJECTED, staff_user.id, review_note="Not appropriate")

        assert reviewed.status == ActionStatus.REJECTED

    def test_get_pending(self, db_session: Session, leader_user: User, staff_user: User):
        """List only pending action requests."""
        repo = ActionRequestRepository(db_session)
        a1 = repo.create(self._make_action(leader_user.id))
        a2 = repo.create(self._make_action(leader_user.id))
        a3 = repo.create(self._make_action(leader_user.id))

        # Approve one
        repo.review(a1, ActionStatus.APPROVED, staff_user.id)

        pending, total = repo.get_pending()
        assert total == 2
        assert len(pending) == 2
        pending_ids = {p.id for p in pending}
        assert a2.id in pending_ids
        assert a3.id in pending_ids

    def test_get_all_with_filters(self, db_session: Session, leader_user: User):
        """Filter actions by status and agent name."""
        repo = ActionRequestRepository(db_session)
        repo.create(self._make_action(leader_user.id, agent_name="PolicyAgent"))
        repo.create(self._make_action(leader_user.id, agent_name="CitizenAgent"))
        repo.create(self._make_action(leader_user.id, agent_name="PolicyAgent"))

        results, total = repo.get_all(agent_name="PolicyAgent")
        assert total == 2
        assert all(a.agent_name == "PolicyAgent" for a in results)

    def test_get_by_session(self, db_session: Session, leader_user: User):
        """Retrieve actions by conversation session."""
        repo = ActionRequestRepository(db_session)
        session_id = uuid.uuid4()
        repo.create(self._make_action(leader_user.id, session_id=session_id))
        repo.create(self._make_action(leader_user.id, session_id=session_id))
        repo.create(self._make_action(leader_user.id))  # different session

        results = repo.get_by_session(session_id)
        assert len(results) == 2

    def test_get_by_requester(self, db_session: Session, leader_user: User, staff_user: User):
        """Retrieve actions initiated by a specific user."""
        repo = ActionRequestRepository(db_session)
        repo.create(self._make_action(leader_user.id))
        repo.create(self._make_action(leader_user.id))
        repo.create(self._make_action(staff_user.id))

        results, total = repo.get_by_requester(leader_user.id)
        assert total == 2

    def test_count_by_status(self, db_session: Session, leader_user: User, staff_user: User):
        """Count actions grouped by status."""
        repo = ActionRequestRepository(db_session)
        a1 = repo.create(self._make_action(leader_user.id))
        repo.create(self._make_action(leader_user.id))
        repo.create(self._make_action(leader_user.id))
        repo.review(a1, ActionStatus.APPROVED, staff_user.id)

        counts = dict(repo.count_by_status())
        assert counts.get(ActionStatus.PENDING) == 2
        assert counts.get(ActionStatus.APPROVED) == 1

    def test_pending_count(self, db_session: Session, leader_user: User):
        """Quick pending count check."""
        repo = ActionRequestRepository(db_session)
        for _ in range(3):
            repo.create(self._make_action(leader_user.id))
        assert repo.pending_count() == 3

    def test_delete_action(self, db_session: Session, leader_user: User):
        """Delete an action request."""
        repo = ActionRequestRepository(db_session)
        action = repo.create(self._make_action(leader_user.id))
        action_id = action.id

        repo.delete(action)
        assert repo.get_by_id(action_id) is None

    def test_get_by_id_not_found(self, db_session: Session):
        """Return None for non-existent action."""
        repo = ActionRequestRepository(db_session)
        assert repo.get_by_id(uuid.uuid4()) is None
