"""Pydantic schemas for evaluation pipeline.

This module defines the data structures used throughout the evaluation
pipeline, including inputs, outputs, and aggregated summaries.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class EvaluationInput(BaseModel):
    """Input data for a single evaluation.
    
    This represents the data needed to evaluate a single query,
    typically extracted from a ChatMessage record.
    """
    question: str = Field(..., description="The user's query")
    retrieved_contexts: List[str] = Field(
        default_factory=list,
        description="List of retrieved document contents"
    )
    answer: str = Field(..., description="The generated response")
    ground_truth: Optional[str] = Field(
        default=None,
        description="Expected answer (optional, for some metrics)"
    )
    chat_message_id: Optional[UUID] = Field(
        default=None,
        description="Reference to the original ChatMessage"
    )
    company_id: Optional[UUID] = Field(
        default=None,
        description="Company ID for scoping"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class MetricDistribution(BaseModel):
    """Distribution of scores for a single metric.
    
    Used in aggregated summaries to show how scores are distributed
    across different ranges.
    """
    mean: float = Field(..., description="Mean score")
    median: float = Field(..., description="Median score")
    std: float = Field(..., description="Standard deviation")
    min: float = Field(..., description="Minimum score")
    max: float = Field(..., description="Maximum score")
    count: int = Field(..., description="Number of data points")
    distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of scores in each range (0.0-0.2, 0.2-0.4, etc.)"
    )


class EvaluationResult(BaseModel):
    """Result of evaluating a single query.
    
    Contains all metric scores and the original input data.
    """
    id: Optional[UUID] = Field(default=None, description="Result ID")
    job_id: Optional[UUID] = Field(default=None, description="Job ID (null for real-time)")
    chat_message_id: Optional[UUID] = Field(default=None, description="Original message ID")
    company_id: Optional[UUID] = Field(default=None, description="Company ID")
    
    # Input data
    question: str = Field(..., description="The user's query")
    retrieved_contexts: List[str] = Field(
        default_factory=list,
        description="Retrieved document contents"
    )
    answer: str = Field(..., description="The generated response")
    
    # Metric scores
    faithfulness_score: Optional[float] = Field(
        default=None,
        description="Faithfulness metric score (0-1)"
    )
    answer_relevance_score: Optional[float] = Field(
        default=None,
        description="Answer relevance metric score (0-1)"
    )
    context_precision_score: Optional[float] = Field(
        default=None,
        description="Context precision metric score (0-1)"
    )
    
    # Overall score
    overall_score: Optional[float] = Field(
        default=None,
        description="Average of available metric scores"
    )
    
    # Metadata
    evaluation_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional evaluation metadata"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="When the evaluation was performed"
    )
    
    def calculate_overall_score(self) -> Optional[float]:
        """Calculate overall score as average of available metrics."""
        scores = [
            s for s in [
                self.faithfulness_score,
                self.answer_relevance_score,
                self.context_precision_score,
            ]
            if s is not None
        ]
        if scores:
            return sum(scores) / len(scores)
        return None


class AggregatedSummary(BaseModel):
    """Aggregated summary of evaluation results.
    
    Contains statistics for each metric across all evaluated queries.
    """
    job_id: Optional[UUID] = Field(default=None, description="Job ID")
    company_id: Optional[UUID] = Field(default=None, description="Company ID")
    status: str = Field(default="completed", description="Job status")
    total_queries: int = Field(..., description="Total number of queries evaluated")
    
    # Metric distributions
    faithfulness: Optional[MetricDistribution] = Field(
        default=None,
        description="Faithfulness score distribution"
    )
    answer_relevance: Optional[MetricDistribution] = Field(
        default=None,
        description="Answer relevance score distribution"
    )
    context_precision: Optional[MetricDistribution] = Field(
        default=None,
        description="Context precision score distribution"
    )
    
    # Overall scores
    overall_score: Optional[float] = Field(
        default=None,
        description="Average overall score across all queries"
    )
    
    # Timestamps
    started_at: Optional[datetime] = Field(default=None, description="When evaluation started")
    completed_at: Optional[datetime] = Field(default=None, description="When evaluation completed")
    
    def get_avg_scores(self) -> Dict[str, Optional[float]]:
        """Get average scores for each metric."""
        return {
            "faithfulness": self.faithfulness.mean if self.faithfulness else None,
            "answer_relevance": self.answer_relevance.mean if self.answer_relevance else None,
            "context_precision": self.context_precision.mean if self.context_precision else None,
        }


class EvaluationJobResult(BaseModel):
    """Complete result of a batch evaluation job.
    
    Contains the job metadata, all individual results, and the aggregated summary.
    """
    job_id: UUID = Field(..., description="Job ID")
    company_id: Optional[UUID] = Field(default=None, description="Company ID")
    status: str = Field(..., description="Job status")
    total_queries: int = Field(..., description="Total queries evaluated")
    
    # Aggregated scores
    avg_faithfulness: Optional[float] = Field(default=None)
    avg_answer_relevance: Optional[float] = Field(default=None)
    avg_context_precision: Optional[float] = Field(default=None)
    overall_score: Optional[float] = Field(default=None)
    
    # Timestamps
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Error info
    error_message: Optional[str] = Field(default=None)
    
    # Detailed results (optional, for full export)
    results: Optional[List[EvaluationResult]] = Field(
        default=None,
        description="Individual query results"
    )
    
    @classmethod
    def from_summary(
        cls,
        job_id: UUID,
        summary: AggregatedSummary,
        results: Optional[List[EvaluationResult]] = None
    ) -> "EvaluationJobResult":
        """Create job result from aggregated summary."""
        return cls(
            job_id=job_id,
            company_id=summary.company_id,
            status=summary.status,
            total_queries=summary.total_queries,
            avg_faithfulness=summary.faithfulness.mean if summary.faithfulness else None,
            avg_answer_relevance=summary.answer_relevance.mean if summary.answer_relevance else None,
            avg_context_precision=summary.context_precision.mean if summary.context_precision else None,
            overall_score=summary.overall_score,
            started_at=summary.started_at,
            completed_at=summary.completed_at,
            results=results,
        )


class EvaluationRequest(BaseModel):
    """Request to run an evaluation job.
    
    Used for API endpoints to trigger evaluations.
    """
    company_id: Optional[UUID] = Field(
        default=None,
        description="Company ID to evaluate"
    )
    chat_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Specific chat IDs to evaluate"
    )
    user_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Specific user IDs to evaluate"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date for messages"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date for messages"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of messages to evaluate"
    )
    config_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override default configuration"
    )


class SingleEvaluationRequest(BaseModel):
    """Request to evaluate a single query.
    
    Used for real-time evaluation after a user query.
    """
    question: str = Field(..., description="The user's query")
    retrieved_contexts: List[str] = Field(
        default_factory=list,
        description="Retrieved document contents"
    )
    answer: str = Field(..., description="The generated response")
    ground_truth: Optional[str] = Field(
        default=None,
        description="Expected answer (optional)"
    )
    chat_message_id: Optional[UUID] = Field(
        default=None,
        description="Reference to the original ChatMessage"
    )
    company_id: Optional[UUID] = Field(
        default=None,
        description="Company ID for scoping"
    )
