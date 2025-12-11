"""
BOQ Aggregation Service

Combines BOQ items from multiple plan files into a unified project BOQ.
Handles deduplication, quantity summation, and source tracking.
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field
import logging
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)


@dataclass
class AggregatedItem:
    """Represents an aggregated BOQ item from multiple sources."""
    item_code: str
    chapter_code: str
    chapter_name_he: str
    chapter_name_en: str
    description_he: str
    description_en: str
    unit: str
    unit_price: float
    total_quantity: float = 0.0
    total_price: float = 0.0
    sources: List[Dict[str, Any]] = field(default_factory=list)
    avg_confidence: float = 0.0
    item_ids: List[int] = field(default_factory=list)

    def add_source(self, item: models.BOQItem):
        """Add a source item to this aggregated item."""
        self.total_quantity += item.quantity
        self.sources.append({
            "plan_id": item.plan_id,
            "filename": item.source_filename or "Unknown",
            "layer": item.source_layer,
            "quantity": item.quantity,
            "confidence": item.confidence or 0.5,
        })
        self.item_ids.append(item.id)

        # Update average confidence
        confidences = [s["confidence"] for s in self.sources]
        self.avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Recalculate total price
        self.total_price = self.total_quantity * self.unit_price

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "item_code": self.item_code,
            "chapter_code": self.chapter_code,
            "chapter_name_he": self.chapter_name_he,
            "chapter_name_en": self.chapter_name_en,
            "description_he": self.description_he,
            "description_en": self.description_en,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "total_quantity": round(self.total_quantity, 2),
            "total_price": round(self.total_price, 2),
            "source_count": len(self.sources),
            "sources": self.sources,
            "avg_confidence": round(self.avg_confidence, 2),
            "item_ids": self.item_ids,
        }


@dataclass
class AggregatedChapter:
    """Represents a chapter with aggregated items."""
    chapter_code: str
    chapter_name_he: str
    chapter_name_en: str
    items: Dict[str, AggregatedItem] = field(default_factory=dict)

    @property
    def total_price(self) -> float:
        return sum(item.total_price for item in self.items.values())

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        sorted_items = sorted(self.items.values(), key=lambda x: x.item_code)
        return {
            "chapter_code": self.chapter_code,
            "chapter_name_he": self.chapter_name_he,
            "chapter_name_en": self.chapter_name_en,
            "items": [item.to_dict() for item in sorted_items],
            "item_count": self.item_count,
            "chapter_total": round(self.total_price, 2),
        }


class BOQAggregator:
    """
    Aggregates BOQ items from multiple plans into a unified project BOQ.

    Features:
    - Deduplicates items by item_code
    - Sums quantities for matching items
    - Tracks source files for each item
    - Organizes by chapter
    - Calculates totals and statistics
    """

    def __init__(self, db: Session):
        self.db = db
        self.chapters: Dict[str, AggregatedChapter] = {}

    def aggregate_project(self, project_id: int, include_deleted: bool = False) -> Dict[str, Any]:
        """
        Aggregate all BOQ items for a project.

        Args:
            project_id: The project ID to aggregate
            include_deleted: Whether to include soft-deleted items

        Returns:
            Dictionary with aggregated BOQ data
        """
        # Get all BOQ items for the project
        query = self.db.query(models.BOQItem).filter(
            models.BOQItem.project_id == project_id
        )

        if not include_deleted:
            query = query.filter(models.BOQItem.is_deleted == False)

        items = query.order_by(
            models.BOQItem.chapter_code,
            models.BOQItem.item_code
        ).all()

        if not items:
            return {
                "project_id": project_id,
                "chapters": [],
                "summary": {
                    "total_items": 0,
                    "total_chapters": 0,
                    "total_price": 0,
                    "source_files": [],
                    "aggregation_stats": {}
                }
            }

        # Reset chapters
        self.chapters = {}

        # Track unique source files
        source_files = set()
        original_item_count = 0

        # Process each item
        for item in items:
            original_item_count += 1

            # Track source file
            if item.source_filename:
                source_files.add(item.source_filename)

            # Get or create chapter
            chapter = self._get_or_create_chapter(item)

            # Get or create aggregated item
            agg_item = self._get_or_create_item(chapter, item)

            # Add this source to the aggregated item
            agg_item.add_source(item)

        # Build result
        sorted_chapters = sorted(self.chapters.values(), key=lambda x: x.chapter_code)

        total_price = sum(ch.total_price for ch in sorted_chapters)
        total_aggregated_items = sum(ch.item_count for ch in sorted_chapters)

        return {
            "project_id": project_id,
            "chapters": [ch.to_dict() for ch in sorted_chapters],
            "summary": {
                "total_items": total_aggregated_items,
                "total_chapters": len(sorted_chapters),
                "total_price": round(total_price, 2),
                "source_files": list(source_files),
                "source_file_count": len(source_files),
                "aggregation_stats": {
                    "original_items": original_item_count,
                    "aggregated_items": total_aggregated_items,
                    "items_merged": original_item_count - total_aggregated_items,
                    "merge_ratio": round(original_item_count / total_aggregated_items, 2) if total_aggregated_items > 0 else 0
                }
            }
        }

    def aggregate_by_plan_type(self, project_id: int) -> Dict[str, Any]:
        """
        Aggregate BOQ items grouped by plan/file type.

        Args:
            project_id: The project ID

        Returns:
            Dictionary with items grouped by source file
        """
        # Get all plans for the project
        plans = self.db.query(models.ProjectPlan).filter(
            models.ProjectPlan.project_id == project_id
        ).all()

        result = {
            "project_id": project_id,
            "plans": [],
            "summary": {
                "total_plans": len(plans),
                "total_price": 0.0
            }
        }

        for plan in plans:
            # Get BOQ items for this plan
            items = self.db.query(models.BOQItem).filter(
                models.BOQItem.project_id == project_id,
                models.BOQItem.plan_id == plan.id,
                models.BOQItem.is_deleted == False
            ).order_by(
                models.BOQItem.chapter_code,
                models.BOQItem.item_code
            ).all()

            plan_total = sum(item.total_price for item in items)

            plan_data = {
                "plan_id": plan.id,
                "filename": plan.filename,
                "file_type": plan.file_type,
                "item_count": len(items),
                "total_price": round(plan_total, 2),
                "chapters": self._group_items_by_chapter(items)
            }

            result["plans"].append(plan_data)
            result["summary"]["total_price"] += plan_total

        result["summary"]["total_price"] = round(result["summary"]["total_price"], 2)

        return result

    def get_chapter_summary(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get summary of BOQ by chapter for a project.

        Args:
            project_id: The project ID

        Returns:
            List of chapter summaries
        """
        aggregated = self.aggregate_project(project_id)

        return [
            {
                "chapter_code": ch["chapter_code"],
                "chapter_name_he": ch["chapter_name_he"],
                "chapter_name_en": ch["chapter_name_en"],
                "item_count": ch["item_count"],
                "chapter_total": ch["chapter_total"]
            }
            for ch in aggregated["chapters"]
        ]

    def _get_or_create_chapter(self, item: models.BOQItem) -> AggregatedChapter:
        """Get or create an aggregated chapter."""
        if item.chapter_code not in self.chapters:
            self.chapters[item.chapter_code] = AggregatedChapter(
                chapter_code=item.chapter_code,
                chapter_name_he=item.chapter_name_he,
                chapter_name_en=item.chapter_name_en or ""
            )
        return self.chapters[item.chapter_code]

    def _get_or_create_item(self, chapter: AggregatedChapter, item: models.BOQItem) -> AggregatedItem:
        """Get or create an aggregated item within a chapter."""
        if item.item_code not in chapter.items:
            chapter.items[item.item_code] = AggregatedItem(
                item_code=item.item_code,
                chapter_code=item.chapter_code,
                chapter_name_he=item.chapter_name_he,
                chapter_name_en=item.chapter_name_en or "",
                description_he=item.description_he,
                description_en=item.description_en or "",
                unit=item.unit,
                unit_price=item.unit_price
            )
        return chapter.items[item.item_code]

    def _group_items_by_chapter(self, items: List[models.BOQItem]) -> List[Dict[str, Any]]:
        """Group items by chapter for a single plan."""
        chapters: Dict[str, List[Dict]] = defaultdict(list)
        chapter_names: Dict[str, tuple] = {}

        for item in items:
            chapters[item.chapter_code].append({
                "id": item.id,
                "item_code": item.item_code,
                "description_he": item.description_he,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "source_layer": item.source_layer,
                "confidence": item.confidence
            })
            chapter_names[item.chapter_code] = (item.chapter_name_he, item.chapter_name_en or "")

        result = []
        for code in sorted(chapters.keys()):
            name_he, name_en = chapter_names[code]
            chapter_items = chapters[code]
            result.append({
                "chapter_code": code,
                "chapter_name_he": name_he,
                "chapter_name_en": name_en,
                "items": sorted(chapter_items, key=lambda x: x["item_code"]),
                "chapter_total": round(sum(i["total_price"] for i in chapter_items), 2)
            })

        return result


def get_aggregated_boq(db: Session, project_id: int, include_deleted: bool = False) -> Dict[str, Any]:
    """
    Convenience function to get aggregated BOQ for a project.

    Args:
        db: Database session
        project_id: The project ID
        include_deleted: Whether to include soft-deleted items

    Returns:
        Aggregated BOQ data
    """
    aggregator = BOQAggregator(db)
    return aggregator.aggregate_project(project_id, include_deleted)


def get_boq_by_plan(db: Session, project_id: int) -> Dict[str, Any]:
    """
    Convenience function to get BOQ grouped by plan/file.

    Args:
        db: Database session
        project_id: The project ID

    Returns:
        BOQ data grouped by source plan
    """
    aggregator = BOQAggregator(db)
    return aggregator.aggregate_by_plan_type(project_id)


def get_chapter_summary(db: Session, project_id: int) -> List[Dict[str, Any]]:
    """
    Convenience function to get chapter summary for a project.

    Args:
        db: Database session
        project_id: The project ID

    Returns:
        List of chapter summaries
    """
    aggregator = BOQAggregator(db)
    return aggregator.get_chapter_summary(project_id)
