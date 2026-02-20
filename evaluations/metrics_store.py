"""Metrics storage for evaluation results.

This module provides the MetricsStore class for persisting evaluation
results to both JSON files and the database.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path

from sqlmodel import Session, select

from layers.models import EvaluationJob, EvaluationResult as EvaluationResultModel
from evaluations.schemas import (
    EvaluationResult,
    AggregatedSummary,
    MetricDistribution,
    EvaluationJobResult,
)
from evaluations.config import EvaluationConfig, EvaluationStatus


class MetricsStore:
    """Persists evaluation results to JSON and database.
    
    This class handles:
    - Saving individual evaluation results to the database
    - Updating job records with aggregated scores
    - Writing results to JSON files
    - Retrieving historical evaluation data
    
    Attributes:
        session: SQLModel database session.
        output_dir: Directory for JSON output files.
        save_to_db: Whether to save results to database.
        save_to_json: Whether to save results to JSON files.
    """
    
    def __init__(
        self,
        session: Session,
        output_dir: str = "evaluations/results",
        save_to_db: bool = True,
        save_to_json: bool = True,
    ):
        """Initialize the metrics store.
        
        Args:
            session: SQLModel database session.
            output_dir: Directory for JSON output files.
            save_to_db: Whether to save results to database.
            save_to_json: Whether to save results to JSON files.
        """
        self.session = session
        self.output_dir = output_dir
        self._save_to_db = save_to_db
        self._save_to_json = save_to_json
        
        # Ensure output directory exists
        if self._save_to_json:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_config(cls, session: Session, config: EvaluationConfig) -> "MetricsStore":
        """Create MetricsStore from EvaluationConfig.
        
        Args:
            session: SQLModel database session.
            config: EvaluationConfig instance.
        
        Returns:
            MetricsStore instance with config settings.
        """
        return cls(
            session=session,
            output_dir=config.output_dir,
            save_to_db=config.save_to_db,
            save_to_json=config.save_to_json,
        )
    
    def create_job(
        self,
        company_id: Optional[UUID] = None,
        config_snapshot: Optional[Dict[str, Any]] = None,
    ) -> EvaluationJob:
        """Create a new evaluation job record.
        
        Args:
            company_id: Optional company ID for the job.
            config_snapshot: Configuration used for this job.
        
        Returns:
            Created EvaluationJob instance.
        """
        job = EvaluationJob(
            id=uuid4(),
            company_id=company_id,
            status=EvaluationStatus.PENDING.value,
            total_queries=0,
            config_snapshot=config_snapshot,
        )
        
        if self._save_to_db:
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        
        return job
    
    def update_job_status(
        self,
        job_id: UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[EvaluationJob]:
        """Update the status of an evaluation job.
        
        Args:
            job_id: UUID of the job to update.
            status: New status value.
            error_message: Optional error message if failed.
        
        Returns:
            Updated EvaluationJob instance.
        """
        if not self._save_to_db:
            return None
        
        statement = select(EvaluationJob).where(EvaluationJob.id == job_id)
        result = self.session.exec(statement)
        job = result.first()
        
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        
        return job
    
    def start_job(self, job_id: UUID) -> Optional[EvaluationJob]:
        """Mark a job as running.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            Updated EvaluationJob instance.
        """
        if not self._save_to_db:
            return None
        
        statement = select(EvaluationJob).where(EvaluationJob.id == job_id)
        result = self.session.exec(statement)
        job = result.first()
        
        if job:
            job.status = EvaluationStatus.RUNNING.value
            job.started_at = datetime.utcnow()
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        
        return job
    
    def save_single_result(
        self,
        job_id: Optional[UUID],
        result: EvaluationResult,
    ) -> Optional[EvaluationResultModel]:
        """Save a single evaluation result to the database.
        
        Args:
            job_id: Optional job ID (None for real-time evaluations).
            result: EvaluationResult to save.
        
        Returns:
            Created database record.
        """
        if not self._save_to_db:
            return None
        
        db_result = EvaluationResultModel(
            id=result.id or uuid4(),
            job_id=job_id,
            chat_message_id=result.chat_message_id,
            company_id=result.company_id,
            question=result.question,
            retrieved_contexts=result.retrieved_contexts,
            answer=result.answer,
            faithfulness_score=result.faithfulness_score,
            answer_relevance_score=result.answer_relevance_score,
            context_precision_score=result.context_precision_score,
            overall_score=result.overall_score,
            evaluation_metadata=result.evaluation_metadata,
            created_at=result.created_at or datetime.utcnow(),
        )
        
        self.session.add(db_result)
        self.session.commit()
        self.session.refresh(db_result)
        
        return db_result
    
    def save_job_summary(
        self,
        job_id: UUID,
        summary: AggregatedSummary,
    ) -> Optional[EvaluationJob]:
        """Update job with aggregated scores.
        
        Args:
            job_id: UUID of the job to update.
            summary: AggregatedSummary with computed scores.
        
        Returns:
            Updated EvaluationJob instance.
        """
        if not self._save_to_db:
            return None
        
        statement = select(EvaluationJob).where(EvaluationJob.id == job_id)
        result = self.session.exec(statement)
        job = result.first()
        
        if job:
            job.status = EvaluationStatus.COMPLETED.value
            job.total_queries = summary.total_queries
            job.avg_faithfulness = summary.faithfulness.mean if summary.faithfulness else None
            job.avg_answer_relevance = summary.answer_relevance.mean if summary.answer_relevance else None
            job.avg_context_precision = summary.context_precision.mean if summary.context_precision else None
            job.overall_score = summary.overall_score
            job.completed_at = datetime.utcnow()
            
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        
        return job
    
    def save_to_json(
        self,
        job_id: UUID,
        results: List[EvaluationResult],
        summary: AggregatedSummary,
    ) -> str:
        """Save results to JSON file.
        
        Args:
            job_id: UUID of the job.
            results: List of evaluation results.
            summary: Aggregated summary.
        
        Returns:
            Path to the created JSON file.
        """
        if not self._save_to_json:
            return ""
        
        # Prepare output data
        output_data = {
            "job_id": str(job_id),
            "summary": summary.model_dump(),
            "results": [r.model_dump() for r in results],
        }
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{job_id}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Write to file
        with open(filepath, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        
        return filepath
    
    def get_job_results(self, job_id: UUID) -> List[EvaluationResultModel]:
        """Retrieve all results for a job.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            List of EvaluationResultModel records.
        """
        statement = (
            select(EvaluationResultModel)
            .where(EvaluationResultModel.job_id == job_id)
            .order_by(EvaluationResultModel.created_at)
        )
        result = self.session.exec(statement)
        return list(result.all())
    
    def get_job(self, job_id: UUID) -> Optional[EvaluationJob]:
        """Get a job by ID.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            EvaluationJob if found, None otherwise.
        """
        statement = select(EvaluationJob).where(EvaluationJob.id == job_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_company_evaluation_history(
        self,
        company_id: UUID,
        limit: int = 10,
    ) -> List[EvaluationJob]:
        """Get evaluation history for a company.
        
        Args:
            company_id: UUID of the company.
            limit: Maximum number of jobs to return.
        
        Returns:
            List of EvaluationJob records, most recent first.
        """
        statement = (
            select(EvaluationJob)
            .where(EvaluationJob.company_id == company_id)
            .order_by(EvaluationJob.created_at.desc())
            .limit(limit)
        )
        result = self.session.exec(statement)
        return list(result.all())
    
    def get_latest_job(self, company_id: Optional[UUID] = None) -> Optional[EvaluationJob]:
        """Get the most recent evaluation job.
        
        Args:
            company_id: Optional company ID to filter by.
        
        Returns:
            Most recent EvaluationJob if any, None otherwise.
        """
        statement = select(EvaluationJob)
        
        if company_id:
            statement = statement.where(EvaluationJob.company_id == company_id)
        
        statement = statement.order_by(EvaluationJob.created_at.desc()).limit(1)
        result = self.session.exec(statement)
        return result.first()
    
    def compute_aggregated_summary(
        self,
        results: List[EvaluationResult],
        job_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
    ) -> AggregatedSummary:
        """Compute aggregated summary from results.
        
        Args:
            results: List of EvaluationResult objects.
            job_id: Optional job ID.
            company_id: Optional company ID.
        
        Returns:
            AggregatedSummary with computed statistics.
        """
        import statistics
        
        if not results:
            return AggregatedSummary(
                job_id=job_id,
                company_id=company_id,
                total_queries=0,
            )
        
        # Extract scores for each metric
        faithfulness_scores = [
            r.faithfulness_score for r in results 
            if r.faithfulness_score is not None
        ]
        answer_relevance_scores = [
            r.answer_relevance_score for r in results 
            if r.answer_relevance_score is not None
        ]
        context_precision_scores = [
            r.context_precision_score for r in results 
            if r.context_precision_score is not None
        ]
        overall_scores = [
            r.overall_score for r in results 
            if r.overall_score is not None
        ]
        
        def compute_distribution(scores: List[float]) -> Dict[str, int]:
            """Compute distribution of scores in ranges."""
            distribution = {
                "0.0-0.2": 0,
                "0.2-0.4": 0,
                "0.4-0.6": 0,
                "0.6-0.8": 0,
                "0.8-1.0": 0,
            }
            for score in scores:
                if score < 0.2:
                    distribution["0.0-0.2"] += 1
                elif score < 0.4:
                    distribution["0.2-0.4"] += 1
                elif score < 0.6:
                    distribution["0.4-0.6"] += 1
                elif score < 0.8:
                    distribution["0.6-0.8"] += 1
                else:
                    distribution["0.8-1.0"] += 1
            return distribution
        
        def compute_metric_distribution(scores: List[float]) -> Optional[MetricDistribution]:
            """Compute distribution for a metric."""
            if not scores:
                return None
            
            return MetricDistribution(
                mean=statistics.mean(scores),
                median=statistics.median(scores),
                std=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                min=min(scores),
                max=max(scores),
                count=len(scores),
                distribution=compute_distribution(scores),
            )
        
        return AggregatedSummary(
            job_id=job_id,
            company_id=company_id,
            total_queries=len(results),
            faithfulness=compute_metric_distribution(faithfulness_scores),
            answer_relevance=compute_metric_distribution(answer_relevance_scores),
            context_precision=compute_metric_distribution(context_precision_scores),
            overall_score=statistics.mean(overall_scores) if overall_scores else None,
        )
