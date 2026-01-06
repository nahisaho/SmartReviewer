"""
Evaluation Sample Datasets
==========================

評価用サンプルデータセット
"""

from .models import (
    EvaluationDataset,
    EvaluationDocument,
    GroundTruthItem,
)


# ==============================================
# 基本設計書サンプル
# ==============================================

SAMPLE_BASIC_DESIGN_COMPLETE = """
# 基本設計書

## システム概要

### システム名称
SmartReviewer - 文書レビュー支援AIシステム

### 目的
本システムは、設計文書のレビュープロセスを自動化・効率化することを目的とする。
デジタル庁ドキュメント標準ガイドラインに準拠したレビューを実現する。

### 背景
従来のレビュープロセスは人的リソースに依存しており、品質のばらつきが課題であった。

## システム構成

### アーキテクチャ概要
マイクロサービスアーキテクチャを採用し、以下のコンポーネントで構成する。

```
┌─────────────────┐    ┌─────────────────┐
│  MCP Host       │────│  MCP Servers    │
│  (CLI/API)      │    │  (Core/RAG/KG)  │
└─────────────────┘    └─────────────────┘
```

### 構成要素
- MCP Host: クライアントアプリケーション
- MCP Servers: 機能提供サーバー群
- Knowledge Base: ベクトルDB + グラフDB

## 機能設計

### 機能一覧
| ID | 機能名 | 概要 |
|----|--------|------|
| F001 | 文書アップロード | レビュー対象文書を登録 |
| F002 | レビュー実行 | チェック項目に基づくレビュー |
| F003 | レポート生成 | レビュー結果をレポート化 |

## データ設計

### データモデル
```mermaid
erDiagram
    DOCUMENT ||--o{ SECTION : contains
    DOCUMENT ||--o{ REVIEW_RESULT : has
```

### データベース
- PostgreSQL: 文書メタデータ
- Qdrant: ベクトル埋め込み

## インターフェース設計

### 外部インターフェース
- MCP Protocol: JSON-RPC 2.0 over stdio

### 内部インターフェース
- サーバー間通信: MCP Protocol

## 非機能設計

### 性能要件
- レビュー応答時間: 30秒以内

### セキュリティ
- 認証: OAuth 2.0対応
"""

SAMPLE_BASIC_DESIGN_INCOMPLETE = """
# 基本設計書

## システム概要
これはテストシステムです。

## システム構成
マイクロサービス構成を採用。
"""

SAMPLE_BASIC_DESIGN_PARTIAL = """
# 基本設計書

## システム概要

### システム名称
テストシステム

### 目的
テスト目的のシステムです。

## システム構成

### アーキテクチャ概要
モノリシックアーキテクチャを採用。

## 機能設計

### 機能一覧
| ID | 機能名 |
|----|--------|
| F001 | 機能A |

## データ設計

設計中
"""


# ==============================================
# テスト計画書サンプル
# ==============================================

SAMPLE_TEST_PLAN_COMPLETE = """
# テスト計画書

## 概要

### 目的
本文書はSmartReviewerシステムのテスト計画を定義する。

### 対象システム
SmartReviewer v2.0

### テスト期間
2024年7月1日 - 2024年7月31日

## テストレベル

### 単体テスト
- 対象: 各モジュール
- 担当: 開発チーム
- 完了基準: カバレッジ80%以上

### 結合テスト
- 対象: コンポーネント間連携
- 担当: QAチーム
- 完了基準: 全シナリオ合格

### システムテスト
- 対象: システム全体
- 担当: QAチーム
- 完了基準: 全テストケース合格

## テスト種別

### 機能テスト
機能要件に基づくテストを実施する。

### 性能テスト
性能要件を満たすことを確認する。

## テスト環境

### 環境構成
- 開発環境: ローカルDockerコンテナ
- テスト環境: クラウドインスタンス

## テストスケジュール

| フェーズ | 開始日 | 終了日 |
|---------|--------|--------|
| 単体テスト | 7/1 | 7/10 |
| 結合テスト | 7/11 | 7/20 |

## 合格基準

### 全体合格基準
- 致命的バグ: 0件
- テストカバレッジ: 80%以上
"""

SAMPLE_TEST_PLAN_INCOMPLETE = """
# テスト計画書

## 概要
テスト計画です。

## テストレベル
単体テストと結合テストを実施。
"""


# ==============================================
# 評価データセット定義
# ==============================================

def create_basic_design_dataset() -> EvaluationDataset:
    """基本設計書評価データセットを作成"""
    return EvaluationDataset(
        id="ds-basic-design-001",
        name="基本設計書評価データセット",
        document_type="basic_design",
        documents=[
            EvaluationDocument(
                id="bd-doc-001",
                name="完全な基本設計書",
                content=SAMPLE_BASIC_DESIGN_COMPLETE,
                document_type="basic_design",
                ground_truth=[
                    GroundTruthItem(
                        check_item_id="BD-001",
                        expected_result="pass",
                        expected_findings=[],
                        notes="全セクションが存在",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-002",
                        expected_result="pass",
                        expected_findings=[],
                        notes="順序が正しい",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-003",
                        expected_result="pass",
                        expected_findings=[],
                        notes="目的が明記されている",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-004",
                        expected_result="pass",
                        expected_findings=[],
                        notes="構成図が存在",
                    ),
                ],
            ),
            EvaluationDocument(
                id="bd-doc-002",
                name="不完全な基本設計書",
                content=SAMPLE_BASIC_DESIGN_INCOMPLETE,
                document_type="basic_design",
                ground_truth=[
                    GroundTruthItem(
                        check_item_id="BD-001",
                        expected_result="fail",
                        expected_findings=["必須セクション不足"],
                        notes="機能設計、データ設計等が不足",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-003",
                        expected_result="fail",
                        expected_findings=["システム目的が不明確"],
                        notes="目的の記述がない",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-004",
                        expected_result="fail",
                        expected_findings=["システム構成図がない"],
                        notes="構成図がない",
                    ),
                ],
            ),
            EvaluationDocument(
                id="bd-doc-003",
                name="部分的な基本設計書",
                content=SAMPLE_BASIC_DESIGN_PARTIAL,
                document_type="basic_design",
                ground_truth=[
                    GroundTruthItem(
                        check_item_id="BD-001",
                        expected_result="fail",
                        expected_findings=["インターフェース設計セクションがない"],
                        notes="一部セクションが不足",
                    ),
                    GroundTruthItem(
                        check_item_id="BD-003",
                        expected_result="pass",
                        expected_findings=[],
                        notes="目的は記述されている",
                    ),
                ],
            ),
        ],
    )


def create_test_plan_dataset() -> EvaluationDataset:
    """テスト計画書評価データセットを作成"""
    return EvaluationDataset(
        id="ds-test-plan-001",
        name="テスト計画書評価データセット",
        document_type="test_plan",
        documents=[
            EvaluationDocument(
                id="tp-doc-001",
                name="完全なテスト計画書",
                content=SAMPLE_TEST_PLAN_COMPLETE,
                document_type="test_plan",
                ground_truth=[
                    GroundTruthItem(
                        check_item_id="TP-001",
                        expected_result="pass",
                        expected_findings=[],
                        notes="全セクションが存在",
                    ),
                ],
            ),
            EvaluationDocument(
                id="tp-doc-002",
                name="不完全なテスト計画書",
                content=SAMPLE_TEST_PLAN_INCOMPLETE,
                document_type="test_plan",
                ground_truth=[
                    GroundTruthItem(
                        check_item_id="TP-001",
                        expected_result="fail",
                        expected_findings=["必須セクション不足"],
                        notes="テスト環境、スケジュール等が不足",
                    ),
                ],
            ),
        ],
    )


def get_all_sample_datasets() -> list[EvaluationDataset]:
    """全サンプルデータセットを取得"""
    return [
        create_basic_design_dataset(),
        create_test_plan_dataset(),
    ]
