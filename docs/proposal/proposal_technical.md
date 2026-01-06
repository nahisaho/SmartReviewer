# 技術提案書

## 第三者検証業務におけるドキュメントレビュー支援AIエージェントの設計開発に係る調査研究

---

## 1. 技術アプローチ

### 1.1 全体アーキテクチャ

本提案では、Model Context Protocol (MCP) に準拠したマルチサーバーアーキテクチャを採用します。これにより、特定ベンダーに依存しない再現可能なPoCを実現します。

```mermaid
flowchart TB
    subgraph UI["User Interface Layer"]
        CLI[CLI<br/>開発・検証用]
        WebUI[Web UI<br/>源内対応]
    end
    
    subgraph Host["MCP Host Layer"]
        MCPHost[MCP Host<br/>セッション管理<br/>ツール呼び出し]
    end
    
    subgraph Servers["MCP Server Layer"]
        Core[smartreviewer-core<br/>・文書アップロード<br/>・レビュー実行<br/>・レポート生成]
        
        RAG[smartreviewer-rag<br/>・ベクトル検索<br/>・ハイブリッド検索<br/>・コンテキスト取得]
        
        Knowledge[smartreviewer-knowledge<br/>・チェックリスト管理<br/>・ナレッジグラフ<br/>・オントロジー]
    end
    
    subgraph Data["Data Layer"]
        VDB[(Qdrant<br/>Vector DB)]
        KG[(Neo4j<br/>Knowledge Graph)]
        SQLite[(SQLite<br/>Document Store)]
    end
    
    subgraph LLM["LLM Layer"]
        Sampling[MCP Sampling<br/>LLM呼び出し]
        Model[庁内利用可能LLM<br/>Claude / GPT-4]
    end
    
    CLI --> MCPHost
    WebUI --> MCPHost
    MCPHost <--> Core
    MCPHost <--> RAG
    MCPHost <--> Knowledge
    MCPHost <--> Sampling
    
    Core --> SQLite
    RAG --> VDB
    Knowledge --> KG
    Sampling --> Model
```

### 1.2 MCP準拠の利点

| 利点 | 説明 |
|------|------|
| **標準化** | JSON-RPC 2.0ベースの標準プロトコル |
| **拡張性** | 新しいサーバーやツールの追加が容易 |
| **再現性** | 異なる環境でも同一の動作を保証 |
| **ベンダー非依存** | 特定の技術・製品に依存しない |

---

## 2. 先行PoC課題への技術的対応

### 2.1 課題1: チェックリスト品質

#### 問題
- 既存のチェックリストは自然言語で記述されており、AIが正確に解釈しにくい
- チェック基準が曖昧な項目が存在

#### 解決策: 構造化チェックリスト

```mermaid
flowchart LR
    subgraph 変換プロセス
        A[既存チェックリスト<br/>自然言語] --> B[分析・分類]
        B --> C[構造化定義<br/>YAML形式]
        C --> D[検証・調整]
        D --> E[AI実行可能形式]
    end
```

**構造化チェックリストの例:**

```yaml
check_items:
  - id: BD-001
    category: 基本設計書
    name: 必須セクション網羅性
    description: 基本設計書に必要なセクションが全て含まれているか
    required_sections:
      - システム概要
      - システム構成
      - 機能設計
      - データ設計
      - インターフェース設計
    check_logic: all_sections_present
    severity: high
    
  - id: BD-002
    category: 基本設計書
    name: システム目的の明確性
    description: システムの目的・背景が明確に記述されているか
    check_criteria:
      - keyword_present: ["目的", "背景", "概要"]
      - min_description_length: 200
      - clarity_score: >= 0.7
    check_logic: llm_evaluation
    severity: medium
```

### 2.2 課題2: 大容量文書処理

#### 問題
- 数万〜数十万文字の文書をLLMのコンテキスト長制限内で処理する必要がある
- 図表等のリッチコンテンツの取り扱い

#### 解決策: 階層的文書処理

```mermaid
flowchart TB
    A[入力文書] --> B{サイズ判定}
    
    B -->|小<br/>~10K文字| C[直接処理]
    B -->|中<br/>10K-50K文字| D[セクション分割]
    B -->|大<br/>50K文字以上| E[階層的処理]
    
    D --> F[関連セクション抽出<br/>RAG検索]
    
    E --> G[軽量モデルで<br/>セクション要約]
    G --> H[要約ベースで<br/>関連部分特定]
    H --> I[詳細部分のみ<br/>高精度処理]
    
    C --> J[LLMチェック]
    F --> J
    I --> J
    
    J --> K[結果統合]
    
    subgraph リッチコンテンツ処理
        L[図表検出] --> M[メタデータ抽出]
        M --> N[テキスト化/説明生成]
        N --> O[本文と統合]
    end
    
    A --> L
    O --> B
```

**処理戦略の詳細:**

| 文書サイズ | 処理方式 | 特徴 |
|-----------|---------|------|
| 小（~10K文字） | 直接処理 | 全文をLLMに投入 |
| 中（10K-50K文字） | セクション分割 | RAGで関連部分を抽出 |
| 大（50K文字以上） | 階層的処理 | 軽量モデルで要約→詳細処理 |

### 2.3 課題3: 是正提案の妥当性評価

#### 問題
- AIが生成する是正提案の品質を継続的に評価する仕組みがない
- 改善のためのフィードバックループが不在

#### 解決策: 回帰テスト環境

```mermaid
flowchart TB
    subgraph 評価基盤
        A[評価データセット<br/>Ground Truth付き]
        B[自動テストランナー]
        C[メトリクス計算<br/>Accuracy, Precision, Recall]
        D[分析レポート生成]
    end
    
    subgraph 改善サイクル
        E[課題分析<br/>FP/FN分析]
        F[改善実装<br/>ロジック/プロンプト]
        G[再評価]
    end
    
    A --> B --> C --> D --> E --> F --> G --> B
    
    subgraph CI/CD統合
        H[コミット] --> I[自動テスト実行]
        I --> J{精度低下?}
        J -->|Yes| K[アラート]
        J -->|No| L[マージ]
    end
```

**評価フレームワーク:**

```python
# 評価システムの概念
class EvaluationRunner:
    def __init__(self, dataset: EvaluationDataset):
        self.dataset = dataset
    
    async def run_evaluation(self) -> EvaluationResult:
        results = []
        for test_case in self.dataset.test_cases:
            actual = await self.execute_check(test_case)
            expected = test_case.expected_result
            results.append(self.compare(actual, expected))
        
        return EvaluationResult(
            accuracy=self.calculate_accuracy(results),
            precision=self.calculate_precision(results),
            recall=self.calculate_recall(results),
            details=results
        )
```

### 2.4 課題4: 庁内AI環境への適合

#### 問題
- 源内における技術的制約（UI/UX、入出力形式、権限管理等）
- 監査要件への対応

#### 解決策: 制約考慮設計

```mermaid
flowchart LR
    subgraph 源内対応
        A[入力制約対応<br/>ファイル形式・サイズ]
        B[出力形式対応<br/>構造化レポート]
        C[権限管理対応<br/>アクセス制御]
        D[監査対応<br/>操作ログ]
    end
    
    subgraph 抽象化レイヤー
        E[インターフェース抽象化]
        F[環境依存部分の分離]
    end
    
    A --> E
    B --> E
    C --> F
    D --> F
```

**庁内環境対応の設計方針:**

| 制約 | 対応方針 |
|------|---------|
| UI/UX制約 | 源内のUI規約に準拠したコンポーネント設計 |
| 入力形式 | 複数フォーマット対応（PDF, Word, Markdown） |
| 出力形式 | 構造化JSON + 人間可読レポート |
| 権限管理 | ロールベースアクセス制御（RBAC） |
| 監査ログ | 全操作の記録・保持 |

---

## 3. LLM/Embeddingモデル選定

### 3.1 選定基準

```mermaid
flowchart TB
    subgraph 選定基準
        A[庁内利用可否]
        B[日本語性能]
        C[コンテキスト長]
        D[コスト効率]
        E[レスポンス速度]
    end
    
    subgraph 候補モデル
        F[Claude 3.5 Sonnet]
        G[GPT-4 Turbo]
        H[GPT-4o]
    end
    
    A --> F
    A --> G
    A --> H
    B --> F
    B --> G
```

### 3.2 モデル比較（想定）

| モデル | 日本語性能 | コンテキスト | 速度 | コスト | 推奨用途 |
|--------|-----------|-------------|------|--------|---------|
| Claude 3.5 Sonnet | ◎ | 200K | ○ | 中 | メインチェック |
| GPT-4 Turbo | ○ | 128K | ○ | 高 | 複雑な判定 |
| GPT-4o | ○ | 128K | ◎ | 中 | 高速処理 |
| Claude 3 Haiku | ○ | 200K | ◎ | 低 | 軽量処理 |

### 3.3 ハイブリッド判定

```mermaid
flowchart TB
    A[チェック項目] --> B{判定方式}
    
    B -->|ルールベース| C[パターンマッチ<br/>構造チェック]
    B -->|LLM判定| D[意味理解<br/>文脈判定]
    B -->|ハイブリッド| E[ルール+LLM<br/>統合判定]
    
    C --> F[高速・確実]
    D --> G[高精度・柔軟]
    E --> H[バランス]
    
    F --> I[結果統合]
    G --> I
    H --> I
```

---

## 4. RAG実装

### 4.1 RAGアーキテクチャ

```mermaid
flowchart LR
    subgraph Indexing
        A[文書] --> B[チャンク分割]
        B --> C[Embedding生成]
        C --> D[(Vector DB<br/>Qdrant)]
    end
    
    subgraph Retrieval
        E[クエリ] --> F[クエリEmbedding]
        F --> G[ベクトル検索]
        D --> G
        G --> H[Re-ranking]
        H --> I[コンテキスト]
    end
    
    subgraph Generation
        I --> J[プロンプト構築]
        J --> K[LLM生成]
        K --> L[回答]
    end
```

### 4.2 ハイブリッド検索

```mermaid
flowchart TB
    A[検索クエリ] --> B[キーワード検索<br/>BM25]
    A --> C[ベクトル検索<br/>Dense Retrieval]
    
    B --> D[キーワード結果]
    C --> E[セマンティック結果]
    
    D --> F[スコア統合<br/>RRF/加重平均]
    E --> F
    
    F --> G[Re-ranking<br/>Cross-Encoder]
    G --> H[最終結果]
```

---

## 5. 評価指標と目標

### 5.1 KPI定義

| 指標 | 定義 | 目標値 |
|------|------|--------|
| **Accuracy** | (TP+TN)/(TP+TN+FP+FN) | ≥70% |
| **Precision** | TP/(TP+FP) | ≥70% |
| **Recall** | TP/(TP+FN) | ≥70% |
| **F1 Score** | 2×(Precision×Recall)/(Precision+Recall) | ≥70% |
| **処理時間** | 1文書あたりの処理時間 | ≤30秒 |
| **再現性** | 同一入力での結果一致率 | ≥95% |

### 5.2 評価データセット設計

```mermaid
flowchart TB
    subgraph データセット構成
        A[基本設計書<br/>10文書]
        B[テスト計画書<br/>10文書]
    end
    
    subgraph 文書バリエーション
        C[良好な文書<br/>チェック通過]
        D[問題のある文書<br/>チェック不合格]
        E[境界ケース<br/>判定困難]
    end
    
    subgraph Ground Truth
        F[期待される指摘]
        G[期待される是正提案]
    end
    
    A --> C
    A --> D
    A --> E
    B --> C
    B --> D
    B --> E
    
    C --> F
    D --> F
    E --> F
    F --> G
```

---

## 6. セキュリティ対策

### 6.1 データフロー

```mermaid
flowchart TB
    subgraph 入力
        A[評価用文書<br/>機密情報なし]
    end
    
    subgraph 処理
        B[文書解析]
        C[チェック実行]
        D[結果生成]
    end
    
    subgraph 保護措置
        E[アクセス制御]
        F[暗号化]
        G[監査ログ]
    end
    
    A --> B --> C --> D
    
    E -.-> B
    E -.-> C
    E -.-> D
    F -.-> A
    G -.-> B
    G -.-> C
    G -.-> D
```

### 6.2 セキュリティ要件対応

| 要件 | 対応方針 |
|------|---------|
| 機密情報の取扱い | 機密情報を含まない評価データセットを使用 |
| データ漏洩防止 | AI学習に利用されないAPIオプションを使用 |
| アクセス制御 | ロールベースアクセス制御の実装 |
| 監査証跡 | 全操作のログ記録・保持 |

---

## 7. 技術スタック

| カテゴリ | 技術 | 選定理由 |
|---------|------|---------|
| 言語 | Python 3.12 | AIライブラリの充実、MCP SDK対応 |
| フレームワーク | FastMCP | MCP準拠サーバー実装 |
| CLI | Typer | モダンなCLI構築 |
| Vector DB | Qdrant | OSS、高性能、ISMAP対応可能 |
| Graph DB | Neo4j | ナレッジグラフ構築 |
| テスト | pytest | 標準的なテストフレームワーク |

---

**以上**
