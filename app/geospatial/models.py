"""
NAYAM (नयम्) — GeoCluster ORM Model (Phase 3).

Stores geographic cluster information produced by the spatial
analysis engine.  Each cluster groups nearby issues for heatmap
rendering and density analysis.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class GeoCluster(Base):
    """
    Geo-spatial issue cluster.

    Attributes:
        id:              UUID primary key.
        ward:            Ward that this cluster belongs to.
        center_lat:      Cluster centroid latitude.
        center_lng:      Cluster centroid longitude.
        radius_meters:   Approximate cluster radius.
        issue_count:     Number of issues in the cluster.
        density_score:   Normalised density metric (0.0 – 1.0).
        dominant_dept:   Most common department in the cluster.
        boundary:        GeoJSON polygon (stored as JSON for portability).
        computed_at:     When this cluster was generated.
    """

    __tablename__ = "geo_clusters"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    ward = Column(String(100), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False, default=500.0)
    issue_count = Column(Integer, nullable=False, default=0)
    density_score = Column(Float, nullable=False, default=0.0)
    dominant_department = Column(String(255), nullable=True)
    boundary = Column(JSON, nullable=True)  # GeoJSON polygon
    computed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_geo_clusters_ward", "ward"),
        Index("ix_geo_clusters_center", "center_lat", "center_lng"),
        Index("ix_geo_clusters_density", "density_score"),
        Index("ix_geo_clusters_computed_at", "computed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<GeoCluster(ward={self.ward}, center=({self.center_lat},{self.center_lng}), "
            f"issues={self.issue_count}, density={self.density_score})>"
        )
