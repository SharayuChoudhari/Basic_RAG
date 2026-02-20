"""Batch evaluation runner for RAGAS pipeline.

This module provides the BatchEvaluationRunner class that orchestrates
batch evaluation runs, using SingleQueryEvaluator for each query and
MetricsStore for persistence.
"""

import asyncio
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlmodel import Session

from evaluations.config import EvaluationConfig, EvaluationStatus
from evaluations.dataset_loader import DatasetLoader
from evaluations.single_eval import SingleQueryEvaluator
from evaluations.metrics_store import MetricsStore
from evaluations.schemas import (
    EvaluationInput,
    EvaluationResult,
    AggregatedSummary,
    EvaluationJobResult,
)


class BatchEvaluationRunner:
    """Orchestrates batch evaluation runs.
    
    This class coordinates the batch evaluation process:
    1. Creates an EvaluationJob record
    2. Loads messages via DatasetLoader
    3. Evaluates each using SingleQueryEvaluator
    4. Stores results via MetricsStore
    5. Updates job with aggregated scores
    
    The runner internally reuses SingleQueryEvaluator for each query,
    enabling both batch and real-time evaluation modes.
    
    Attributes:
        session: SQLModel database session.
        config: Evaluation configuration.
        dataset_loader: Loader for evaluation data.
        single_evaluator: Evaluator for individual queries.
        metrics_store: Storage for results.
    """
    
    def __init__(
        self,
        session: Session,
        config: Optional[EvaluationConfig] = None,
    ):
        """Initialize the batch runner.
        
        Args:
            session: SQLModel database session.
            config: Optional EvaluationConfig. Uses default if not provided.
        """
        self.session = session
        self.config = config or EvaluationConfig.from_env()
        self.dataset_loader: Optional[DatasetLoader] = None
        self.single_evaluator = SingleQueryEvaluator(self.config)
        self.metrics_store = MetricsStore.from_config(session, self.config)
    
    def run_evaluation(
        self,
        company_id: Optional[UUID] = None,
        chat_ids: Optional[List[UUID]] = None,
        user_ids: Optional[List[UUID]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> EvaluationJobResult:
        """Run batch evaluation for specified messages.
        
        This is the main entry point for batch evaluation.
        
        Args:
            company_id: Optional company ID to filter messages.
            chat_ids: Optional list of chat IDs to evaluate.
            user_ids: Optional list of user IDs to evaluate.
            start_time: Start of date range for messages. If days is provided,
                       calculated as end_time - days.
            end_time: End of date range for messages. Defaults to now.
            days: Number of days to look back from end_time. If provided,
                  start_time is calculated automatically.
            limit: Optional maximum number of messages to evaluate.
            dry_run: If True, don't save results to database.
        
        Returns:
            EvaluationJobResult with aggregated scores.
        
        Example:
            >>> runner = BatchEvaluationRunner(session)
            >>> # Evaluate last 7 days
            >>> result = runner.run_evaluation(
            ...     company_id=company_uuid,
            ...     days=7
            ... )
            >>> print(f"Overall score: {result.overall_score}")
        """
        return asyncio.run(self.run_evaluation_async(
            company_id=company_id,
            chat_ids=chat_ids,
            user_ids=user_ids,
            start_time=start_time,
            end_time=end_time,
            days=days,
            limit=limit,
            dry_run=dry_run,
        ))
    
    async def run_evaluation_async(
        self,
        company_id: Optional[UUID] = None,
        chat_ids: Optional[List[UUID]] = None,
        user_ids: Optional[List[UUID]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> EvaluationJobResult:
        """Async version of run_evaluation.
        
        Use this when integrating with async code.
        
        Args:
            company_id: Optional company ID to filter messages.
            chat_ids: Optional list of chat IDs to evaluate.
            user_ids: Optional list of user IDs to evaluate.
            start_time: Start of date range for messages.
            end_time: End of date range for messages. Defaults to now.
            days: Number of days to look back from end_time.
            limit: Optional maximum number of messages to evaluate.
            dry_run: If True, don't save results to database.
        
        Returns:
            EvaluationJobResult with aggregated scores.
        """
        # Calculate date range from parameters
        date_range = self._calculate_date_range(
            start_time=start_time,
            end_time=end_time,
            days=days,
        )
        
        # Initialize dataset loader with company filter
        self.dataset_loader = DatasetLoader(self.session, company_id)
        
        # Create job record
        job = self.metrics_store.create_job(
            company_id=company_id,
            config_snapshot=self.config.to_dict(),
        )
        job_id = job.id
        
        try:
            # Mark job as running
            self.metrics_store.start_job(job_id)
            
            # Load messages to evaluate
            inputs = self.dataset_loader.load_messages(
                chat_ids=chat_ids,
                user_ids=user_ids,
                date_range=date_range,
                limit=limit,
            )
            
            if not inputs:
                # No messages to evaluate
                summary = AggregatedSummary(
                    job_id=job_id,
                    company_id=company_id,
                    total_queries=0,
                )
                self.metrics_store.save_job_summary(job_id, summary)
                return EvaluationJobResult.from_summary(job_id, summary)
            
            # Evaluate each query
            results = await self._evaluate_batch(inputs, job_id, dry_run)
            
            # Compute aggregated summary
            summary = self.metrics_store.compute_aggregated_summary(
                results,
                job_id=job_id,
                company_id=company_id,
            )
            
            # Save summary
            if not dry_run:
                self.metrics_store.save_job_summary(job_id, summary)
                self.metrics_store.save_to_json(job_id, results, summary)
            
            return EvaluationJobResult.from_summary(job_id, summary, results)
            
        except Exception as e:
            # Mark job as failed
            self.metrics_store.update_job_status(
                job_id,
                EvaluationStatus.FAILED.value,
                error_message=str(e),
            )
            raise
    
    async def _evaluate_batch(
        self,
        inputs: List[EvaluationInput],
        job_id: UUID,
        dry_run: bool = False,
    ) -> List[EvaluationResult]:
        """Evaluate a batch of inputs.
        
        Processes inputs in batches based on config.batch_size.
        
        Args:
            inputs: List of EvaluationInput to evaluate.
            job_id: UUID of the current job.
            dry_run: If True, don't save individual results.
        
        Returns:
            List of EvaluationResult objects.
        """
        results = []
        batch_size = self.config.batch_size
        
        # Process in batches
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            batch_results = await self._process_batch(batch, job_id, dry_run)
            results.extend(batch_results)
        
        return results
    
    async def _process_batch(
        self,
        batch: List[EvaluationInput],
        job_id: UUID,
        dry_run: bool = False,
    ) -> List[EvaluationResult]:
        """Process a single batch of inputs.
        
        Args:
            batch: List of EvaluationInput to evaluate.
            job_id: UUID of the current job.
            dry_run: If True, don't save individual results.
        
        Returns:
            List of EvaluationResult objects.
        """
        results = []
        
        for input_data in batch:
            try:
                # Evaluate single query
                result = await self.single_evaluator.evaluate_input_async(input_data)
                
                # Save to database
                if not dry_run:
                    self.metrics_store.save_single_result(job_id, result)
                
                results.append(result)
                
            except Exception as e:
                # Create error result
                error_result = EvaluationResult(
                    question=input_data.question,
                    retrieved_contexts=input_data.retrieved_contexts,
                    answer=input_data.answer,
                    evaluation_metadata={"error": str(e)},
                )
                results.append(error_result)
        
        return results
    
    def _calculate_date_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        days: Optional[int] = None,
    ) -> Optional[Tuple[datetime, datetime]]:
        """Calculate date range from parameters.
        
        Priority:
        1. If days is provided: start_time = end_time - days, end_time defaults to now
        2. If start_time and end_time are provided: use them directly
        3. If only start_time is provided: end_time defaults to now
        4. If only end_time is provided: start_time is None (no lower bound)
        5. If nothing is provided: return None (no date filter)
        
        Args:
            start_time: Start of date range.
            end_time: End of date range. Defaults to now.
            days: Number of days to look back from end_time.
        
        Returns:
            Tuple of (start_time, end_time) or None if no filter.
        """
        # Default end_time to now if not provided
        if end_time is None:
            end_time = datetime.utcnow()
        
        # If days is provided, calculate start_time
        if days is not None:
            start_time = end_time - timedelta(days=days)
            return (start_time, end_time)
        
        # If start_time is provided, use it with end_time
        if start_time is not None:
            return (start_time, end_time)
        
        # If only end_time was explicitly set (and we defaulted it), no filter
        # But if user explicitly wants to filter from beginning of time to end_time,
        # they should use days=36500 (100 years) or similar
        return None
    
    def preview_evaluation(
        self,
        company_id: Optional[UUID] = None,
        chat_ids: Optional[List[UUID]] = None,
        user_ids: Optional[List[UUID]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Preview what would be evaluated without running.
        
        Useful for confirming scope before running a large evaluation.
        
        Args:
            company_id: Optional company ID to filter messages.
            chat_ids: Optional list of chat IDs.
            user_ids: Optional list of user IDs.
            start_time: Start of date range.
            end_time: End of date range. Defaults to now.
            days: Number of days to look back from end_time.
        
        Returns:
            Dictionary with preview information.
        """
        # Calculate date range
        date_range = self._calculate_date_range(
            start_time=start_time,
            end_time=end_time,
            days=days,
        )
        
        loader = DatasetLoader(self.session, company_id)
        
        count = loader.get_message_count(
            chat_ids=chat_ids,
            user_ids=user_ids,
            date_range=date_range,
        )
        
        return {
            "message_count": count,
            "company_id": str(company_id) if company_id else None,
            "filters": {
                "chat_ids": [str(cid) for cid in chat_ids] if chat_ids else None,
                "user_ids": [str(uid) for uid in user_ids] if user_ids else None,
                "start_time": date_range[0].isoformat() if date_range else None,
                "end_time": date_range[1].isoformat() if date_range else None,
                "days": days,
            },
            "config": self.config.to_dict(),
        }
    
    def get_evaluation_history(
        self,
        company_id: UUID,
        limit: int = 10,
    ) -> List[EvaluationJobResult]:
        """Get evaluation history for a company.
        
        Args:
            company_id: UUID of the company.
            limit: Maximum number of jobs to return.
        
        Returns:
            List of EvaluationJobResult objects.
        """
        jobs = self.metrics_store.get_company_evaluation_history(
            company_id,
            limit=limit,
        )
        
        return [
            EvaluationJobResult(
                job_id=job.id,
                company_id=job.company_id,
                status=job.status,
                total_queries=job.total_queries,
                avg_faithfulness=job.avg_faithfulness,
                avg_answer_relevance=job.avg_answer_relevance,
                avg_context_precision=job.avg_context_precision,
                overall_score=job.overall_score,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
            )
            for job in jobs
        ]
    
    def get_job_details(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about a job.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            Dictionary with job details and results, or None if not found.
        """
        job = self.metrics_store.get_job(job_id)
        if not job:
            return None
        
        results = self.metrics_store.get_job_results(job_id)
        
        return {
            "job": EvaluationJobResult(
                job_id=job.id,
                company_id=job.company_id,
                status=job.status,
                total_queries=job.total_queries,
                avg_faithfulness=job.avg_faithfulness,
                avg_answer_relevance=job.avg_answer_relevance,
                avg_context_precision=job.avg_context_precision,
                overall_score=job.overall_score,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
            ),
            "results": [
                EvaluationResult(
                    id=r.id,
                    job_id=r.job_id,
                    chat_message_id=r.chat_message_id,
                    company_id=r.company_id,
                    question=r.question,
                    retrieved_contexts=r.retrieved_contexts or [],
                    answer=r.answer,
                    faithfulness_score=r.faithfulness_score,
                    answer_relevance_score=r.answer_relevance_score,
                    context_precision_score=r.context_precision_score,
                    overall_score=r.overall_score,
                    evaluation_metadata=r.evaluation_metadata,
                    created_at=r.created_at,
                )
                for r in results
            ],
        }
