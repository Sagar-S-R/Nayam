"""
NAYAM (नयम्) — Notification Service.

Pure aggregation layer — pulls recent high-signal events from existing
repositories and presents them as a unified notification feed.
No dedicated DB table needed (phase-1).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.action_request import ActionRequest, ActionStatus
from app.models.issue import Issue, IssueStatus, IssuePriority
from app.models.document import Document
from app.models.event import Event, EventStatus
from app.schemas.notification import NotificationItem, NotificationsResponse

logger = logging.getLogger(__name__)


class NotificationService:
    """Aggregate recent events into notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── helpers ───────────────────────────────────────────────────────

    def _pending_approvals(self) -> list[NotificationItem]:
        """Action requests still awaiting human review."""
        rows = (
            self.db.query(ActionRequest)
            .filter(ActionRequest.status == ActionStatus.PENDING)
            .order_by(ActionRequest.created_at.desc())
            .limit(10)
            .all()
        )
        return [
            NotificationItem(
                id=f"approval-{r.id}",
                type="pending_approval",
                title=f"Pending: {r.action_type.replace('_', ' ').title()}",
                detail=r.description[:120],
                severity="warning",
                timestamp=r.created_at,
                link="/approvals",
            )
            for r in rows
        ]

    def _critical_issues(self) -> list[NotificationItem]:
        """Open issues with High priority (last 20)."""
        rows = (
            self.db.query(Issue)
            .filter(
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS]),
                Issue.priority == IssuePriority.HIGH,
            )
            .order_by(Issue.created_at.desc())
            .limit(20)
            .all()
        )
        return [
            NotificationItem(
                id=f"issue-{r.id}",
                type="critical_issue",
                title=f"[HIGH] {r.department}",
                detail=(r.description or "")[:120],
                severity="critical",
                timestamp=r.created_at,
                link="/issues",
            )
            for r in rows
        ]

    def _recent_documents(self) -> list[NotificationItem]:
        """Last 5 documents uploaded."""
        rows = (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .limit(5)
            .all()
        )
        return [
            NotificationItem(
                id=f"doc-{r.id}",
                type="new_document",
                title=f"📄 {r.title}",
                detail=f"Uploaded by {r.uploaded_by or 'system'}",
                severity="info",
                timestamp=r.created_at,
                link="/documents",
            )
            for r in rows
        ]

    def _upcoming_events(self) -> list[NotificationItem]:
        """Scheduled events in the next 48 hours."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=48)
        rows = (
            self.db.query(Event)
            .filter(
                Event.status == EventStatus.SCHEDULED,
                Event.start_time >= now,
                Event.start_time <= cutoff,
            )
            .order_by(Event.start_time.asc())
            .limit(10)
            .all()
        )
        items = []
        for r in rows:
            hours_until = max(0, (r.start_time.replace(tzinfo=timezone.utc) - now).total_seconds() / 3600)
            if hours_until < 1:
                time_label = "in less than 1 hour"
            elif hours_until < 24:
                time_label = f"in {int(hours_until)} hours"
            else:
                time_label = f"tomorrow"
            items.append(
                NotificationItem(
                    id=f"event-{r.id}",
                    type="system",
                    title=f"📅 {r.title}",
                    detail=f"{r.event_type.value} {time_label} at {r.location or 'TBD'}",
                    severity="warning" if hours_until < 6 else "info",
                    timestamp=r.start_time if r.start_time.tzinfo else r.start_time.replace(tzinfo=timezone.utc),
                    link="/schedule",
                )
            )
        return items

    # ── public API ────────────────────────────────────────────────────

    def get_notifications(self) -> NotificationsResponse:
        """Return aggregated notifications sorted newest-first."""
        items: list[NotificationItem] = []
        items.extend(self._pending_approvals())
        items.extend(self._critical_issues())
        items.extend(self._recent_documents())
        items.extend(self._upcoming_events())

        # Sort by timestamp descending (handle mixed tz-aware/naive datetimes)
        def _sort_key(n: NotificationItem) -> datetime:
            ts = n.timestamp
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts

        items.sort(key=_sort_key, reverse=True)

        logger.info("Notifications aggregated: %d items", len(items))
        return NotificationsResponse(total=len(items), items=items)
