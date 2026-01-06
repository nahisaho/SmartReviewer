"""
Review Engine Models
====================

レビューエンジンのデータモデル定義
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ReviewStatus(str, Enum):
    """レビューステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingType(str, Enum):
    """指摘種別"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckResultStatus(str, Enum):
    """チェック結果ステータス"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


# ==============================================
# Request Models
# ==============================================

class ReviewOptions(BaseModel):
    """レビューオプション"""
    parallel: bool = Field(default=True, description="並列実行フラグ")
    include_evidence: bool = Field(default=True, description="根拠情報を含める")
    max_findings: int = Field(default=100, description="最大指摘数")
    timeout_seconds: int = Field(default=300, description="タイムアウト秒数")
    use_llm: bool = Field(default=True, description="LLM推論を使用")


class ReviewRequest(BaseModel):
    """レビューリクエスト"""
    document_id: str = Field(description="対象文書ID")
    document_content: str = Field(description="文書内容")
    document_type: str = Field(description="文書タイプ (basic_design / test_plan)")
    check_item_ids: Optional[list[str]] = Field(default=None, description="チェック項目IDリスト（空で全項目）")
    options: ReviewOptions = Field(default_factory=ReviewOptions, description="レビューオプション")


# ==============================================
# Result Models
# ==============================================

class Finding(BaseModel):
    """指摘事項"""
    id: str = Field(description="指摘ID")
    check_item_id: str = Field(description="関連チェック項目ID")
    type: FindingType = Field(description="指摘種別")
    severity: Severity = Field(description="重要度")
    title: str = Field(description="指摘タイトル")
    description: str = Field(description="指摘詳細")
    location: Optional[str] = Field(default=None, description="該当箇所（セクション等）")
    evidence: Optional[str] = Field(default=None, description="根拠・引用")
    guideline_reference: Optional[str] = Field(default=None, description="ガイドライン参照")


class Suggestion(BaseModel):
    """改善提案"""
    id: str = Field(description="提案ID")
    finding_id: str = Field(description="関連指摘ID")
    title: str = Field(description="提案タイトル")
    description: str = Field(description="提案詳細")
    example: Optional[str] = Field(default=None, description="修正例")
    priority: int = Field(default=1, description="優先度 (1-5)")


class CheckResult(BaseModel):
    """チェック結果"""
    check_item_id: str = Field(description="チェック項目ID")
    check_item_name: str = Field(description="チェック項目名")
    status: CheckResultStatus = Field(description="チェック結果ステータス")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="確信度")
    findings: list[Finding] = Field(default_factory=list, description="検出された指摘")
    suggestions: list[Suggestion] = Field(default_factory=list, description="改善提案")
    execution_time_ms: int = Field(default=0, description="実行時間(ms)")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")


class ReviewMetadata(BaseModel):
    """レビューメタデータ"""
    checks_executed: int = Field(description="実行チェック数")
    checks_passed: int = Field(description="合格チェック数")
    checks_failed: int = Field(description="不合格チェック数")
    checks_warning: int = Field(description="警告チェック数")
    checks_skipped: int = Field(description="スキップチェック数")
    document_sections_analyzed: int = Field(default=0, description="解析セクション数")
    llm_calls: int = Field(default=0, description="LLM呼び出し回数")


class ReviewResult(BaseModel):
    """レビュー結果"""
    review_id: str = Field(description="レビューID")
    document_id: str = Field(description="対象文書ID")
    document_type: str = Field(description="文書タイプ")
    status: ReviewStatus = Field(description="レビューステータス")
    overall_result: CheckResultStatus = Field(description="総合結果")
    created_at: str = Field(description="作成日時")
    completed_at: Optional[str] = Field(default=None, description="完了日時")
    execution_time_ms: int = Field(default=0, description="総実行時間(ms)")
    total_findings: int = Field(description="総指摘数")
    critical_findings: int = Field(description="重大指摘数")
    check_results: list[CheckResult] = Field(default_factory=list, description="チェック結果一覧")
    metadata: ReviewMetadata = Field(description="メタデータ")


# ==============================================
# Progress Model (for streaming updates)
# ==============================================

class ReviewProgress(BaseModel):
    """レビュー進捗"""
    review_id: str = Field(description="レビューID")
    current_check: int = Field(description="現在のチェック番号")
    total_checks: int = Field(description="総チェック数")
    current_check_name: str = Field(description="現在のチェック項目名")
    percent_complete: float = Field(description="完了パーセント")
    findings_so_far: int = Field(description="現時点の指摘数")
    status: str = Field(default="running", description="ステータス")
