"""Core evaluation logic for single query RAGAS evaluation.

This module provides the SingleQueryEvaluator class that evaluates
individual queries using RAGAS metrics. It is designed to be used
both in batch mode and for real-time per-query evaluation.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from evaluations.config import EvaluationConfig, MetricType
from evaluations.schemas import EvaluationInput, EvaluationResult


class SingleQueryEvaluator:
    """Evaluates single queries using RAGAS metrics.
    
    This class provides the core evaluation logic that can be used:
    - In batch mode via BatchEvaluationRunner
    - Directly for real-time per-query evaluation
    
    The evaluator uses RAGAS metrics with OpenAI models for LLM-based
    evaluation of RAG system outputs.
    
    Attributes:
        config: Evaluation configuration.
        llm: LangChain LLM instance for evaluation.
        embeddings: LangChain embeddings for context precision.
    """
    
    def __init__(self, config: EvaluationConfig):
        """Initialize the evaluator with configuration.
        
        Args:
            config: EvaluationConfig instance with LLM and metric settings.
        """
        self.config = config
        self._llm = None
        self._embeddings = None
        self._metrics = None
    
    @classmethod
    def from_env(cls) -> "SingleQueryEvaluator":
        """Create evaluator from environment variables.
        
        Returns:
            SingleQueryEvaluator with config from environment.
        """
        return cls(EvaluationConfig.from_env())
    
    @classmethod
    def for_company(cls, company_config: Dict[str, Any]) -> "SingleQueryEvaluator":
        """Create evaluator with company-specific settings.
        
        Args:
            company_config: Dictionary with company's LLM configuration.
        
        Returns:
            SingleQueryEvaluator with company-specific config.
        """
        return cls(EvaluationConfig.for_company(company_config))
    
    @property
    def llm(self):
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    @property
    def embeddings(self):
        """Lazy-load the embeddings instance."""
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings
    
    @property
    def metrics(self):
        """Lazy-load the RAGAS metrics."""
        if self._metrics is None:
            self._metrics = self._create_metrics()
        return self._metrics
    
    def _create_llm(self):
        """Create the LLM instance based on configuration."""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
            api_key=self.config.openai_api_key,
        )
    
    def _create_embeddings(self):
        """Create the embeddings instance."""
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            api_key=self.config.openai_api_key,
        )
    
    def _create_metrics(self) -> List:
        """Create RAGAS metrics based on configuration.
        
        Returns:
            List of RAGAS metric instances.
        """
        from ragas.metrics import _Faithfulness, _AnswerRelevancy, _LLMContextPrecisionWithoutReference
        
        metrics_map = {
            MetricType.FAITHFULNESS.value: _Faithfulness(),
            MetricType.ANSWER_RELEVANCE.value: _AnswerRelevancy(),
            MetricType.CONTEXT_PRECISION.value: _LLMContextPrecisionWithoutReference(),
        }
        
        selected_metrics = []
        for metric_name in self.config.metrics:
            if metric_name in metrics_map:
                selected_metrics.append(metrics_map[metric_name])
        
        return selected_metrics
    
    def evaluate_single(
        self,
        question: str,
        retrieved_contexts: List[str],
        answer: str,
        ground_truth: Optional[str] = None,
        chat_message_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> EvaluationResult:
        """Evaluate a single query using RAGAS metrics.
        
        This is the main entry point for per-query evaluation.
        Can be called directly for real-time evaluation.
        
        Args:
            question: The user's query.
            retrieved_contexts: List of retrieved document contents.
            answer: The generated response.
            ground_truth: Expected answer (optional, for some metrics).
            chat_message_id: Reference to the original ChatMessage.
            company_id: Company ID for scoping.
        
        Returns:
            EvaluationResult with all metric scores.
        
        Example:
            >>> evaluator = SingleQueryEvaluator.from_env()
            >>> result = evaluator.evaluate_single(
            ...     question="What is the revenue?",
            ...     retrieved_contexts=["Revenue was $10M in Q1."],
            ...     answer="The revenue was $10 million in Q1."
            ... )
            >>> print(result.faithfulness_score)
            0.85
        """
        # Run async evaluation in sync context
        return asyncio.run(self.evaluate_single_async(
            question=question,
            retrieved_contexts=retrieved_contexts,
            answer=answer,
            ground_truth=ground_truth,
            chat_message_id=chat_message_id,
            company_id=company_id,
        ))
    
    async def evaluate_single_async(
        self,
        question: str,
        retrieved_contexts: List[str],
        answer: str,
        ground_truth: Optional[str] = None,
        chat_message_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> EvaluationResult:
        """Async version of evaluate_single.
        
        Use this when integrating with async code (e.g., FastAPI endpoints).
        
        Args:
            question: The user's query.
            retrieved_contexts: List of retrieved document contents.
            answer: The generated response.
            ground_truth: Expected answer (optional).
            chat_message_id: Reference to the original ChatMessage.
            company_id: Company ID for scoping.
        
        Returns:
            EvaluationResult with all metric scores.
        """
        from ragas import evaluate
        from datasets import Dataset
        
        # Prepare data for RAGAS (0.4.x uses new column names)
        data = {
            "user_input": [question],
            "retrieved_contexts": [retrieved_contexts],
            "response": [answer],
        }
        
        # Add ground truth (reference) if provided
        if ground_truth:
            data["reference"] = [ground_truth]
        
        dataset = Dataset.from_dict(data)
        
        # Run evaluation
        try:
            results = evaluate(
                dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )
            
            # Extract scores
            scores = results.to_pandas().iloc[0].to_dict()
            
            # Create result object
            result = EvaluationResult(
                id=uuid4(),
                chat_message_id=chat_message_id,
                company_id=company_id,
                question=question,
                retrieved_contexts=retrieved_contexts,
                answer=answer,
                faithfulness_score=scores.get("faithfulness"),
                answer_relevance_score=scores.get("answer_relevancy"),  # RAGAS 0.4.x uses 'answer_relevancy'
                context_precision_score=scores.get("llm_context_precision_without_reference"),  # RAGAS 0.4.x
                created_at=datetime.utcnow(),
            )
            
            # Calculate overall score
            result.overall_score = result.calculate_overall_score()
            
            return result
            
        except Exception as e:
            # Return result with error info
            return EvaluationResult(
                id=uuid4(),
                chat_message_id=chat_message_id,
                company_id=company_id,
                question=question,
                retrieved_contexts=retrieved_contexts,
                answer=answer,
                evaluation_metadata={"error": str(e)},
                created_at=datetime.utcnow(),
            )
    
    def evaluate_input(self, input_data: EvaluationInput) -> EvaluationResult:
        """Evaluate an EvaluationInput object.
        
        Convenience method that accepts an EvaluationInput directly.
        
        Args:
            input_data: EvaluationInput containing query data.
        
        Returns:
            EvaluationResult with all metric scores.
        """
        return self.evaluate_single(
            question=input_data.question,
            retrieved_contexts=input_data.retrieved_contexts,
            answer=input_data.answer,
            ground_truth=input_data.ground_truth,
            chat_message_id=str(input_data.chat_message_id) if input_data.chat_message_id else None,
            company_id=str(input_data.company_id) if input_data.company_id else None,
        )
    
    async def evaluate_input_async(self, input_data: EvaluationInput) -> EvaluationResult:
        """Async version of evaluate_input.
        
        Args:
            input_data: EvaluationInput containing query data.
        
        Returns:
            EvaluationResult with all metric scores.
        """
        return await self.evaluate_single_async(
            question=input_data.question,
            retrieved_contexts=input_data.retrieved_contexts,
            answer=input_data.answer,
            ground_truth=input_data.ground_truth,
            chat_message_id=str(input_data.chat_message_id) if input_data.chat_message_id else None,
            company_id=str(input_data.company_id) if input_data.company_id else None,
        )
    
    def check_threshold(
        self,
        result: EvaluationResult,
        metric: str
    ) -> Optional[bool]:
        """Check if a metric score meets the threshold.
        
        Args:
            result: EvaluationResult to check.
            metric: Metric name to check.
        
        Returns:
            True if score meets threshold, False if not, None if score unavailable.
        """
        score = getattr(result, f"{metric}_score", None)
        if score is None:
            return None
        
        threshold = self.config.thresholds.get(metric, 0.7)
        return score >= threshold
    
    def get_pass_fail_summary(self, result: EvaluationResult) -> Dict[str, Optional[bool]]:
        """Get pass/fail status for all metrics.
        
        Args:
            result: EvaluationResult to check.
        
        Returns:
            Dictionary mapping metric names to pass/fail status.
        """
        return {
            metric: self.check_threshold(result, metric)
            for metric in self.config.metrics
        }
