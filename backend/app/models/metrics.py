"""
Extraction Metrics Model for ConstructionAI Pro

Tracks performance and accuracy metrics for material extraction operations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExtractionMetrics(Base):
    """
    Stores metrics for each extraction operation.

    Used for:
    - Performance monitoring (processing time)
    - Accuracy tracking (confidence scores, user corrections)
    - AI model optimization (which models work best)
    - Cost tracking (API tokens used)
    """
    __tablename__ = "extraction_metrics"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id"), nullable=False)

    # Processing metrics
    processing_time_seconds = Column(Float)
    pages_processed = Column(Integer, default=0)
    images_processed = Column(Integer, default=0)

    # Extraction details
    extraction_method = Column(String)  # 'pdf_text', 'pdf_vision', 'ifc', 'dxf', 'image'
    file_size_bytes = Column(Integer)

    # Results metrics
    materials_extracted = Column(Integer, default=0)
    avg_confidence_score = Column(Float)
    min_confidence_score = Column(Float)
    max_confidence_score = Column(Float)

    # User feedback (populated later when user reviews)
    user_corrections = Column(Integer, default=0)
    accuracy_rating = Column(Float)  # User-provided 1-5 rating

    # AI model info
    model_used = Column(String)
    tokens_used = Column(Integer, default=0)
    api_cost_usd = Column(Float, default=0.0)

    # Raw data for debugging
    extraction_errors = Column(JSON)  # List of any errors encountered

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    plan = relationship("ProjectPlan", backref="metrics")


class DailyStats(Base):
    """
    Aggregated daily statistics for dashboard reporting.
    """
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # Volume metrics
    plans_processed = Column(Integer, default=0)
    materials_extracted = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)

    # Performance metrics
    avg_processing_time = Column(Float)
    total_processing_time = Column(Float)

    # Quality metrics
    avg_confidence_score = Column(Float)
    avg_accuracy_rating = Column(Float)

    # Cost metrics
    total_tokens_used = Column(Integer, default=0)
    total_api_cost_usd = Column(Float, default=0.0)

    # Breakdown by method
    pdf_extractions = Column(Integer, default=0)
    ifc_extractions = Column(Integer, default=0)
    dxf_extractions = Column(Integer, default=0)
    image_extractions = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
