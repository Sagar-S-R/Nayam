"""
NAYAM (नयम्) — ORM Models Package.
"""

# Phase 1 models
from app.models.user import User
from app.models.citizen import Citizen
from app.models.issue import Issue
from app.models.document import Document

# Phase 2 models
from app.models.conversation import Conversation
from app.models.embedding import Embedding
from app.models.action_request import ActionRequest

# Phase 3 models
from app.predictive.models import RiskScore
from app.predictive.anomaly_model import AnomalyLog
from app.geospatial.models import GeoCluster
from app.recommendations.models import TaskRecommendation, ExecutionFeedback
from app.observability.models import AuditLog
from app.privacy.models import EncryptedFieldRegistry

# Phase 4 models
from app.sync.models import SyncQueue
from app.sync.conflict_model import ConflictLog
from app.offline.models import OfflineAction
from app.compliance.models import ComplianceExport
from app.monitoring.models import PerformanceMetric
from app.hardening.models import RateLimitRecord

# Phase 5 models — PS gap closure
from app.models.event import Event
from app.models.draft import Draft

__all__ = [
    # Phase 1
    "User",
    "Citizen",
    "Issue",
    "Document",
    # Phase 2
    "Conversation",
    "Embedding",
    "ActionRequest",
    # Phase 3
    "RiskScore",
    "AnomalyLog",
    "GeoCluster",
    "TaskRecommendation",
    "ExecutionFeedback",
    "AuditLog",
    "EncryptedFieldRegistry",
    # Phase 4
    "SyncQueue",
    "ConflictLog",
    "OfflineAction",
    "ComplianceExport",
    "PerformanceMetric",
    "RateLimitRecord",
    # Phase 5
    "Event",
    "Draft",
]
