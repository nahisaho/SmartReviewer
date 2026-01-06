# SmartReviewer Ontologies

このディレクトリには SmartReviewer で使用するドメインオントロジーを格納します。

## ファイル構成

```
data/ontologies/
├── README.md                 # このファイル
├── basic_design.owl          # 基本設計書オントロジー
├── test_plan.owl             # 全体テスト計画書オントロジー
└── common/                   # 共通オントロジー（将来拡張用）
```

## オントロジー概要

### 1. 基本設計書オントロジー (`basic_design.owl`)

政府情報システムの基本設計書をレビューするためのドメインオントロジー。

**主要クラス:**
- `Document` / `BasicDesignDocument` - 文書
- `Section` - セクション
- `DesignComponent` - 設計要素（抽象クラス）
  - `SystemOverview` - システム概要
  - `Architecture` - アーキテクチャ設計
  - `FunctionalDesign` - 機能設計
  - `DataDesign` - データ設計
  - `InterfaceDesign` - インターフェース設計
  - `NonFunctionalDesign` - 非機能設計
- `CheckItem` - チェック項目
- `Guideline` / `GuidelineSection` - ガイドライン

**主要リレーションシップ:**
- `hasSection` - 文書がセクションを持つ
- `containsComponent` - セクションが設計要素を含む
- `realizesRequirement` - 設計要素が要件を実現する
- `appliesTo` - チェック項目が設計要素に適用される
- `referencesGuideline` - 設計要素がガイドラインを参照する

**必須セクション（Individual）:**
1. 概要
2. システム構成
3. 機能設計
4. データ設計
5. インターフェース設計
6. 非機能設計

### 2. 全体テスト計画書オントロジー (`test_plan.owl`)

政府情報システムの全体テスト計画書をレビューするためのドメインオントロジー。
`basic_design.owl` をインポートして共通クラスを再利用します。

**主要クラス:**
- `TestPlanDocument` - テスト計画書（`Document` のサブクラス）
- `TestPlanComponent` - テスト計画要素（抽象クラス）
  - `TestPolicy` - テスト方針
  - `TestLevel` - テストレベル（単体/結合/システム/受入）
  - `TestType` - テスト種別（機能/性能/セキュリティ等）
  - `TestScope` - テストスコープ
  - `TestCriteria` - テスト基準（開始/終了/合格）
  - `TestOrganization` - テスト体制
  - `TestEnvironment` - テスト環境
  - `TestSchedule` - テストスケジュール
  - `TestManagement` - テスト管理

**主要リレーションシップ:**
- `hasTestLevel` - テスト計画がテストレベルを持つ
- `hasTestType` - テストレベルがテスト種別を持つ
- `hasEntryCriteria` / `hasExitCriteria` - テストレベルが基準を持つ
- `requiresEnvironment` - テストレベルが環境を要する
- `precedesPhase` - テストフェーズの前後関係

**必須セクション:**
1. テスト方針
2. テストスコープ
3. テストレベル定義
4. テストスケジュール
5. テスト体制
6. テスト環境
7. テスト管理

**必須テストレベル:**
- 単体テスト
- 結合テスト
- システムテスト
- 受入テスト

## 使用方法

### Python (rdflib) での読み込み

```python
from rdflib import Graph

# オントロジーを読み込む
g = Graph()
g.parse("data/ontologies/basic_design.owl", format="xml")

# クラス一覧を取得
for s, p, o in g.triples((None, RDF.type, OWL.Class)):
    print(s)
```

### Neo4j ナレッジグラフとの連携

オントロジーで定義された概念は、`src/knowledge/schema.py` でNeo4jのスキーマにマッピングされています：

| OWL Class | Neo4j Label |
|-----------|-------------|
| `BasicDesignDocument` | `:BasicDesign` |
| `TestPlanDocument` | `:TestPlan` |
| `Section` | `:Section` |
| `CheckItem` | `:CheckItem` |
| `GuidelineSection` | `:GuidelineSection` |

## 参照ガイドライン

オントロジーは以下のガイドラインに基づいて設計されています：

- **DG推進標準ガイドライン**
  - 第3編 3.2章: 設計工程
  - 第3編 3.3章: テスト工程
  - 第4編 第5章: セキュリティ

## 拡張方法

新しい文書タイプをサポートする場合：

1. 新しいOWLファイルを作成（例：`detailed_design.owl`）
2. `basic_design.owl` をインポート
3. 文書タイプ固有のクラスとプロパティを定義
4. `src/knowledge/schema.py` にNeo4jマッピングを追加
5. チェック項目（`CHECK_ITEMS_DATA`）に新しい項目を追加

## バージョン情報

- Version: 1.0.0
- Created: 2025-01
- Based on: デジタル・ガバメント推進標準ガイドライン
