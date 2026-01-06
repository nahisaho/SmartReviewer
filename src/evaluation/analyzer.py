"""
Evaluation Analyzer
===================

P3-3: 評価・分析
- P3-3-1: チェック結果レビュー
- P3-3-2: 是正提案妥当性評価
- P3-3-3: False Positive/Negative分析
- P3-3-4: RAG方式別精度比較分析
- P3-3-5: 改善点特定・優先度付け
"""

from datetime import datetime, UTC
from typing import Optional
from collections import defaultdict

from pydantic import BaseModel, Field

from src.evaluation.models import (
    EvaluationResult,
    EvaluationSummary,
    ErrorAnalysis,
    RAGComparison,
    ImprovementSuggestion,
    DocumentEvaluationResult,
    CheckEvaluationResult,
)


class AnalysisReport(BaseModel):
    """分析レポート"""
    report_id: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    
    # 総合評価
    overall_accuracy: float = 0.0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1_score: float = 0.0
    
    # False Positive/Negative分析
    error_analysis: list[ErrorAnalysis] = Field(default_factory=list)
    
    # RAG方式比較
    rag_comparisons: list[RAGComparison] = Field(default_factory=list)
    
    # 改善提案
    improvement_suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    
    # 詳細分析
    check_item_analysis: dict[str, dict] = Field(default_factory=dict)
    
    # 再現性分析
    reproducibility_rate: float = 1.0
    reproducibility_notes: list[str] = Field(default_factory=list)


class EvaluationAnalyzer:
    """評価結果アナライザー"""
    
    def __init__(self):
        self.results: list[EvaluationResult] = []
    
    def add_result(self, result: EvaluationResult):
        """評価結果を追加"""
        self.results.append(result)
    
    def analyze(self) -> AnalysisReport:
        """総合分析を実行"""
        if not self.results:
            raise ValueError("No evaluation results to analyze")
        
        report_id = f"analysis-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        report = AnalysisReport(report_id=report_id)
        
        # 総合メトリクス計算
        self._calculate_overall_metrics(report)
        
        # エラー分析
        self._analyze_errors(report)
        
        # チェック項目別分析
        self._analyze_by_check_item(report)
        
        # 再現性分析
        self._analyze_reproducibility(report)
        
        # 改善提案生成
        self._generate_improvements(report)
        
        return report
    
    def _calculate_overall_metrics(self, report: AnalysisReport):
        """総合メトリクスを計算"""
        total_tp = sum(r.summary.true_positives for r in self.results)
        total_tn = sum(r.summary.true_negatives for r in self.results)
        total_fp = sum(r.summary.false_positives for r in self.results)
        total_fn = sum(r.summary.false_negatives for r in self.results)
        total_all = total_tp + total_tn + total_fp + total_fn
        
        if total_all > 0:
            report.overall_accuracy = (total_tp + total_tn) / total_all
        
        if total_tp + total_fp > 0:
            report.overall_precision = total_tp / (total_tp + total_fp)
        
        if total_tp + total_fn > 0:
            report.overall_recall = total_tp / (total_tp + total_fn)
        
        if report.overall_precision + report.overall_recall > 0:
            report.overall_f1_score = (
                2 * report.overall_precision * report.overall_recall /
                (report.overall_precision + report.overall_recall)
            )
    
    def _analyze_errors(self, report: AnalysisReport):
        """False Positive/Negative分析"""
        # チェック項目ごとのエラー集計
        error_counts: dict[str, dict] = defaultdict(lambda: {
            "fp_count": 0,
            "fn_count": 0,
            "fp_examples": [],
            "fn_examples": [],
        })
        
        for result in self.results:
            for doc_result in result.document_results:
                for check_result in doc_result.check_results:
                    if not check_result.is_correct:
                        check_id = check_result.check_item_id
                        
                        # False Positive: 実際はpassなのにfailと判定
                        if check_result.expected_result == "pass" and check_result.actual_result == "fail":
                            error_counts[check_id]["fp_count"] += 1
                            error_counts[check_id]["fp_examples"].append(doc_result.document_id)
                        
                        # False Negative: 実際はfailなのにpassと判定
                        elif check_result.expected_result == "fail" and check_result.actual_result == "pass":
                            error_counts[check_id]["fn_count"] += 1
                            error_counts[check_id]["fn_examples"].append(doc_result.document_id)
        
        # ErrorAnalysisオブジェクトに変換
        for check_id, counts in error_counts.items():
            if counts["fp_count"] > 0 or counts["fn_count"] > 0:
                report.error_analysis.append(ErrorAnalysis(
                    check_item_id=check_id,
                    check_item_name=check_id,
                    false_positive_count=counts["fp_count"],
                    false_negative_count=counts["fn_count"],
                    false_positive_examples=counts["fp_examples"][:5],
                    false_negative_examples=counts["fn_examples"][:5],
                ))
    
    def _analyze_by_check_item(self, report: AnalysisReport):
        """チェック項目別分析"""
        check_stats: dict[str, dict] = defaultdict(lambda: {
            "total": 0,
            "correct": 0,
            "tp": 0,
            "tn": 0,
            "fp": 0,
            "fn": 0,
        })
        
        for result in self.results:
            for doc_result in result.document_results:
                for check_result in doc_result.check_results:
                    check_id = check_result.check_item_id
                    stats = check_stats[check_id]
                    stats["total"] += 1
                    
                    if check_result.is_correct:
                        stats["correct"] += 1
                        if check_result.expected_result == "fail":
                            stats["tp"] += 1
                        else:
                            stats["tn"] += 1
                    else:
                        if check_result.expected_result == "pass":
                            stats["fp"] += 1
                        else:
                            stats["fn"] += 1
        
        # チェック項目別レポート
        for check_id, stats in check_stats.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            precision = stats["tp"] / (stats["tp"] + stats["fp"]) if stats["tp"] + stats["fp"] > 0 else 0
            recall = stats["tp"] / (stats["tp"] + stats["fn"]) if stats["tp"] + stats["fn"] > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
            
            report.check_item_analysis[check_id] = {
                "total_evaluations": stats["total"],
                "correct": stats["correct"],
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "true_positives": stats["tp"],
                "true_negatives": stats["tn"],
                "false_positives": stats["fp"],
                "false_negatives": stats["fn"],
            }
    
    def _analyze_reproducibility(self, report: AnalysisReport):
        """再現性分析"""
        consistent_runs = 0
        total_runs = 0
        
        for result in self.results:
            if result.repeat_results:
                hashes = [r.results_hash for r in result.repeat_results]
                if len(set(hashes)) == 1:
                    consistent_runs += len(hashes)
                else:
                    # 異なる結果がある
                    unique_count = len(set(hashes))
                    report.reproducibility_notes.append(
                        f"{result.config.name}: {unique_count}種類の異なる結果"
                    )
                total_runs += len(hashes)
        
        if total_runs > 0:
            report.reproducibility_rate = consistent_runs / total_runs
        
        if report.reproducibility_rate == 1.0:
            report.reproducibility_notes.append("全ての繰り返し実行で一貫した結果を確認")
    
    def _generate_improvements(self, report: AnalysisReport):
        """改善提案を生成"""
        # エラー分析に基づく改善提案
        for error in report.error_analysis:
            if error.false_positive_count > 0:
                report.improvement_suggestions.append(ImprovementSuggestion(
                    priority="high" if error.false_positive_count >= 3 else "medium",
                    category="check_logic",
                    description=f"{error.check_item_id}: False Positive削減 ({error.false_positive_count}件)",
                    expected_impact="Precision向上",
                    effort_estimate="1-2日",
                ))
            
            if error.false_negative_count > 0:
                report.improvement_suggestions.append(ImprovementSuggestion(
                    priority="high" if error.false_negative_count >= 3 else "medium",
                    category="check_logic",
                    description=f"{error.check_item_id}: False Negative削減 ({error.false_negative_count}件)",
                    expected_impact="Recall向上",
                    effort_estimate="1-2日",
                ))
        
        # 全体精度に基づく改善提案
        if report.overall_accuracy < 0.8:
            report.improvement_suggestions.append(ImprovementSuggestion(
                priority="high",
                category="prompt",
                description="プロンプトチューニングによる精度向上",
                expected_impact="Accuracy 80%以上達成",
                effort_estimate="2-3日",
            ))
        
        if report.overall_precision < 0.7:
            report.improvement_suggestions.append(ImprovementSuggestion(
                priority="high",
                category="check_logic",
                description="判定ロジックの厳密化",
                expected_impact="Precision向上",
                effort_estimate="2-3日",
            ))
        
        if report.overall_recall < 0.7:
            report.improvement_suggestions.append(ImprovementSuggestion(
                priority="high",
                category="check_logic",
                description="判定条件の見直し",
                expected_impact="Recall向上",
                effort_estimate="2-3日",
            ))
        
        # RAG改善提案
        report.improvement_suggestions.append(ImprovementSuggestion(
            priority="medium",
            category="rag",
            description="LLM統合による高精度チェック",
            expected_impact="全体精度10-20%向上",
            effort_estimate="1週間",
        ))
        
        # 優先度でソート
        priority_order = {"high": 0, "medium": 1, "low": 2}
        report.improvement_suggestions.sort(
            key=lambda x: priority_order.get(x.priority, 99)
        )


def create_analysis_report(
    results: list[EvaluationResult],
) -> AnalysisReport:
    """分析レポートを作成"""
    analyzer = EvaluationAnalyzer()
    for result in results:
        analyzer.add_result(result)
    return analyzer.analyze()


def format_analysis_report(report: AnalysisReport) -> str:
    """分析レポートをテキスト形式でフォーマット"""
    lines = []
    
    lines.append("=" * 60)
    lines.append("📊 SmartReviewer PoC 評価分析レポート")
    lines.append("=" * 60)
    lines.append(f"レポートID: {report.report_id}")
    lines.append(f"作成日時: {report.created_at}")
    
    lines.append("\n" + "=" * 60)
    lines.append("📈 総合メトリクス")
    lines.append("=" * 60)
    lines.append(f"Accuracy:  {report.overall_accuracy:.1%}")
    lines.append(f"Precision: {report.overall_precision:.1%}")
    lines.append(f"Recall:    {report.overall_recall:.1%}")
    lines.append(f"F1 Score:  {report.overall_f1_score:.1%}")
    
    if report.error_analysis:
        lines.append("\n" + "=" * 60)
        lines.append("🔍 False Positive/Negative分析")
        lines.append("=" * 60)
        for error in report.error_analysis:
            lines.append(f"\n{error.check_item_id}:")
            if error.false_positive_count > 0:
                lines.append(f"  - False Positive: {error.false_positive_count}件")
            if error.false_negative_count > 0:
                lines.append(f"  - False Negative: {error.false_negative_count}件")
    
    if report.check_item_analysis:
        lines.append("\n" + "=" * 60)
        lines.append("📋 チェック項目別分析")
        lines.append("=" * 60)
        for check_id, analysis in report.check_item_analysis.items():
            lines.append(f"\n{check_id}:")
            lines.append(f"  - Accuracy: {analysis['accuracy']:.1%}")
            lines.append(f"  - Precision: {analysis['precision']:.1%}")
            lines.append(f"  - Recall: {analysis['recall']:.1%}")
    
    lines.append("\n" + "=" * 60)
    lines.append("🔄 再現性分析")
    lines.append("=" * 60)
    lines.append(f"再現性率: {report.reproducibility_rate:.1%}")
    for note in report.reproducibility_notes:
        lines.append(f"  - {note}")
    
    if report.improvement_suggestions:
        lines.append("\n" + "=" * 60)
        lines.append("💡 改善提案")
        lines.append("=" * 60)
        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion.priority, "⚪")
            lines.append(f"\n{i}. [{priority_icon} {suggestion.priority.upper()}] {suggestion.description}")
            lines.append(f"   カテゴリ: {suggestion.category}")
            lines.append(f"   期待効果: {suggestion.expected_impact}")
            lines.append(f"   工数: {suggestion.effort_estimate}")
    
    return "\n".join(lines)
