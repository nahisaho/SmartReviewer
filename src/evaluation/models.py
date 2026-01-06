"""
Evaluation Models
=================

評価システムのデータモデル定義
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# ==============================================
# Enums
# ==============================================

class EvaluationStatus(str, Enum):
    """評価ステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MetricType(str, Enum):
    """メトリクスタイプ"""
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ACCURACY = "accuracy"
    PROCESSING_TIME = "processing_time"
    TOKEN_COUNT = "token_count"
    COST = "cost"


# ==============================================
# Input Models
# ==============================================

class EvaluationDataset(BaseModel):
    """評価データセット"""
    id: str = Field(..., description="データセットID")
    name: str = Field(..., description="データセット名")
    document_type: str = Field(..., description="文書タイプ")
    documents: list["EvaluationDocument"] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


class EvaluationDocument(BaseModel):
    """評価用文書"""
    id: str = Field(..., description="文書ID")
    name: str = Field(..., description="文書名")
    content: str = Field(..., description="文書内容")
    document_type: str = Field(..., description="文書タイプ")
    ground_truth: list["GroundTruthItem"] = Field(
        default_factory=list,
        description="正解データ"
    )


class GroundTruthItem(BaseModel):
    """正解データ項目"""
    check_item_id: str = Field(..., description="チェック項目ID")
    expected_result: str = Field(
        ..., 
        description="期待される結果 (pass/fail/warning)"
    )
    expected_findings: list[str] = Field(
        default_factory=list,
        description="期待される指摘事項"
    )
    notes: Optional[str] = Field(None, description="備考")


class EvaluationConfig(BaseModel):
    """評価設定"""
    name: str = Field(..., description="評価名")
    dataset_id: str = Field(..., description="データセットID")
    check_item_ids: Optional[list[str]] = Field(
        None, 
        description="評価対象チェック項目（Noneで全項目）"
    )
    parallel: bool = Field(True, description="並列実行")
    repeat_count: int = Field(1, description="繰り返し回数（再現性検証用）")
    timeout_seconds: int = Field(300, description="タイムアウト秒")


# ==============================================
# Result Models
# ==============================================

class CheckEvaluationResult(BaseModel):
    """チェック評価結果"""
    check_item_id: str
    document_id: str
    expected_result: str
    actual_result: str
    is_correct: bool
    expected_findings: list[str] = Field(default_factory=list)
    actual_findings: list[str] = Field(default_factory=list)
    finding_match_count: int = 0
    processing_time_ms: int = 0


class DocumentEvaluationResult(BaseModel):
    """文書評価結果"""
    document_id: str
    document_name: str
    check_results: list[CheckEvaluationResult] = Field(default_factory=list)
    total_checks: int = 0
    correct_checks: int = 0
    accuracy: float = 0.0
    processing_time_ms: int = 0


class MetricResult(BaseModel):
    """メトリクス結果"""
    metric_type: MetricType
    value: float
    details: dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    """評価サマリー"""
    total_documents: int = 0
    total_checks: int = 0
    correct_checks: int = 0
    
    # 適合率・再現率
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # 計算メトリクス
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    
    # パフォーマンス
    avg_processing_time_ms: float = 0.0
    total_processing_time_ms: int = 0
    
    # 再現性（複数回実行時）
    consistency_rate: float = 1.0
    
    def calculate_metrics(self):
        """メトリクスを計算"""
        # Precision
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        # Recall
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        # F1 Score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        
        # Accuracy
        if self.total_checks > 0:
            self.accuracy = self.correct_checks / self.total_checks
        
        # Average processing time
        if self.total_documents > 0:
            self.avg_processing_time_ms = self.total_processing_time_ms / self.total_documents


class EvaluationResult(BaseModel):
    """評価結果"""
    evaluation_id: str = Field(..., description="評価ID")
    config: EvaluationConfig = Field(..., description="評価設定")
    status: EvaluationStatus = Field(
        default=EvaluationStatus.PENDING,
        description="ステータス"
    )
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    document_results: list[DocumentEvaluationResult] = Field(
        default_factory=list
    )
    summary: EvaluationSummary = Field(
        default_factory=EvaluationSummary
    )
    metrics: list[MetricResult] = Field(default_factory=list)
    
    # 再現性検証結果
    repeat_results: list["RepeatResult"] = Field(default_factory=list)
    
    error_message: Optional[str] = None


class RepeatResult(BaseModel):
    """繰り返し実行結果"""
    run_number: int
    accuracy: float
    processing_time_ms: int
    results_hash: str  # 結果のハッシュ（一貫性確認用）


# ==============================================
# Analysis Models
# ==============================================

class ErrorAnalysis(BaseModel):
    """エラー分析"""
    check_item_id: str
    check_item_name: str
    false_positive_count: int = 0
    false_negative_count: int = 0
    false_positive_examples: list[str] = Field(default_factory=list)
    false_negative_examples: list[str] = Field(default_factory=list)
    error_patterns: list[str] = Field(default_factory=list)


class RAGComparison(BaseModel):
    """RAG方式比較"""
    method: str  # vector / graph / hybrid
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    avg_processing_time_ms: float = 0.0


class ImprovementSuggestion(BaseModel):
    """改善提案"""
    priority: str  # high / medium / low
    category: str  # prompt / rag / check_logic / data
    description: str
    expected_impact: str
    effort_estimate: str
