#!/usr/bin/env python
"""CLI entry point for running RAGAS evaluations.

This script provides a command-line interface for running batch
evaluations on the RAG system.

Usage:
    python -m evaluations.run_evaluations --company-id <uuid>
    python -m evaluations.run_evaluations --company-id <uuid> --days 7
    python -m evaluations.run_evaluations --company-id <uuid> --chat-ids <uuid1> <uuid2>
    python -m evaluations.run_evaluations --company-id <uuid> --from-date 2024-01-01 --to-date 2024-01-31
    python -m evaluations.run_evaluations --company-id <uuid> --dry-run
    python -m evaluations.run_evaluations --preview --company-id <uuid>
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from layers.database import get_db_session
from evaluations.config import EvaluationConfig
from evaluations.batch_runner import BatchEvaluationRunner
from evaluations.single_eval import SingleQueryEvaluator


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run RAGAS evaluations on RAG system queries.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run evaluation for a company (last 7 days by default)
  python -m evaluations.run_evaluations --company-id 123e4567-e89b-12d3-a456-426614174000

  # Run for last 30 days
  python -m evaluations.run_evaluations --company-id <uuid> --days 30

  # Run for specific chats
  python -m evaluations.run_evaluations --company-id <uuid> --chat-ids <uuid1> <uuid2>

  # Run for date range
  python -m evaluations.run_evaluations --company-id <uuid> --from-date 2024-01-01 --to-date 2024-01-31

  # Preview without running
  python -m evaluations.run_evaluations --preview --company-id <uuid>

  # Dry run (no database save)
  python -m evaluations.run_evaluations --company-id <uuid> --dry-run
        """,
    )
    
    # Required arguments
    parser.add_argument(
        "--company-id",
        type=str,
        help="Company UUID to evaluate",
    )
    
    # Filter options
    parser.add_argument(
        "--chat-ids",
        nargs="+",
        type=str,
        help="Specific chat UUIDs to evaluate",
    )
    parser.add_argument(
        "--user-ids",
        nargs="+",
        type=str,
        help="Specific user UUIDs to evaluate",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back from now (default: 7). Use --days 0 for all time.",
    )
    parser.add_argument(
        "--from-date",
        type=str,
        help="Start date (YYYY-MM-DD). Overrides --days if provided.",
    )
    parser.add_argument(
        "--to-date",
        type=str,
        help="End date (YYYY-MM-DD). Defaults to now.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of messages to evaluate",
    )
    
    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving to database",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview what would be evaluated without running",
    )
    
    # Configuration options
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="LLM model to use for evaluation (default: gpt-4)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluations/results",
        help="Output directory for JSON results",
    )
    
    # Single query evaluation
    parser.add_argument(
        "--single",
        action="store_true",
        help="Evaluate a single query (requires --question, --answer, --contexts)",
    )
    parser.add_argument(
        "--question",
        type=str,
        help="Question for single query evaluation",
    )
    parser.add_argument(
        "--answer",
        type=str,
        help="Answer for single query evaluation",
    )
    parser.add_argument(
        "--contexts",
        nargs="+",
        type=str,
        help="Context documents for single query evaluation",
    )
    
    return parser.parse_args()


def validate_uuid(value: str, name: str) -> UUID:
    """Validate and convert string to UUID."""
    try:
        return UUID(value)
    except ValueError:
        print(f"Error: Invalid UUID for {name}: {value}")
        sys.exit(1)


def parse_date(value: str, name: str) -> datetime:
    """Parse date string to datetime."""
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format for {name}: {value}. Use YYYY-MM-DD.")
        sys.exit(1)


def run_single_evaluation(args: argparse.Namespace) -> None:
    """Run evaluation for a single query."""
    if not args.question or not args.answer:
        print("Error: --single requires --question and --answer")
        sys.exit(1)
    
    contexts = args.contexts or []
    
    print("Running single query evaluation...")
    print(f"Question: {args.question}")
    print(f"Answer: {args.answer}")
    print(f"Contexts: {len(contexts)} documents")
    print()
    
    evaluator = SingleQueryEvaluator.from_env()
    result = evaluator.evaluate_single(
        question=args.question,
        retrieved_contexts=contexts,
        answer=args.answer,
    )
    
    print("Evaluation Results:")
    print(f"  Faithfulness: {result.faithfulness_score:.4f}" if result.faithfulness_score else "  Faithfulness: N/A")
    print(f"  Answer Relevance: {result.answer_relevance_score:.4f}" if result.answer_relevance_score else "  Answer Relevance: N/A")
    print(f"  Context Precision: {result.context_precision_score:.4f}" if result.context_precision_score else "  Context Precision: N/A")
    print(f"  Overall Score: {result.overall_score:.4f}" if result.overall_score else "  Overall Score: N/A")
    
    # Print pass/fail
    print()
    print("Threshold Check:")
    pass_fail = evaluator.get_pass_fail_summary(result)
    for metric, passed in pass_fail.items():
        status = "✓ PASS" if passed else "✗ FAIL" if passed is False else "N/A"
        print(f"  {metric}: {status}")


def run_batch_evaluation(args: argparse.Namespace) -> None:
    """Run batch evaluation."""
    # Parse company ID
    company_id = None
    if args.company_id:
        company_id = validate_uuid(args.company_id, "company-id")
    
    # Parse chat IDs
    chat_ids = None
    if args.chat_ids:
        chat_ids = [validate_uuid(cid, "chat-id") for cid in args.chat_ids]
    
    # Parse user IDs
    user_ids = None
    if args.user_ids:
        user_ids = [validate_uuid(uid, "user-id") for uid in args.user_ids]
    
    # Parse date parameters
    start_time = None
    end_time = None
    days = args.days
    
    # If explicit dates are provided, they override --days
    if args.from_date:
        start_time = parse_date(args.from_date, "from-date")
    if args.to_date:
        end_time = parse_date(args.to_date, "to-date")
    
    # If --days 0, set days to None to disable date filter
    if days == 0:
        days = None
    
    # Create configuration
    config = EvaluationConfig(
        llm_model=args.model,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
    )
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Get database session
    session = next(get_db_session())
    
    try:
        runner = BatchEvaluationRunner(session, config)
        
        if args.preview:
            # Preview mode
            print("Previewing evaluation scope...")
            preview = runner.preview_evaluation(
                company_id=company_id,
                chat_ids=chat_ids,
                user_ids=user_ids,
                start_time=start_time,
                end_time=end_time,
                days=days,
            )
            print(json.dumps(preview, indent=2, default=str))
            return
        
        # Run evaluation
        print("Starting batch evaluation...")
        print(f"Company ID: {company_id}")
        print(f"Chat IDs: {chat_ids}")
        print(f"User IDs: {user_ids}")
        if start_time:
            print(f"Start Time: {start_time}")
        if end_time:
            print(f"End Time: {end_time}")
        if days is not None:
            print(f"Days: {days}")
        print(f"Limit: {args.limit}")
        print(f"Dry Run: {args.dry_run}")
        print()
        
        result = runner.run_evaluation(
            company_id=company_id,
            chat_ids=chat_ids,
            user_ids=user_ids,
            start_time=start_time,
            end_time=end_time,
            days=days,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        
        # Print results
        print("=" * 60)
        print("EVALUATION COMPLETE")
        print("=" * 60)
        print(f"Job ID: {result.job_id}")
        print(f"Status: {result.status}")
        print(f"Total Queries: {result.total_queries}")
        print()
        
        if result.total_queries > 0:
            print("Metric Scores:")
            if result.avg_faithfulness is not None:
                print(f"  Faithfulness: {result.avg_faithfulness:.4f}")
            if result.avg_answer_relevance is not None:
                print(f"  Answer Relevance: {result.avg_answer_relevance:.4f}")
            if result.avg_context_precision is not None:
                print(f"  Context Precision: {result.avg_context_precision:.4f}")
            if result.overall_score is not None:
                print(f"  Overall Score: {result.overall_score:.4f}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print()
        print(f"Started: {result.started_at}")
        print(f"Completed: {result.completed_at}")
        
    finally:
        session.close()


def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required.")
        print("Set it in your .env file or export it directly.")
        sys.exit(1)
    
    # Run appropriate mode
    if args.single:
        run_single_evaluation(args)
    else:
        run_batch_evaluation(args)


if __name__ == "__main__":
    main()
