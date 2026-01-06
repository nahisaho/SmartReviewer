"""
Evaluation Package
==================

SmartReviewer モデル評価モジュール
"""

from src.evaluation.metrics import (
    EmbeddingEvalResult,
    LLMEvalResult,
    EmbeddingEvaluator,
    LLMEvaluator,
    calculate_recall_at_k,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_rouge_l,
    calculate_f1,
)
from .models import (
    EvaluationStatus,
    MetricType,
    EvaluationDataset,
    EvaluationDocument,
    GroundTruthItem,
    EvaluationConfig,
    EvaluationResult,
    EvaluationSummary,
    DocumentEvaluationResult,
    CheckEvaluationResult,
    RepeatResult,
    MetricResult,
    ErrorAnalysis,
    RAGComparison,
    ImprovementSuggestion,
)
from .runner import (
    EvaluationRunner,
    run_evaluation_streaming,
    create_evaluation_runner,
)
from .datasets import (
    create_basic_design_dataset,
    create_test_plan_dataset,
    get_all_sample_datasets,
)
from .analyzer import (
    AnalysisReport,
    EvaluationAnalyzer,
    create_analysis_report,
    format_analysis_report,
)

__all__ = [
    # Metrics (existing)
    "EmbeddingEvalResult",
    "LLMEvalResult",
    "EmbeddingEvaluator",
    "LLMEvaluator",
    "calculate_recall_at_k",
    "calculate_mrr",
    "calculate_ndcg_at_k",
    "calculate_rouge_l",
    "calculate_f1",
    # Enums
    "EvaluationStatus",
    "MetricType",
    # Input Models
    "EvaluationDataset",
    "EvaluationDocument",
    "GroundTruthItem",
    "EvaluationConfig",
    # Result Models
    "EvaluationResult",
    "EvaluationSummary",
    "DocumentEvaluationResult",
    "CheckEvaluationResult",
    "RepeatResult",
    "MetricResult",
    # Analysis Models
    "ErrorAnalysis",
    "RAGComparison",
    "ImprovementSuggestion",
    "AnalysisReport",
    # Runner
    "EvaluationRunner",
    "run_evaluation_streaming",
    "create_evaluation_runner",
    # Analyzer
    "EvaluationAnalyzer",
    "create_analysis_report",
    "format_analysis_report",
    # Datasets
    "create_basic_design_dataset",
    "create_test_plan_dataset",
    "get_all_sample_datasets",
]
