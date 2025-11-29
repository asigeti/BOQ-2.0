"""
Metrics Service for ConstructionAI Pro

Tracks and stores extraction performance metrics.
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Context manager for tracking extraction metrics.

    Usage:
        with MetricsTracker(plan_id, db, file_path) as tracker:
            # Do extraction
            materials = extract_from_pdf(file_path)
            tracker.record_results(materials, method='pdf_text', model='gpt-4o')
    """

    def __init__(self, plan_id: int, db: Session, file_path: str):
        self.plan_id = plan_id
        self.db = db
        self.file_path = file_path
        self.start_time: Optional[float] = None
        self.metrics: Dict = {}
        self.errors: List[str] = []

    def __enter__(self):
        self.start_time = time.time()
        self.metrics['started_at'] = datetime.utcnow()

        # Get file size
        try:
            self.metrics['file_size_bytes'] = os.path.getsize(self.file_path)
        except OSError:
            self.metrics['file_size_bytes'] = 0

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate processing time
        self.metrics['processing_time_seconds'] = time.time() - self.start_time
        self.metrics['completed_at'] = datetime.utcnow()

        # Record any exception as error
        if exc_type is not None:
            self.errors.append(f"{exc_type.__name__}: {str(exc_val)}")

        # Save metrics to database
        self._save_metrics()

        # Don't suppress exceptions
        return False

    def record_results(
        self,
        materials: List[Dict],
        method: str = 'unknown',
        model: str = None,
        tokens_used: int = 0,
        pages_processed: int = 0,
        images_processed: int = 0
    ):
        """Record extraction results"""
        self.metrics['extraction_method'] = method
        self.metrics['model_used'] = model
        self.metrics['tokens_used'] = tokens_used
        self.metrics['pages_processed'] = pages_processed
        self.metrics['images_processed'] = images_processed
        self.metrics['materials_extracted'] = len(materials)

        # Calculate confidence score statistics
        if materials:
            confidence_scores = [
                m.get('confidence_score', 0.5)
                for m in materials
                if 'confidence_score' in m
            ]

            if confidence_scores:
                self.metrics['avg_confidence_score'] = sum(confidence_scores) / len(confidence_scores)
                self.metrics['min_confidence_score'] = min(confidence_scores)
                self.metrics['max_confidence_score'] = max(confidence_scores)

        # Estimate API cost (approximate)
        if tokens_used > 0:
            cost_per_1k_tokens = 0.01 if 'gpt-4' in (model or '') else 0.002
            self.metrics['api_cost_usd'] = (tokens_used / 1000) * cost_per_1k_tokens

    def record_error(self, error: str):
        """Record an error that occurred during extraction"""
        self.errors.append(error)

    def _save_metrics(self):
        """Save metrics to database"""
        try:
            metrics_record = models.ExtractionMetrics(
                plan_id=self.plan_id,
                processing_time_seconds=self.metrics.get('processing_time_seconds'),
                pages_processed=self.metrics.get('pages_processed', 0),
                images_processed=self.metrics.get('images_processed', 0),
                extraction_method=self.metrics.get('extraction_method'),
                file_size_bytes=self.metrics.get('file_size_bytes'),
                materials_extracted=self.metrics.get('materials_extracted', 0),
                avg_confidence_score=self.metrics.get('avg_confidence_score'),
                min_confidence_score=self.metrics.get('min_confidence_score'),
                max_confidence_score=self.metrics.get('max_confidence_score'),
                model_used=self.metrics.get('model_used'),
                tokens_used=self.metrics.get('tokens_used', 0),
                api_cost_usd=self.metrics.get('api_cost_usd', 0.0),
                extraction_errors=self.errors if self.errors else None,
                started_at=self.metrics.get('started_at'),
                completed_at=self.metrics.get('completed_at')
            )

            self.db.add(metrics_record)
            self.db.commit()

            logger.info(
                f"Metrics saved for plan {self.plan_id}: "
                f"{self.metrics.get('materials_extracted', 0)} materials, "
                f"{self.metrics.get('processing_time_seconds', 0):.2f}s"
            )

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
            # Don't raise - metrics failure shouldn't break extraction


def get_extraction_stats(db: Session, days: int = 30) -> Dict:
    """
    Get extraction statistics for the last N days.

    Returns summary stats for dashboard display.
    """
    from datetime import timedelta
    from sqlalchemy import func

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query aggregated stats
    stats = db.query(
        func.count(models.ExtractionMetrics.id).label('total_extractions'),
        func.sum(models.ExtractionMetrics.materials_extracted).label('total_materials'),
        func.avg(models.ExtractionMetrics.processing_time_seconds).label('avg_processing_time'),
        func.avg(models.ExtractionMetrics.avg_confidence_score).label('avg_confidence'),
        func.sum(models.ExtractionMetrics.tokens_used).label('total_tokens'),
        func.sum(models.ExtractionMetrics.api_cost_usd).label('total_cost')
    ).filter(
        models.ExtractionMetrics.created_at >= cutoff_date
    ).first()

    # Query by method
    method_stats = db.query(
        models.ExtractionMetrics.extraction_method,
        func.count(models.ExtractionMetrics.id).label('count')
    ).filter(
        models.ExtractionMetrics.created_at >= cutoff_date
    ).group_by(
        models.ExtractionMetrics.extraction_method
    ).all()

    return {
        'period_days': days,
        'total_extractions': stats.total_extractions or 0,
        'total_materials': int(stats.total_materials or 0),
        'avg_processing_time_seconds': round(stats.avg_processing_time or 0, 2),
        'avg_confidence_score': round(stats.avg_confidence or 0, 2),
        'total_tokens_used': int(stats.total_tokens or 0),
        'total_api_cost_usd': round(stats.total_cost or 0, 4),
        'extractions_by_method': {
            m.extraction_method: m.count
            for m in method_stats
            if m.extraction_method
        }
    }
