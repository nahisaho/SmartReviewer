"""
Tests for Evaluation System
===========================

評価システムのテスト
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock


# ==============================================
# Model Tests
# ==============================================

class TestEvaluationModels:
    """評価モデルテスト"""
    
    def test_import_models(self):
        """モデルがインポートできること"""
        from src.evaluation.models import (
            EvaluationStatus,
            MetricType,
            EvaluationDataset,
            EvaluationDocument,
            GroundTruthItem,
            EvaluationConfig,
            EvaluationResult,
            EvaluationSummary,
        )
        
        assert EvaluationStatus is not None
        assert MetricType is not None
    
    def test_evaluation_status_values(self):
        """EvaluationStatusの値"""
        from src.evaluation.models import EvaluationStatus
        
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.RUNNING.value == "running"
        assert EvaluationStatus.COMPLETED.value == "completed"
        assert EvaluationStatus.FAILED.value == "failed"
    
    def test_metric_type_values(self):
        """MetricTypeの値"""
        from src.evaluation.models import MetricType
        
        assert MetricType.PRECISION.value == "precision"
        assert MetricType.RECALL.value == "recall"
        assert MetricType.F1_SCORE.value == "f1_score"
        assert MetricType.ACCURACY.value == "accuracy"
    
    def test_ground_truth_item(self):
        """GroundTruthItem"""
        from src.evaluation.models import GroundTruthItem
        
        item = GroundTruthItem(
            check_item_id="BD-001",
            expected_result="pass",
            expected_findings=[],
        )
        
        assert item.check_item_id == "BD-001"
        assert item.expected_result == "pass"
    
    def test_evaluation_document(self):
        """EvaluationDocument"""
        from src.evaluation.models import EvaluationDocument, GroundTruthItem
        
        doc = EvaluationDocument(
            id="doc-001",
            name="テスト文書",
            content="# Test",
            document_type="basic_design",
            ground_truth=[
                GroundTruthItem(
                    check_item_id="BD-001",
                    expected_result="pass",
                ),
            ],
        )
        
        assert doc.id == "doc-001"
        assert len(doc.ground_truth) == 1
    
    def test_evaluation_dataset(self):
        """EvaluationDataset"""
        from src.evaluation.models import EvaluationDataset, EvaluationDocument
        
        dataset = EvaluationDataset(
            id="ds-001",
            name="テストデータセット",
            document_type="basic_design",
            documents=[],
        )
        
        assert dataset.id == "ds-001"
        assert dataset.name == "テストデータセット"
    
    def test_evaluation_config(self):
        """EvaluationConfig"""
        from src.evaluation.models import EvaluationConfig
        
        config = EvaluationConfig(
            name="Test Evaluation",
            dataset_id="ds-001",
            repeat_count=3,
        )
        
        assert config.name == "Test Evaluation"
        assert config.repeat_count == 3
        assert config.parallel is True
    
    def test_evaluation_summary_calculate_metrics(self):
        """EvaluationSummaryのメトリクス計算"""
        from src.evaluation.models import EvaluationSummary
        
        summary = EvaluationSummary(
            total_documents=5,
            total_checks=20,
            correct_checks=16,
            true_positives=8,
            false_positives=2,
            true_negatives=8,
            false_negatives=2,
            total_processing_time_ms=5000,
        )
        
        summary.calculate_metrics()
        
        # Precision = 8 / (8 + 2) = 0.8
        assert summary.precision == pytest.approx(0.8, rel=0.01)
        
        # Recall = 8 / (8 + 2) = 0.8
        assert summary.recall == pytest.approx(0.8, rel=0.01)
        
        # F1 = 2 * (0.8 * 0.8) / (0.8 + 0.8) = 0.8
        assert summary.f1_score == pytest.approx(0.8, rel=0.01)
        
        # Accuracy = 16 / 20 = 0.8
        assert summary.accuracy == pytest.approx(0.8, rel=0.01)
        
        # Avg processing time = 5000 / 5 = 1000
        assert summary.avg_processing_time_ms == pytest.approx(1000.0, rel=0.01)


# ==============================================
# Dataset Tests
# ==============================================

class TestDatasets:
    """データセットテスト"""
    
    def test_create_basic_design_dataset(self):
        """基本設計書データセット作成"""
        from src.evaluation.datasets import create_basic_design_dataset
        
        dataset = create_basic_design_dataset()
        
        assert dataset.id == "ds-basic-design-001"
        assert dataset.document_type == "basic_design"
        assert len(dataset.documents) >= 2
    
    def test_create_test_plan_dataset(self):
        """テスト計画書データセット作成"""
        from src.evaluation.datasets import create_test_plan_dataset
        
        dataset = create_test_plan_dataset()
        
        assert dataset.id == "ds-test-plan-001"
        assert dataset.document_type == "test_plan"
        assert len(dataset.documents) >= 1
    
    def test_get_all_sample_datasets(self):
        """全サンプルデータセット取得"""
        from src.evaluation.datasets import get_all_sample_datasets
        
        datasets = get_all_sample_datasets()
        
        assert len(datasets) >= 2
        
        ids = [ds.id for ds in datasets]
        assert "ds-basic-design-001" in ids
        assert "ds-test-plan-001" in ids
    
    def test_basic_design_dataset_has_ground_truth(self):
        """基本設計書データセットに正解データがあること"""
        from src.evaluation.datasets import create_basic_design_dataset
        
        dataset = create_basic_design_dataset()
        
        for doc in dataset.documents:
            assert len(doc.ground_truth) > 0
            for gt in doc.ground_truth:
                assert gt.check_item_id.startswith("BD-")
                assert gt.expected_result in ["pass", "fail", "warning"]


# ==============================================
# Runner Tests
# ==============================================

class TestEvaluationRunner:
    """評価ランナーテスト"""
    
    def test_create_runner(self):
        """ランナー作成"""
        from src.evaluation.runner import EvaluationRunner, create_evaluation_runner
        
        runner = EvaluationRunner(use_llm=False)
        assert runner is not None
        
        runner2 = create_evaluation_runner(use_llm=False)
        assert runner2 is not None
    
    def test_register_dataset(self):
        """データセット登録"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.datasets import create_basic_design_dataset
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        
        runner.register_dataset(dataset)
        
        retrieved = runner.get_dataset(dataset.id)
        assert retrieved is not None
        assert retrieved.id == dataset.id
    
    def test_list_datasets(self):
        """データセット一覧"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.datasets import get_all_sample_datasets
        
        runner = EvaluationRunner(use_llm=False)
        
        for ds in get_all_sample_datasets():
            runner.register_dataset(ds)
        
        datasets = runner.list_datasets()
        assert len(datasets) >= 2
    
    def test_run_evaluation_basic_design(self):
        """基本設計書評価実行"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.models import EvaluationConfig, EvaluationStatus
        from src.evaluation.datasets import create_basic_design_dataset
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test Evaluation",
            dataset_id=dataset.id,
        )
        
        result = asyncio.run(runner.run_evaluation(config))
        
        assert result.status == EvaluationStatus.COMPLETED
        assert len(result.document_results) == len(dataset.documents)
        assert result.summary.total_documents == len(dataset.documents)
    
    def test_run_evaluation_test_plan(self):
        """テスト計画書評価実行"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.models import EvaluationConfig, EvaluationStatus
        from src.evaluation.datasets import create_test_plan_dataset
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_test_plan_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test Plan Evaluation",
            dataset_id=dataset.id,
        )
        
        result = asyncio.run(runner.run_evaluation(config))
        
        assert result.status == EvaluationStatus.COMPLETED
    
    def test_run_evaluation_with_repeat(self):
        """再現性検証評価"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.models import EvaluationConfig
        from src.evaluation.datasets import create_basic_design_dataset
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Repeat Evaluation",
            dataset_id=dataset.id,
            repeat_count=3,
        )
        
        result = asyncio.run(runner.run_evaluation(config))
        
        # 繰り返し結果が記録されていること
        assert len(result.repeat_results) == 3
        
        # 一貫性率が計算されていること
        assert result.summary.consistency_rate > 0
    
    def test_run_evaluation_dataset_not_found(self):
        """存在しないデータセット"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.models import EvaluationConfig, EvaluationStatus
        
        runner = EvaluationRunner(use_llm=False)
        
        config = EvaluationConfig(
            name="Invalid Evaluation",
            dataset_id="nonexistent-dataset",
        )
        
        result = asyncio.run(runner.run_evaluation(config))
        
        assert result.status == EvaluationStatus.FAILED
        assert "not found" in result.error_message.lower()
    
    def test_metrics_calculated(self):
        """メトリクスが計算されること"""
        from src.evaluation.runner import EvaluationRunner
        from src.evaluation.models import EvaluationConfig, MetricType
        from src.evaluation.datasets import create_basic_design_dataset
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Metrics Evaluation",
            dataset_id=dataset.id,
        )
        
        result = asyncio.run(runner.run_evaluation(config))
        
        # メトリクスが存在すること
        assert len(result.metrics) > 0
        
        metric_types = [m.metric_type for m in result.metrics]
        assert MetricType.ACCURACY in metric_types
        assert MetricType.PRECISION in metric_types
        assert MetricType.RECALL in metric_types


# ==============================================
# CLI Tests
# ==============================================

class TestEvaluationCLI:
    """評価CLIテスト"""
    
    def test_evaluate_command_help(self):
        """evaluateコマンドヘルプ"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["evaluate", "--help"])
        
        assert result.exit_code == 0
        assert "evaluate" in result.stdout.lower() or "評価" in result.stdout
    
    def test_evaluate_basic_design(self):
        """基本設計書評価"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["evaluate", "--dataset", "basic_design"])
        
        # 結果が表示されること
        assert "評価" in result.stdout or "Accuracy" in result.stdout
    
    def test_evaluate_test_plan(self):
        """テスト計画書評価"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["evaluate", "--dataset", "test_plan"])
        
        assert "評価" in result.stdout or "Accuracy" in result.stdout
    
    def test_evaluate_json_output(self, tmp_path):
        """JSON出力"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        output_file = tmp_path / "eval_result.json"
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "evaluate",
            "--dataset", "basic_design",
            "--format", "json",
            "--output", str(output_file),
        ])
        
        assert output_file.exists()
        
        data = json.loads(output_file.read_text())
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_evaluate_invalid_dataset(self):
        """無効なデータセット"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["evaluate", "--dataset", "invalid"])
        
        assert result.exit_code == 1


# ==============================================
# Integration Tests
# ==============================================

class TestEvaluationIntegration:
    """評価統合テスト"""
    
    def test_full_evaluation_workflow(self):
        """完全な評価ワークフロー"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            EvaluationStatus,
            create_basic_design_dataset,
            create_test_plan_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        
        # データセット登録
        bd_dataset = create_basic_design_dataset()
        tp_dataset = create_test_plan_dataset()
        runner.register_dataset(bd_dataset)
        runner.register_dataset(tp_dataset)
        
        # 基本設計書評価
        bd_config = EvaluationConfig(
            name="Basic Design Evaluation",
            dataset_id=bd_dataset.id,
        )
        bd_result = asyncio.run(runner.run_evaluation(bd_config))
        
        assert bd_result.status == EvaluationStatus.COMPLETED
        
        # テスト計画書評価
        tp_config = EvaluationConfig(
            name="Test Plan Evaluation",
            dataset_id=tp_dataset.id,
        )
        tp_result = asyncio.run(runner.run_evaluation(tp_config))
        
        assert tp_result.status == EvaluationStatus.COMPLETED
        
        # 結果一覧
        results = runner.list_results()
        assert len(results) == 2
    
    def test_evaluation_streaming(self):
        """ストリーミング評価"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            run_evaluation_streaming,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Streaming Evaluation",
            dataset_id=dataset.id,
        )
        
        events = []
        
        async def collect_events():
            async for event in run_evaluation_streaming(runner, config):
                events.append(event)
        
        asyncio.run(collect_events())
        
        # イベントが発生していること
        assert len(events) > 0
        
        # 開始と完了イベントがあること
        event_types = [e["type"] for e in events]
        assert "started" in event_types
        assert "completed" in event_types


# ==============================================
# Analyzer Tests
# ==============================================

class TestEvaluationAnalyzer:
    """評価アナライザーテスト"""
    
    def test_import_analyzer(self):
        """アナライザーがインポートできること"""
        from src.evaluation.analyzer import (
            AnalysisReport,
            EvaluationAnalyzer,
            create_analysis_report,
            format_analysis_report,
        )
        
        assert AnalysisReport is not None
        assert EvaluationAnalyzer is not None
    
    def test_create_analyzer(self):
        """アナライザー作成"""
        from src.evaluation.analyzer import EvaluationAnalyzer
        
        analyzer = EvaluationAnalyzer()
        assert analyzer is not None
        assert len(analyzer.results) == 0
    
    def test_add_result(self):
        """結果追加"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            EvaluationAnalyzer,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        
        analyzer = EvaluationAnalyzer()
        analyzer.add_result(result)
        
        assert len(analyzer.results) == 1
    
    def test_analyze(self):
        """分析実行"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            EvaluationAnalyzer,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        
        analyzer = EvaluationAnalyzer()
        analyzer.add_result(result)
        report = analyzer.analyze()
        
        assert report is not None
        assert report.report_id is not None
        assert report.overall_accuracy >= 0
    
    def test_create_analysis_report(self):
        """create_analysis_report関数"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            create_analysis_report,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        
        report = create_analysis_report([result])
        
        assert report is not None
        assert report.overall_accuracy > 0
    
    def test_format_analysis_report(self):
        """format_analysis_report関数"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            create_analysis_report,
            format_analysis_report,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        report = create_analysis_report([result])
        
        formatted = format_analysis_report(report)
        
        assert formatted is not None
        assert "SmartReviewer" in formatted
        assert "Accuracy" in formatted
    
    def test_error_analysis(self):
        """エラー分析"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            create_analysis_report,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        report = create_analysis_report([result])
        
        # エラー分析が含まれていること
        assert hasattr(report, "error_analysis")
    
    def test_improvement_suggestions(self):
        """改善提案"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            create_analysis_report,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
        )
        result = asyncio.run(runner.run_evaluation(config))
        report = create_analysis_report([result])
        
        # 改善提案が含まれていること
        assert hasattr(report, "improvement_suggestions")
        assert len(report.improvement_suggestions) > 0
    
    def test_reproducibility_analysis(self):
        """再現性分析"""
        from src.evaluation import (
            EvaluationRunner,
            EvaluationConfig,
            create_analysis_report,
            create_basic_design_dataset,
        )
        
        runner = EvaluationRunner(use_llm=False)
        dataset = create_basic_design_dataset()
        runner.register_dataset(dataset)
        
        config = EvaluationConfig(
            name="Test",
            dataset_id=dataset.id,
            repeat_count=3,
        )
        result = asyncio.run(runner.run_evaluation(config))
        report = create_analysis_report([result])
        
        # 再現性分析が含まれていること
        assert report.reproducibility_rate == 1.0

