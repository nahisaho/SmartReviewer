# 基本設計書

## ドキュメントレビュー支援AIエージェント（SmartReviewer）

---

**文書管理情報**
- 文書ID: DES-001
- バージョン: 2.0.0
- 作成日: 2026-01-06
- 更新日: 2026-01-06
- ステータス: Draft
- 関連文書: REQ-001（要件定義書 v1.2.0）

---

## 1. 設計概要

### 1.1 目的
本設計書は、要件定義書（REQ-001）に基づき、ドキュメントレビュー支援AIエージェント（SmartReviewer）のシステムアーキテクチャ、コンポーネント構成、データ設計、インターフェース設計を定義する。

### 1.2 設計方針

| 方針 | 説明 |
|------|------|
| **MCP準拠** | Model Context Protocol (MCP) に準拠したAIエージェント設計 |
| **ハイブリッドRAG** | チェック種別に応じて通常RAG/GraphRAG/オントロジー参照を使い分け |
| **MCP Server構成** | 各機能をMCP Serverとして実装し、Tools/Resources/Promptsで公開 |
| **ベンダー非依存** | 特定クラウド/LLMへのロックイン回避、MCP Host汎用対応 |
| **段階的拡張** | MVP→本格導入への拡張性を確保 |

### 1.3 要件トレーサビリティ

| 設計項目 | 対応要件 |
|----------|----------|
| 2章 システムアーキテクチャ | FR-004, FR-010〜FR-014 |
| 3章 コンポーネント設計 | FR-001〜FR-014 |
| 4章 データ設計 | FR-002, FR-010, FR-011 |
| 5章 インターフェース設計 | FR-001, FR-009, NFR-005, NFR-006 |
| 6章 処理フロー設計 | FR-004〜FR-008 |
| 7章 技術選定 | FR-003 |

#### 機能要件トレーサビリティマトリクス

| 要件ID | 要件名 | 対応コンポーネント | 対応設計章 |
|--------|--------|-------------------|------------|
| FR-001 | 利用シナリオの具体化 | C-011 (Scenario Manager) | 3章, 5章 |
| FR-002 | データ収集・整備機能 | C-001, C-012 | 3章, 4章 |
| FR-003 | LLM/Embeddingモデル選定 | C-006, C-012 | 3章, 7章 |
| FR-004 | ドキュメントチェック機能 | C-006, C-007, C-008 | 3章, 6章 |
| FR-005 | 大容量文書処理機能 | C-001 | 3章 |
| FR-006 | リッチドキュメント処理機能 | C-001 | 3章 |
| FR-007 | 是正提案機能 | C-006 | 3章 |
| FR-008 | 回帰テスト環境 | C-009 | 3章 |
| FR-009 | ユーザーインターフェース | C-010 | 3章, 5章 |
| FR-010 | ドメインオントロジー構築 | C-005 | 3章, 4章 |
| FR-011 | ナレッジグラフ構築 | C-004 | 3章, 4章 |
| FR-012 | 通常RAG機能 | C-003 | 3章 |
| FR-013 | GraphRAG機能 | C-004 | 3章 |
| FR-014 | チェック種別ルーティング | C-002 | 3章 |

---

## 2. システムアーキテクチャ

### 2.1 全体アーキテクチャ（MCP構成）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP Host (AI Application)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Claude Desktop / VS Code Copilot / 源内AI環境 / カスタムHost        │   │
│  └────────────────────────────────────┬────────────────────────────────┘   │
│                                       │ MCP Protocol (JSON-RPC 2.0)         │
│                    ┌──────────────────┼──────────────────┐                  │
│                    │                  │                  │                  │
│                    ▼                  ▼                  ▼                  │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐   │
│  │  MCP Client 1       │ │  MCP Client 2       │ │  MCP Client 3       │   │
│  └──────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘   │
└─────────────┼────────────────────────┼────────────────────────┼─────────────┘
              │                        │                        │
              ▼                        ▼                        ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  SmartReviewer      │ │  RAG Engine         │ │  Knowledge          │
│  Core Server        │ │  Server             │ │  Server             │
│  (MCP Server)       │ │  (MCP Server)       │ │  (MCP Server)       │
│                     │ │                     │ │                     │
│  Tools:             │ │  Tools:             │ │  Tools:             │
│  - review_document  │ │  - vector_search    │ │  - query_graph      │
│  - get_check_items  │ │  - graph_search     │ │  - check_ontology   │
│  - create_report    │ │  - hybrid_retrieve  │ │  - get_coverage     │
│                     │ │                     │ │                     │
│  Resources:         │ │  Resources:         │ │  Resources:         │
│  - documents/*      │ │  - embeddings/*     │ │  - ontology/*       │
│  - results/*        │ │  - chunks/*         │ │  - graph/*          │
│                     │ │                     │ │                     │
│  Prompts:           │ │  Prompts:           │ │  Prompts:           │
│  - review_template  │ │  - rag_query        │ │  - coverage_check   │
│  - suggestion_gen   │ │  - context_build    │ │  - reasoning        │
└──────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Vector DB   │  │  Graph DB    │  │  Document    │  │  Ontology    │    │
│  │  (Qdrant)    │  │  (Neo4j)     │  │  Store       │  │  Repository  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  庁内LLM    │ │ ガイドライン │ │  評価用     │
            │  (源内)     │ │   文書      │ │ データセット │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 MCPアーキテクチャ概要

| 構成要素 | 役割 | 説明 |
|----------|------|------|
| **MCP Host** | AIアプリケーション | Claude Desktop、VS Code、源内環境等のAIクライアント |
| **MCP Client** | 接続管理 | 各MCP Serverへの専用接続を維持 |
| **MCP Server** | 機能提供 | Tools/Resources/Promptsを通じて機能を公開 |
| **Transport** | 通信層 | STDIO（ローカル）/ Streamable HTTP（リモート） |

### 2.3 MCP Server構成

| Server名 | 責務 | 公開機能 |
|----------|------|----------|
| **smartreviewer-core** | レビュー処理のオーケストレーション | レビュー実行、結果管理 |
| **smartreviewer-rag** | RAG処理（Vector/Graph/Hybrid） | 検索、コンテキスト構築 |
| **smartreviewer-knowledge** | ナレッジグラフ・オントロジー管理 | グラフクエリ、網羅性チェック |

### 2.4 MCPプロトコル仕様

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Protocol Stack                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Data Layer (JSON-RPC 2.0)               │   │
│  │                                                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │   Tools     │  │  Resources  │  │   Prompts   │     │   │
│  │  │             │  │             │  │             │     │   │
│  │  │ tools/list  │  │ resources/  │  │ prompts/    │     │   │
│  │  │ tools/call  │  │   list      │  │   list      │     │   │
│  │  │             │  │ resources/  │  │ prompts/    │     │   │
│  │  │             │  │   read      │  │   get       │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │                                                          │   │
│  │  Lifecycle: initialize → notifications/initialized       │   │
│  │  Notifications: tools/list_changed, resources/updated   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Transport Layer                         │   │
│  │                                                          │   │
│  │  ┌─────────────────────┐  ┌─────────────────────────┐  │   │
│  │  │  STDIO Transport    │  │  Streamable HTTP        │  │   │
│  │  │  (Local Server)     │  │  (Remote Server)        │  │   │
│  │  │                     │  │                         │  │   │
│  │  │  stdin/stdout       │  │  POST + SSE             │  │   │
│  │  │  No network         │  │  OAuth/Bearer Token     │  │   │
│  │  └─────────────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 MCP Tools設計（ハイブリッドRAG）

```
┌─────────────────────────────────────────────────────────────────┐
│              smartreviewer-rag Server - Tools                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tool: vector_search                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Description: ベクトル類似検索による関連チャンク取得     │   │
│  │  Use Case: 用語定義、記述スタイル、フォーマットチェック  │   │
│  │                                                          │   │
│  │  Input Schema:                                           │   │
│  │  {                                                       │   │
│  │    "query": "検索クエリ",                                │   │
│  │    "top_k": 5,                                           │   │
│  │    "threshold": 0.7,                                     │   │
│  │    "filter": { "document_type": "basic_design" }         │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  Output: 関連チャンク配列 + 類似度スコア                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tool: graph_search                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Description: ナレッジグラフ探索による関係性取得         │   │
│  │  Use Case: ガイドライン準拠、トレーサビリティチェック    │   │
│  │                                                          │   │
│  │  Input Schema:                                           │   │
│  │  {                                                       │   │
│  │    "entity": "エンティティ名",                           │   │
│  │    "relation_type": "MUST_COMPLY",                       │   │
│  │    "max_depth": 3,                                       │   │
│  │    "traversal": "bfs"                                    │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  Output: サブグラフ + パス情報                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tool: check_ontology                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Description: オントロジーに基づく網羅性検証             │   │
│  │  Use Case: カテゴリ網羅、必須項目欠落、階層構造検証      │   │
│  │                                                          │   │
│  │  Input Schema:                                           │   │
│  │  {                                                       │   │
│  │    "document_id": "文書ID",                              │   │
│  │    "domain": "system_design",                            │   │
│  │    "check_type": "coverage"                              │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  Output: 網羅性結果 + 欠落項目リスト                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tool: hybrid_retrieve (Check Router)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Description: チェック種別に応じたRAG方式自動選択・実行  │   │
│  │                                                          │   │
│  │  Input Schema:                                           │   │
│  │  {                                                       │   │
│  │    "check_item": { "id": "CHK-001", "type": "compliance"},│   │
│  │    "document_id": "文書ID",                              │   │
│  │    "context_chunks": ["chunk_id_1", "chunk_id_2"]        │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  Routing Logic:                                          │   │
│  │    type=terminology|style → vector_search                │   │
│  │    type=compliance|traceability → graph_search           │   │
│  │    type=coverage → check_ontology                        │   │
│  │    type=composite → 複数Tool組み合わせ                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. コンポーネント設計（MCP Server構成）

### 3.1 MCP Server一覧

| Server名 | 責務 | Transport | 対応要件 |
|----------|------|-----------|----------|
| **smartreviewer-core** | レビュー処理オーケストレーション | STDIO/HTTP | FR-001〜FR-009, FR-014 |
| **smartreviewer-rag** | RAG処理（Vector/Graph/Hybrid） | STDIO | FR-012〜FR-014 |
| **smartreviewer-knowledge** | ナレッジグラフ・オントロジー管理 | STDIO | FR-010, FR-011 |

### 3.2 smartreviewer-core Server

```
┌─────────────────────────────────────────────────────────────────┐
│                   smartreviewer-core Server                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Capabilities:                                                   │
│  {                                                               │
│    "tools": { "listChanged": true },                            │
│    "resources": { "subscribe": true, "listChanged": true },     │
│    "prompts": {}                                                 │
│  }                                                               │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                         TOOLS                                    │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: review_document                                    │   │
│  │ Description: 文書のレビューを実行し、指摘事項を生成      │   │
│  │ FR: FR-004, FR-007                                       │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   document_id: string (required)                         │   │
│  │   check_items: string[] (optional, default: all)         │   │
│  │   options: { parallel: boolean, include_evidence: boolean}│   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   review_id: string                                      │   │
│  │   status: "pass" | "fail" | "warning"                    │   │
│  │   findings: Finding[]                                    │   │
│  │   suggestions: Suggestion[]                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: upload_document                                    │   │
│  │ Description: 文書をアップロードし、前処理を実行          │   │
│  │ FR: FR-005, FR-006                                       │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   content: string (base64 or text)                       │   │
│  │   filename: string                                       │   │
│  │   document_type: "basic_design" | "test_plan"            │   │
│  │   metadata: { author, project, version }                 │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   document_id: string                                    │   │
│  │   chunks_count: number                                   │   │
│  │   processing_status: string                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: get_check_items                                    │   │
│  │ Description: 利用可能なチェック項目一覧を取得            │   │
│  │ FR: FR-004                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   document_type: "basic_design" | "test_plan" (optional) │   │
│  │   priority: "critical"|"high"|"medium"|"low" (optional)  │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   check_items: CheckItem[]                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: create_report                                      │   │
│  │ Description: レビュー結果からレポートを生成              │   │
│  │ FR: FR-004                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   review_id: string (required)                           │   │
│  │   format: "json" | "markdown" | "html" (default: json)   │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   report_content: string                                 │   │
│  │   summary: { total, pass, fail, warning }                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: run_evaluation                                     │   │
│  │ Description: 回帰テスト・評価を実行                      │   │
│  │ FR: FR-008                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   dataset_id: string (required)                          │   │
│  │   metrics: string[] (default: ["precision", "recall"])   │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   evaluation_id: string                                  │   │
│  │   metrics: { precision, recall, f1_score }               │   │
│  │   comparison: object (vs baseline)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                       RESOURCES                                  │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Resource: documents/{document_id}                               │
│    URI: smartreviewer://documents/{id}                          │
│    MIME: application/json                                       │
│    Description: アップロード済み文書の情報                      │
│                                                                  │
│  Resource: results/{review_id}                                   │
│    URI: smartreviewer://results/{id}                            │
│    MIME: application/json                                       │
│    Description: レビュー結果詳細                                │
│                                                                  │
│  Resource: check-items                                           │
│    URI: smartreviewer://check-items                             │
│    MIME: application/json                                       │
│    Description: チェック項目マスタ                              │
│                                                                  │
│  Resource: scenarios/{scenario_id}                               │
│    URI: smartreviewer://scenarios/{id}                          │
│    MIME: application/json                                       │
│    Description: 利用シナリオ定義 (FR-001)                       │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                        PROMPTS                                   │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Prompt: review_document_template                                │
│    Description: 文書レビュー実行用プロンプトテンプレート        │
│    Arguments:                                                    │
│      - document_type: 文書種別                                  │
│      - focus_areas: 重点チェック領域                            │
│                                                                  │
│  Prompt: suggestion_generation                                   │
│    Description: 是正提案生成用プロンプトテンプレート            │
│    Arguments:                                                    │
│      - finding: 指摘事項                                        │
│      - context: 関連コンテキスト                                │
│      - guideline_ref: 参照ガイドライン                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 smartreviewer-rag Server

```
┌─────────────────────────────────────────────────────────────────┐
│                    smartreviewer-rag Server                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Capabilities:                                                   │
│  {                                                               │
│    "tools": { "listChanged": true },                            │
│    "resources": { "subscribe": true }                           │
│  }                                                               │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                         TOOLS                                    │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: vector_search                                      │   │
│  │ Description: ベクトル類似検索による関連チャンク取得      │   │
│  │ FR: FR-012                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   query: string (required)                               │   │
│  │   top_k: number (default: 5)                             │   │
│  │   threshold: number (default: 0.7)                       │   │
│  │   filter: { document_type?, document_id? }               │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   chunks: Array<{ id, content, score, metadata }>        │   │
│  │   total_found: number                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: graph_search                                       │   │
│  │ Description: ナレッジグラフ探索による関係性情報取得      │   │
│  │ FR: FR-013                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   entity: string (required)                              │   │
│  │   relation_type: string (optional)                       │   │
│  │   max_depth: number (default: 2)                         │   │
│  │   traversal: "bfs" | "dfs" (default: "bfs")              │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   nodes: Array<{ id, type, properties }>                 │   │
│  │   edges: Array<{ source, target, type }>                 │   │
│  │   paths: Array<string[]>                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: hybrid_retrieve                                    │   │
│  │ Description: チェック種別に応じたRAG方式自動選択・実行   │   │
│  │ FR: FR-014                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   check_item_id: string (required)                       │   │
│  │   document_id: string (required)                         │   │
│  │   query: string (required)                               │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   strategy_used: "vector"|"graph"|"ontology"|"hybrid"    │   │
│  │   context: string                                        │   │
│  │   sources: Array<{ type, reference, relevance }>         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: embed_document                                     │   │
│  │ Description: 文書チャンクのEmbedding生成                 │   │
│  │ FR: FR-003, FR-012                                       │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   document_id: string (required)                         │   │
│  │   model: string (default: "multilingual-e5-large")       │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   chunks_embedded: number                                │   │
│  │   model_used: string                                     │   │
│  │   status: string                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                       RESOURCES                                  │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Resource: embeddings/{document_id}                              │
│    URI: smartreviewer-rag://embeddings/{id}                     │
│    Description: 文書のEmbedding情報                             │
│                                                                  │
│  Resource: chunks/{document_id}                                  │
│    URI: smartreviewer-rag://chunks/{id}                         │
│    Description: 文書のチャンク一覧                              │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                        PROMPTS                                   │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Prompt: rag_query_template                                      │
│    Description: RAG検索クエリ生成テンプレート                   │
│    Arguments:                                                    │
│      - check_item: チェック項目情報                             │
│      - document_context: 文書コンテキスト                       │
│                                                                  │
│  Prompt: context_synthesis                                       │
│    Description: 複数ソースからのコンテキスト統合テンプレート    │
│    Arguments:                                                    │
│      - vector_results: Vector検索結果                           │
│      - graph_results: Graph検索結果                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 smartreviewer-knowledge Server

```
┌─────────────────────────────────────────────────────────────────┐
│                 smartreviewer-knowledge Server                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Capabilities:                                                   │
│  {                                                               │
│    "tools": { "listChanged": true },                            │
│    "resources": { "subscribe": true, "listChanged": true }      │
│  }                                                               │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                         TOOLS                                    │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: query_knowledge_graph                              │   │
│  │ Description: ナレッジグラフへのCypherクエリ実行          │   │
│  │ FR: FR-011                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   cypher_query: string (required)                        │   │
│  │   parameters: object (optional)                          │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   records: Array<object>                                 │   │
│  │   summary: { nodes_returned, relationships_returned }    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: check_ontology_coverage                            │   │
│  │ Description: オントロジーに基づく網羅性検証              │   │
│  │ FR: FR-010                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   document_id: string (required)                         │   │
│  │   domain: "system_design"|"test_plan"|"guideline"        │   │
│  │   check_type: "coverage"|"hierarchy"|"required"          │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   coverage_rate: number (0-100)                          │   │
│  │   missing_items: Array<{ category, item, severity }>     │   │
│  │   hierarchy_issues: Array<object>                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: get_guideline_mapping                              │   │
│  │ Description: ガイドライン条項とチェック項目のマッピング取得│   │
│  │ FR: FR-010                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   guideline_article: string (optional)                   │   │
│  │   check_item_id: string (optional)                       │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   mappings: Array<{ article, check_item, relation }>     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool: reason_ontology                                    │   │
│  │ Description: オントロジー推論エンジンによる推論実行      │   │
│  │ FR: FR-010                                               │   │
│  │                                                          │   │
│  │ inputSchema:                                             │   │
│  │   ontology_domain: string (required)                     │   │
│  │   inference_type: "subclass"|"property"|"consistency"    │   │
│  │   target_class: string (optional)                        │   │
│  │                                                          │   │
│  │ outputSchema:                                            │   │
│  │   inferred_facts: Array<object>                          │   │
│  │   consistency_result: boolean                            │   │
│  │   explanation: string                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                       RESOURCES                                  │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Resource: ontology/{domain}                                     │
│    URI: smartreviewer-knowledge://ontology/{domain}             │
│    MIME: application/rdf+xml                                    │
│    Description: ドメインオントロジー定義                        │
│                                                                  │
│  Resource: graph/schema                                          │
│    URI: smartreviewer-knowledge://graph/schema                  │
│    MIME: application/json                                       │
│    Description: ナレッジグラフスキーマ                          │
│                                                                  │
│  Resource: guidelines/{article_id}                               │
│    URI: smartreviewer-knowledge://guidelines/{id}               │
│    MIME: application/json                                       │
│    Description: ガイドライン条項詳細                            │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                        PROMPTS                                   │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  Prompt: coverage_check_template                                 │
│    Description: 網羅性チェック用プロンプトテンプレート          │
│    Arguments:                                                    │
│      - document_structure: 文書構造                             │
│      - required_categories: 必須カテゴリ一覧                    │
│                                                                  │
│  Prompt: reasoning_template                                      │
│    Description: オントロジー推論結果解釈テンプレート            │
│    Arguments:                                                    │
│      - inference_result: 推論結果                               │
│      - context: 検証コンテキスト                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 コンポーネント対応表（旧設計→MCP Server）

| 旧コンポーネント | 新MCP Server | MCP Primitive | 対応要件 |
|-----------------|--------------|---------------|----------|
| C-001 Document Processor | smartreviewer-core | Tool: upload_document | FR-005, FR-006 |
| C-002 Check Router | smartreviewer-rag | Tool: hybrid_retrieve | FR-014 |
| C-003 Vector RAG Engine | smartreviewer-rag | Tool: vector_search | FR-012 |
| C-004 Graph RAG Engine | smartreviewer-rag | Tool: graph_search | FR-013 |
| C-005 Ontology Engine | smartreviewer-knowledge | Tool: check_ontology_coverage | FR-010 |
| C-006 LLM Inference | MCP Host (Sampling) | Client Primitive | FR-004, FR-007 |
| C-007 Review Orchestrator | smartreviewer-core | Tool: review_document | FR-004 |
| C-008 Result Aggregator | smartreviewer-core | Tool: create_report | FR-004 |
| C-009 Evaluation Engine | smartreviewer-core | Tool: run_evaluation | FR-008 |
| C-010 API Gateway | MCP Transport Layer | Protocol | FR-009 |
| C-011 Scenario Manager | smartreviewer-core | Resource: scenarios/* | FR-001 |
| C-012 Configuration Manager | smartreviewer-core | Resource: config | FR-002, FR-003 |

---

## 4. データ設計

### 4.1 データモデル概要

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Models                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Document   │    │  CheckItem  │    │  Review     │         │
│  │  Model      │    │  Model      │    │  Result     │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Chunk      │    │  Ontology   │    │  Suggestion │         │
│  │  Model      │    │  Model      │    │  Model      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 エンティティ定義

#### Document（文書）

```typescript
interface Document {
  id: string;                    // 文書ID
  name: string;                  // 文書名
  type: DocumentType;            // 文書種別 (基本設計書, テスト計画書等)
  version: string;               // バージョン
  content: string;               // 本文
  metadata: DocumentMetadata;    // メタデータ
  structure: DocumentStructure;  // 構造情報
  chunks: Chunk[];               // チャンク配列
  createdAt: DateTime;
  updatedAt: DateTime;
}

interface DocumentMetadata {
  author: string;
  project: string;
  classification: string;        // 機密区分
  format: 'pdf' | 'docx' | 'xlsx' | 'md';
  pageCount: number;
  characterCount: number;
}

interface DocumentStructure {
  sections: Section[];           // セクション階層
  tableOfContents: TOCItem[];   // 目次
  figures: Figure[];             // 図表一覧
}
```

#### Chunk（チャンク）

```typescript
interface Chunk {
  id: string;                    // チャンクID
  documentId: string;            // 所属文書ID
  content: string;               // テキスト内容
  embedding: number[];           // ベクトル表現 (次元数: 1536 for OpenAI, 768 for multilingual-e5)
  position: ChunkPosition;       // 文書内位置
  metadata: ChunkMetadata;       // メタデータ
}

interface ChunkPosition {
  sectionPath: string[];         // セクションパス
  startOffset: number;           // 開始位置
  endOffset: number;             // 終了位置
  pageNumber?: number;           // ページ番号
}

interface ChunkMetadata {
  tokenCount: number;            // トークン数
  hasTable: boolean;             // 表を含むか
  hasFigure: boolean;            // 図を含むか
  language: string;              // 言語
}
```

#### CheckItem（チェック項目）

```typescript
interface CheckItem {
  id: string;                    // チェック項目ID
  name: string;                  // チェック項目名
  description: string;           // 説明
  type: CheckType;               // チェック種別
  strategy: RAGStrategy;         // 適用RAG戦略
  domain: string;                // 対象ドメイン
  guidelineRef?: string;         // ガイドライン参照
  priority: 'critical' | 'high' | 'medium' | 'low';
  criteria: CheckCriteria;       // 判定基準
}

type CheckType = 
  | 'terminology'     // 用語定義
  | 'style'          // 記述スタイル
  | 'compliance'     // ガイドライン準拠
  | 'traceability'   // トレーサビリティ
  | 'coverage'       // 網羅性
  | 'composite';     // 複合

type RAGStrategy = 
  | 'vector_rag'
  | 'graph_rag'
  | 'ontology'
  | 'hybrid';

interface CheckCriteria {
  prompt: string;                // LLM用プロンプト
  expectedFormat: string;        // 期待出力形式
  scoringRubric?: string;        // 採点基準
}
```

#### ReviewResult（レビュー結果）

```typescript
interface ReviewResult {
  id: string;                    // 結果ID
  documentId: string;            // 対象文書ID
  checkItemId: string;           // チェック項目ID
  status: 'pass' | 'fail' | 'warning' | 'error';
  score?: number;                // スコア (0-100)
  findings: Finding[];           // 指摘事項
  suggestions: Suggestion[];     // 是正提案
  evidence: Evidence;            // 根拠情報
  executedAt: DateTime;
  executionTimeMs: number;       // 実行時間
}

interface Finding {
  id: string;
  severity: 'critical' | 'major' | 'minor' | 'info';
  location: ChunkPosition;       // 指摘箇所
  message: string;               // 指摘内容
  relatedGuideline?: string;     // 関連ガイドライン
}

interface Suggestion {
  id: string;
  findingId: string;             // 対応する指摘
  content: string;               // 是正提案内容
  confidence: number;            // 信頼度 (0-1)
  rationale: string;             // 提案根拠
}

interface Evidence {
  retrievedChunks: Chunk[];      // 参照したチャンク
  graphPaths?: GraphPath[];      // グラフ探索パス
  ontologyRefs?: OntologyRef[];  // オントロジー参照
}
```

### 4.3 ナレッジグラフスキーマ

```
┌─────────────────────────────────────────────────────────────────┐
│                   Knowledge Graph Schema                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Node Types (ノード種別):                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Document   │  │  Section    │  │  Guideline  │             │
│  │  Type       │  │             │  │  Article    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  CheckItem  │  │  Concept    │  │  Requirement│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  Edge Types (エッジ種別):                                        │
│  ─[CONTAINS]→      : 包含関係                                    │
│  ─[TRACES_TO]→     : トレーサビリティ                            │
│  ─[MUST_COMPLY]→   : 準拠関係                                    │
│  ─[REFERENCES]→    : 参照関係                                    │
│  ─[CATEGORIZED_BY]→: カテゴリ分類                                │
│  ─[VALIDATES]→     : 検証関係                                    │
│  ─[DEFINES]→       : 定義関係（ガイドライン→チェック項目）        │
│  ─[HAS_SECTION]→   : セクション所有                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**ナレッジグラフ例**:

```cypher
// ノード定義
(:DocumentType {name: "基本設計書"})
(:Section {name: "機能要件", level: 1})
(:GuidelineArticle {id: "GL-3.2.1", title: "機能要件の記載事項"})
(:CheckItem {id: "CHK-001", name: "機能要件の網羅性"})
(:Concept {name: "非機能要件", category: "品質属性"})

// エッジ定義
(基本設計書)-[:CONTAINS]->(機能要件)
(機能要件)-[:MUST_COMPLY]->(GL-3.2.1)
(GL-3.2.1)-[:DEFINES]->(CHK-001)
(非機能要件)-[:CATEGORIZED_BY]->({name: "性能"})
(非機能要件)-[:CATEGORIZED_BY]->({name: "セキュリティ"})
(非機能要件)-[:CATEGORIZED_BY]->({name: "可用性"})
```

### 4.4 オントロジー設計

#### ドメインオントロジー構造

```
SmartReviewer Ontology
├── DocumentOntology (文書オントロジー)
│   ├── DocumentType
│   │   ├── BasicDesignDocument (基本設計書)
│   │   ├── DetailedDesignDocument (詳細設計書)
│   │   └── TestPlanDocument (テスト計画書)
│   ├── Section
│   └── Element
│
├── GuidelineOntology (ガイドラインオントロジー)
│   ├── Guideline
│   │   ├── StandardGuideline (標準ガイドライン)
│   │   └── PracticeGuideline (実践ガイドライン)
│   ├── Article (条項)
│   └── CheckPoint (チェックポイント)
│
├── QualityOntology (品質オントロジー)
│   ├── FunctionalRequirement (機能要件)
│   └── NonFunctionalRequirement (非機能要件)
│       ├── Performance (性能)
│       ├── Security (セキュリティ)
│       ├── Availability (可用性)
│       ├── Maintainability (保守性)
│       └── Portability (可搬性)
│
└── TestOntology (テストオントロジー)
    ├── TestLevel
    │   ├── UnitTest
    │   ├── IntegrationTest
    │   ├── SystemTest
    │   └── AcceptanceTest
    └── TestTechnique
```

#### OWL定義例

```xml
<!-- 非機能要件クラス定義 -->
<owl:Class rdf:about="#NonFunctionalRequirement">
  <rdfs:subClassOf rdf:resource="#Requirement"/>
  <rdfs:label xml:lang="ja">非機能要件</rdfs:label>
</owl:Class>

<!-- 性能要件サブクラス -->
<owl:Class rdf:about="#PerformanceRequirement">
  <rdfs:subClassOf rdf:resource="#NonFunctionalRequirement"/>
  <rdfs:label xml:lang="ja">性能要件</rdfs:label>
</owl:Class>

<!-- 必須プロパティ定義 -->
<owl:ObjectProperty rdf:about="#mustHave">
  <rdfs:domain rdf:resource="#BasicDesignDocument"/>
  <rdfs:range rdf:resource="#NonFunctionalRequirement"/>
</owl:ObjectProperty>
```

---

## 5. インターフェース設計

### 5.1 MCPプロトコルインターフェース

#### 5.1.1 Transport設定

```yaml
# MCP Server Transport Configuration
servers:
  smartreviewer-core:
    transport: 
      type: stdio  # ローカル開発・単体テスト用
    # 本番環境では Streamable HTTP を使用
    # transport:
    #   type: http
    #   url: http://smartreviewer-core:8080/mcp
    
  smartreviewer-rag:
    transport:
      type: stdio
      command: python
      args: ["-m", "smartreviewer.rag.server"]
      
  smartreviewer-knowledge:
    transport:
      type: stdio
      command: python
      args: ["-m", "smartreviewer.knowledge.server"]
```

#### 5.1.2 MCP Tools インターフェース定義

```typescript
// ======================================================
//             smartreviewer-core Tools
// ======================================================

/**
 * Tool: review_document
 * 文書のレビューを実行し、指摘事項を生成
 */
interface ReviewDocumentInput {
  document_id: string;           // 必須: 対象文書ID
  check_items?: string[];        // 任意: チェック項目ID配列 (省略時: 全項目)
  options?: {
    parallel?: boolean;          // 並列実行 (default: true)
    include_evidence?: boolean;  // 根拠情報を含める (default: true)
    max_findings?: number;       // 最大指摘数 (default: 100)
  };
}

interface ReviewDocumentOutput {
  review_id: string;
  status: "pass" | "fail" | "warning";
  total_findings: number;
  findings: Finding[];
  suggestions: Suggestion[];
  execution_time_ms: number;
  metadata: {
    checks_executed: number;
    document_chunks_processed: number;
  };
}

/**
 * Tool: upload_document
 * 文書をアップロードし、前処理を実行
 */
interface UploadDocumentInput {
  content: string;               // Base64エンコードまたはテキスト
  filename: string;
  document_type: "basic_design" | "test_plan" | "guideline";
  metadata?: {
    author?: string;
    project?: string;
    version?: string;
    classification?: string;
  };
  options?: {
    chunking_strategy?: "section" | "fixed" | "semantic";
    chunk_size?: number;         // トークン数 (default: 512)
    chunk_overlap?: number;      // オーバーラップ (default: 50)
  };
}

interface UploadDocumentOutput {
  document_id: string;
  chunks_count: number;
  processing_status: "completed" | "processing" | "failed";
  structure: {
    sections_count: number;
    pages_count: number;
    tables_count: number;
    figures_count: number;
  };
}

/**
 * Tool: get_check_items
 * 利用可能なチェック項目一覧を取得
 */
interface GetCheckItemsInput {
  document_type?: "basic_design" | "test_plan";
  priority?: "critical" | "high" | "medium" | "low";
  check_type?: "terminology" | "style" | "compliance" | "traceability" | "coverage" | "composite";
}

interface GetCheckItemsOutput {
  check_items: CheckItem[];
  total: number;
  filters_applied: string[];
}

/**
 * Tool: create_report
 * レビュー結果からレポートを生成
 */
interface CreateReportInput {
  review_id: string;
  format: "json" | "markdown" | "html";
  options?: {
    include_summary?: boolean;
    include_details?: boolean;
    language?: "ja" | "en";
  };
}

interface CreateReportOutput {
  report_content: string;        // 生成されたレポート本文
  format: string;
  summary: {
    total_checks: number;
    passed: number;
    failed: number;
    warnings: number;
    critical_findings: number;
  };
}

/**
 * Tool: run_evaluation
 * 回帰テスト・評価を実行
 */
interface RunEvaluationInput {
  dataset_id: string;
  metrics?: string[];            // default: ["precision", "recall", "f1"]
  compare_baseline?: boolean;    // ベースラインとの比較
}

interface RunEvaluationOutput {
  evaluation_id: string;
  metrics: {
    precision: number;
    recall: number;
    f1_score: number;
  };
  comparison?: {
    baseline_metrics: object;
    delta: object;
    improved: boolean;
  };
  details: {
    true_positives: number;
    false_positives: number;
    false_negatives: number;
    samples_evaluated: number;
  };
}

// ======================================================
//              smartreviewer-rag Tools
// ======================================================

/**
 * Tool: vector_search
 * ベクトル類似検索による関連チャンク取得
 */
interface VectorSearchInput {
  query: string;
  top_k?: number;                // default: 5
  threshold?: number;            // default: 0.7
  filter?: {
    document_type?: string;
    document_id?: string;
    section_path?: string[];
  };
}

interface VectorSearchOutput {
  chunks: Array<{
    id: string;
    content: string;
    score: number;               // 類似度スコア (0-1)
    metadata: {
      document_id: string;
      section_path: string[];
      page_number?: number;
    };
  }>;
  total_found: number;
  query_embedding_time_ms: number;
  search_time_ms: number;
}

/**
 * Tool: graph_search
 * ナレッジグラフ探索による関係性情報取得
 */
interface GraphSearchInput {
  entity: string;                // 検索起点エンティティ
  relation_type?: string;        // 関係タイプでフィルタ
  max_depth?: number;            // default: 2
  traversal?: "bfs" | "dfs";     // default: "bfs"
  limit?: number;                // default: 50
}

interface GraphSearchOutput {
  nodes: Array<{
    id: string;
    type: string;
    properties: Record<string, any>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    properties?: Record<string, any>;
  }>;
  paths: string[][];             // 発見されたパス
  traversal_stats: {
    nodes_visited: number;
    max_depth_reached: number;
  };
}

/**
 * Tool: hybrid_retrieve
 * チェック種別に応じたRAG方式自動選択・実行
 */
interface HybridRetrieveInput {
  check_item_id: string;
  document_id: string;
  query: string;
  force_strategy?: "vector" | "graph" | "ontology" | "hybrid";
}

interface HybridRetrieveOutput {
  strategy_used: "vector" | "graph" | "ontology" | "hybrid";
  context: string;               // 統合コンテキスト
  sources: Array<{
    type: "vector" | "graph" | "ontology";
    reference: string;
    relevance: number;
  }>;
  strategy_selection_reason: string;
}

/**
 * Tool: embed_document
 * 文書チャンクのEmbedding生成
 */
interface EmbedDocumentInput {
  document_id: string;
  model?: string;                // default: "multilingual-e5-large"
  force_reembed?: boolean;       // 再埋め込み強制
}

interface EmbedDocumentOutput {
  chunks_embedded: number;
  model_used: string;
  status: "completed" | "partial" | "failed";
  embedding_dimension: number;
  total_time_ms: number;
}

// ======================================================
//           smartreviewer-knowledge Tools
// ======================================================

/**
 * Tool: query_knowledge_graph
 * ナレッジグラフへのCypherクエリ実行
 */
interface QueryKnowledgeGraphInput {
  cypher_query: string;
  parameters?: Record<string, any>;
  timeout_ms?: number;           // default: 30000
}

interface QueryKnowledgeGraphOutput {
  records: Array<Record<string, any>>;
  summary: {
    nodes_returned: number;
    relationships_returned: number;
    properties_returned: number;
  };
  execution_time_ms: number;
}

/**
 * Tool: check_ontology_coverage
 * オントロジーに基づく網羅性検証
 */
interface CheckOntologyCoverageInput {
  document_id: string;
  domain: "system_design" | "test_plan" | "guideline";
  check_type: "coverage" | "hierarchy" | "required";
}

interface CheckOntologyCoverageOutput {
  coverage_rate: number;         // 0-100
  missing_items: Array<{
    category: string;
    item: string;
    severity: "critical" | "major" | "minor";
    expected_location?: string;
  }>;
  hierarchy_issues: Array<{
    issue_type: string;
    description: string;
    location: string;
  }>;
  required_items_status: Array<{
    item: string;
    found: boolean;
    location?: string;
  }>;
}

/**
 * Tool: get_guideline_mapping
 * ガイドライン条項とチェック項目のマッピング取得
 */
interface GetGuidelineMappingInput {
  guideline_article?: string;
  check_item_id?: string;
  include_rationale?: boolean;   // マッピング根拠を含める
}

interface GetGuidelineMappingOutput {
  mappings: Array<{
    article: string;
    article_title: string;
    check_item: string;
    check_item_name: string;
    relation: "direct" | "indirect" | "derived";
    rationale?: string;
  }>;
}

/**
 * Tool: reason_ontology
 * オントロジー推論エンジンによる推論実行
 */
interface ReasonOntologyInput {
  ontology_domain: string;
  inference_type: "subclass" | "property" | "consistency";
  target_class?: string;
  depth?: number;                // default: 3
}

interface ReasonOntologyOutput {
  inferred_facts: Array<{
    subject: string;
    predicate: string;
    object: string;
    confidence: number;
  }>;
  consistency_result: boolean;
  explanation: string;
  reasoning_chain?: string[];
}
```

### 5.2 MCP Resources インターフェース定義

```typescript
// ======================================================
//            smartreviewer-core Resources
// ======================================================

/**
 * Resource: documents/{document_id}
 * URI: smartreviewer://documents/{id}
 */
interface DocumentResource {
  uri: string;                   // smartreviewer://documents/{id}
  name: string;                  // 文書名
  mimeType: "application/json";
  contents: {
    id: string;
    name: string;
    type: "basic_design" | "test_plan" | "guideline";
    version: string;
    metadata: DocumentMetadata;
    structure: DocumentStructure;
    chunks_count: number;
    created_at: string;
    updated_at: string;
  };
}

/**
 * Resource: results/{review_id}
 * URI: smartreviewer://results/{id}
 */
interface ReviewResultResource {
  uri: string;
  name: string;
  mimeType: "application/json";
  contents: {
    review_id: string;
    document_id: string;
    status: "pass" | "fail" | "warning";
    findings: Finding[];
    suggestions: Suggestion[];
    summary: ReviewSummary;
    executed_at: string;
  };
}

/**
 * Resource: check-items
 * URI: smartreviewer://check-items
 */
interface CheckItemsResource {
  uri: "smartreviewer://check-items";
  name: "Check Items Master";
  mimeType: "application/json";
  contents: {
    items: CheckItem[];
    categories: string[];
    last_updated: string;
  };
}

/**
 * Resource: scenarios/{scenario_id}
 * URI: smartreviewer://scenarios/{id}
 */
interface ScenarioResource {
  uri: string;
  name: string;
  mimeType: "application/json";
  contents: {
    id: string;
    name: string;
    target_role: "pjmo" | "quality_support" | "admin";
    description: string;
    workflow_steps: WorkflowStep[];
    applicable_doc_types: string[];
  };
}

// ======================================================
//             smartreviewer-rag Resources
// ======================================================

/**
 * Resource: embeddings/{document_id}
 * URI: smartreviewer-rag://embeddings/{id}
 */
interface EmbeddingsResource {
  uri: string;
  name: string;
  mimeType: "application/json";
  contents: {
    document_id: string;
    model: string;
    dimension: number;
    chunks_count: number;
    created_at: string;
    status: "ready" | "pending" | "failed";
  };
}

/**
 * Resource: chunks/{document_id}
 * URI: smartreviewer-rag://chunks/{id}
 */
interface ChunksResource {
  uri: string;
  name: string;
  mimeType: "application/json";
  contents: {
    document_id: string;
    chunks: Array<{
      id: string;
      content: string;
      position: ChunkPosition;
      has_embedding: boolean;
    }>;
    total_tokens: number;
  };
}

// ======================================================
//          smartreviewer-knowledge Resources
// ======================================================

/**
 * Resource: ontology/{domain}
 * URI: smartreviewer-knowledge://ontology/{domain}
 */
interface OntologyResource {
  uri: string;
  name: string;
  mimeType: "application/rdf+xml";
  contents: string;              // RDF/OWL形式のオントロジー定義
}

/**
 * Resource: graph/schema
 * URI: smartreviewer-knowledge://graph/schema
 */
interface GraphSchemaResource {
  uri: "smartreviewer-knowledge://graph/schema";
  name: "Knowledge Graph Schema";
  mimeType: "application/json";
  contents: {
    node_types: Array<{
      type: string;
      properties: string[];
      required: string[];
    }>;
    edge_types: Array<{
      type: string;
      source_types: string[];
      target_types: string[];
      properties: string[];
    }>;
    indexes: string[];
    constraints: string[];
  };
}

/**
 * Resource: guidelines/{article_id}
 * URI: smartreviewer-knowledge://guidelines/{id}
 */
interface GuidelineResource {
  uri: string;
  name: string;
  mimeType: "application/json";
  contents: {
    article_id: string;
    title: string;
    category: string;
    content: string;
    related_check_items: string[];
    parent_article?: string;
    child_articles?: string[];
  };
}
```

### 5.3 MCP Prompts インターフェース定義

```typescript
// ======================================================
//            smartreviewer-core Prompts
// ======================================================

/**
 * Prompt: review_document_template
 * 文書レビュー実行用プロンプトテンプレート
 */
interface ReviewDocumentPrompt {
  name: "review_document_template";
  description: "文書レビュー実行用プロンプトテンプレート";
  arguments: [
    {
      name: "document_type";
      description: "文書種別（基本設計書/テスト計画書）";
      required: true;
    },
    {
      name: "focus_areas";
      description: "重点チェック領域（カンマ区切り）";
      required: false;
    },
    {
      name: "severity_threshold";
      description: "報告する最低重要度";
      required: false;
    }
  ];
  // 生成されるプロンプト例:
  // messages: [
  //   { role: "user", content: "以下の${document_type}をレビューしてください..." }
  // ]
}

/**
 * Prompt: suggestion_generation
 * 是正提案生成用プロンプトテンプレート
 */
interface SuggestionGenerationPrompt {
  name: "suggestion_generation";
  description: "是正提案生成用プロンプトテンプレート";
  arguments: [
    {
      name: "finding";
      description: "指摘事項の詳細";
      required: true;
    },
    {
      name: "context";
      description: "関連コンテキスト";
      required: true;
    },
    {
      name: "guideline_ref";
      description: "参照ガイドライン";
      required: false;
    }
  ];
}

// ======================================================
//              smartreviewer-rag Prompts
// ======================================================

/**
 * Prompt: rag_query_template
 * RAG検索クエリ生成テンプレート
 */
interface RAGQueryPrompt {
  name: "rag_query_template";
  description: "RAG検索クエリ生成テンプレート";
  arguments: [
    {
      name: "check_item";
      description: "チェック項目情報";
      required: true;
    },
    {
      name: "document_context";
      description: "文書コンテキスト（対象セクション等）";
      required: true;
    }
  ];
}

/**
 * Prompt: context_synthesis
 * 複数ソースからのコンテキスト統合テンプレート
 */
interface ContextSynthesisPrompt {
  name: "context_synthesis";
  description: "複数ソースからのコンテキスト統合テンプレート";
  arguments: [
    {
      name: "vector_results";
      description: "Vector検索結果";
      required: true;
    },
    {
      name: "graph_results";
      description: "Graph検索結果";
      required: false;
    },
    {
      name: "max_context_length";
      description: "最大コンテキスト長（トークン数）";
      required: false;
    }
  ];
}

// ======================================================
//          smartreviewer-knowledge Prompts
// ======================================================

/**
 * Prompt: coverage_check_template
 * 網羅性チェック用プロンプトテンプレート
 */
interface CoverageCheckPrompt {
  name: "coverage_check_template";
  description: "網羅性チェック用プロンプトテンプレート";
  arguments: [
    {
      name: "document_structure";
      description: "文書構造情報";
      required: true;
    },
    {
      name: "required_categories";
      description: "必須カテゴリ一覧";
      required: true;
    },
    {
      name: "check_depth";
      description: "チェック深度（shallow/deep）";
      required: false;
    }
  ];
}

/**
 * Prompt: reasoning_template
 * オントロジー推論結果解釈テンプレート
 */
interface ReasoningPrompt {
  name: "reasoning_template";
  description: "オントロジー推論結果解釈テンプレート";
  arguments: [
    {
      name: "inference_result";
      description: "推論結果";
      required: true;
    },
    {
      name: "context";
      description: "検証コンテキスト";
      required: true;
    },
    {
      name: "explain_reasoning";
      description: "推論過程を説明するか";
      required: false;
    }
  ];
}
```

### 5.4 MCP Sampling インターフェース（Host側）

```typescript
/**
 * MCP Sampling Request (Host → Server → Host)
 * LLM推論はHost側のSamplingを通じて実行
 */
interface SamplingRequest {
  method: "sampling/createMessage";
  params: {
    messages: Array<{
      role: "user" | "assistant";
      content: {
        type: "text" | "image";
        text?: string;
        data?: string;           // Base64 for images
        mimeType?: string;
      };
    }>;
    modelPreferences?: {
      hints?: Array<{ name: string }>;
      costPriority?: number;     // 0-1
      speedPriority?: number;    // 0-1
      intelligencePriority?: number;  // 0-1
    };
    systemPrompt?: string;
    includeContext?: "none" | "thisServer" | "allServers";
    temperature?: number;
    maxTokens: number;
    stopSequences?: string[];
    metadata?: Record<string, unknown>;
  };
}

interface SamplingResponse {
  role: "assistant";
  content: {
    type: "text";
    text: string;
  };
  model: string;
  stopReason?: "endTurn" | "stopSequence" | "maxTokens";
}
```

### 5.5 共通データ型定義

```typescript
// ======================================================
//               Common Data Types
// ======================================================

interface Finding {
  id: string;
  severity: "critical" | "major" | "minor" | "info";
  check_item_id: string;
  message: string;
  location: {
    section_path: string[];
    page_number?: number;
    line_range?: [number, number];
  };
  evidence: string;
  related_guideline?: string;
  confidence: number;            // 0-1
}

interface Suggestion {
  id: string;
  finding_id: string;
  content: string;
  rationale: string;
  confidence: number;            // 0-1
  example?: string;
  references?: string[];
}

interface CheckItem {
  id: string;
  name: string;
  description: string;
  type: "terminology" | "style" | "compliance" | "traceability" | "coverage" | "composite";
  strategy: "vector_rag" | "graph_rag" | "ontology" | "hybrid";
  priority: "critical" | "high" | "medium" | "low";
  domain: string;
  guideline_ref?: string;
  criteria: {
    threshold?: number;
    required_elements?: string[];
    patterns?: string[];
  };
}

interface DocumentMetadata {
  author?: string;
  project?: string;
  classification?: string;
  format: "pdf" | "docx" | "xlsx" | "md";
  page_count?: number;
  character_count?: number;
  created_at?: string;
}

interface DocumentStructure {
  sections: Section[];
  table_of_contents: TOCItem[];
  figures: Figure[];
  tables: Table[];
}

interface Section {
  id: string;
  title: string;
  level: number;
  path: string[];
  start_page?: number;
  children?: Section[];
}

interface ChunkPosition {
  section_path: string[];
  start_offset: number;
  end_offset: number;
  page_number?: number;
}

interface WorkflowStep {
  order: number;
  name: string;
  description: string;
  required: boolean;
  expected_output?: string;
}

interface ReviewSummary {
  total_checks: number;
  passed: number;
  failed: number;
  warnings: number;
  critical_findings: number;
  execution_time_ms: number;
}
```
      properties:
        parallelExecution:
          type: boolean
          default: true
        includeEvidence:
          type: boolean
          default: true
        suggestionLevel:
          type: string
          enum: [none, basic, detailed]

    Scenario:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        targetRole:
          type: string
          enum: [pjmo, quality_support, admin]
        steps:
          type: array
          items:
            type: object
            properties:
              order:
                type: integer
              action:
                type: string
              description:
                type: string
        applicableDocTypes:
          type: array
          items:
            type: string
```

### 5.6 庁内AI環境（源内）連携

```
┌─────────────────────────────────────────────────────────────────┐
│                    源内連携アーキテクチャ（MCP経由）               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MCP Host (AIエージェント)              源内環境                 │
│  ┌─────────────────┐                 ┌─────────────────┐       │
│  │                 │  MCP Sampling   │                 │       │
│  │  Sampling       │◄───────────────►│  LLM Gateway    │       │
│  │  Handler        │  (JSON-RPC)     │                 │       │
│  └─────────────────┘                 └─────────────────┘       │
│           │                                   │                  │
│           │                                   ▼                  │
│           │                          ┌─────────────────┐       │
│           │                          │  庁内LLM        │       │
│           │                          │  (GPT-4等)      │       │
│           │                          └─────────────────┘       │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │  Audit Logger   │  ← MCP通信の監査ログ出力                   │
│  └─────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 処理フロー設計（MCPプロトコル）

### 6.1 MCPベースのレビュー実行フロー

```
┌─────────────────────────────────────────────────────────────────┐
│               MCPプロトコルによるレビュー実行フロー               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1. 文書アップロード] Tool: upload_document                     │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MCP Host                           smartreviewer-core    │   │
│  │    │                                      │              │   │
│  │    │──tools/call: upload_document────────►│              │   │
│  │    │◄─result: { document_id, chunks }────│              │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  [2. Embedding生成] Tool: embed_document                         │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MCP Host                           smartreviewer-rag     │   │
│  │    │                                      │              │   │
│  │    │──tools/call: embed_document─────────►│              │   │
│  │    │◄─result: { chunks_embedded }─────────│              │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  [3. レビュー実行] Tool: review_document                         │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ smartreviewer-core  ←──internal──►  smartreviewer-rag    │   │
│  │        │                                  │              │   │
│  │        │──tools/call: hybrid_retrieve────►│              │   │
│  │        │◄─context─────────────────────────│              │   │
│  │        │                                                 │   │
│  │        │←──internal──► smartreviewer-knowledge           │   │
│  │        │──tools/call: check_ontology_coverage──►│        │   │
│  │        │◄─coverage_result──────────────────────│         │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  [4. LLM推論（Sampling）]                                        │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ smartreviewer-core                    MCP Host (源内)    │   │
│  │    │                                      │              │   │
│  │    │──sampling/createMessage─────────────►│              │   │
│  │    │  { prompt, context, check_criteria } │              │   │
│  │    │◄─result: { judgment, suggestions }───│              │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  [5. レポート生成] Tool: create_report                           │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MCP Host                           smartreviewer-core    │   │
│  │    │                                      │              │   │
│  │    │──tools/call: create_report──────────►│              │   │
│  │    │◄─result: { report_content }──────────│              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 MCPシーケンス図（レビュー実行）

```
MCP Host     core Server    rag Server    knowledge Server   源内LLM
    │             │              │               │              │
    │──initialize─►│              │               │              │
    │◄─capabilities│              │               │              │
    │──initialize──────────────►│               │              │
    │◄─capabilities────────────│               │              │
    │──initialize───────────────────────────►│              │
    │◄─capabilities─────────────────────────│              │
    │             │              │               │              │
    │==== 文書アップロード ==========================================│
    │             │              │               │              │
    │──tools/call: upload_document────────────────────────────►│
    │  { content, filename, type }              │              │
    │◄─result: { document_id }──────────────────────────────────│
    │             │              │               │              │
    │==== Embedding生成 =============================================│
    │             │              │               │              │
    │──tools/call: embed_document──────────►│               │              │
    │  { document_id }          │              │               │
    │◄─result: { chunks_embedded }────────────│               │
    │             │              │               │              │
    │==== レビュー実行 ==============================================│
    │             │              │               │              │
    │──tools/call: review_document─────────►│               │              │
    │  { document_id, check_items }            │               │
    │             │──tools/call: hybrid_retrieve──►│               │
    │             │◄─context────────────────│               │
    │             │──tools/call: check_ontology_coverage─────►│
    │             │◄─coverage_result──────────────────────────│
    │             │              │               │              │
    │             │──sampling/createMessage─────────────────────────►│
    │             │  { messages, systemPrompt }                       │
    │             │◄─result: { content }──────────────────────────────│
    │             │              │               │              │
    │◄─result: { review_id, findings, suggestions }────────────│
    │             │              │               │              │
    │==== レポート生成 ==============================================│
    │             │              │               │              │
    │──tools/call: create_report───────────►│               │
    │  { review_id, format: "markdown" }       │               │
    │◄─result: { report_content }──────────────────────────────│
    │             │              │               │              │
```

### 6.3 MCPメッセージフォーマット

#### Tool呼び出しリクエスト例

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "review_document",
    "arguments": {
      "document_id": "doc-12345",
      "check_items": ["CHK-001", "CHK-002", "CHK-003"],
      "options": {
        "parallel": true,
        "include_evidence": true
      }
    }
  }
}
```

#### Tool呼び出しレスポンス例

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"review_id\":\"rev-67890\",\"status\":\"fail\",\"total_findings\":3,\"findings\":[{\"id\":\"f-001\",\"severity\":\"major\",\"message\":\"非機能要件の性能要件が未記載\",\"location\":{\"section_path\":[\"3\",\"3.2\"]}}],\"suggestions\":[{\"id\":\"s-001\",\"finding_id\":\"f-001\",\"content\":\"性能要件として応答時間、スループット、同時接続数を明記してください\"}]}"
      }
    ],
    "isError": false
  }
}
```

#### Sampling リクエスト例

```json
{
  "jsonrpc": "2.0",
  "id": "smp-001",
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "以下の基本設計書セクションをレビューし、非機能要件の網羅性を評価してください。\n\n## コンテキスト\n{retrieved_context}\n\n## チェック基準\n{check_criteria}"
        }
      }
    ],
    "modelPreferences": {
      "intelligencePriority": 0.8
    },
    "systemPrompt": "あなたは政府システムの設計書レビュー専門家です。デジタル・ガバメント推進標準ガイドラインに基づいて厳密に評価してください。",
    "maxTokens": 2048,
    "temperature": 0
  }
}
```

### 6.4 Resource購読フロー

```
MCP Host                    smartreviewer-core
    │                              │
    │──resources/subscribe─────────►│
    │  { uri: "smartreviewer://results/rev-67890" }
    │◄─subscribed──────────────────│
    │                              │
    │     (レビュー処理進行中...)     │
    │                              │
    │◄─notifications/resources/updated─│
    │  { uri, progress: 50 }       │
    │                              │
    │◄─notifications/resources/updated─│
    │  { uri, progress: 100, status: "completed" }
    │                              │
    │──resources/read──────────────►│
    │  { uri: "smartreviewer://results/rev-67890" }
    │◄─contents: { findings, suggestions }
    │                              │
```

### 6.5 エラーハンドリング（MCPプロトコル）

| MCPエラーコード | エラー種別 | 対応策 | リトライ |
|----------------|-----------|--------|----------|
| -32700 | Parse Error | リクエスト再構築 | No |
| -32600 | Invalid Request | スキーマ検証 | No |
| -32601 | Method Not Found | サポートTool確認 | No |
| -32602 | Invalid Params | パラメータ修正 | No |
| -32603 | Internal Error | フォールバック戦略 | Yes (3回) |

#### MCP固有エラーハンドリング

```typescript
// MCPエラーレスポンス構造
interface MCPErrorResponse {
  jsonrpc: "2.0";
  id: string | number;
  error: {
    code: number;
    message: string;
    data?: {
      retryable: boolean;
      fallbackStrategy?: string;
      details?: string;
    };
  };
}

// エラーハンドリング戦略
const errorHandlingStrategies = {
  // RAG Server接続エラー時
  "rag_server_unavailable": {
    action: "fallback_to_vector_only",
    notification: "Graph RAGは一時的に利用できません。Vector RAGのみで処理を継続します。"
  },
  
  // Knowledge Server接続エラー時
  "knowledge_server_unavailable": {
    action: "skip_ontology_check",
    notification: "オントロジーチェックはスキップされます。"
  },
  
  // Sampling タイムアウト時
  "sampling_timeout": {
    action: "retry_with_reduced_context",
    maxRetries: 3,
    contextReduction: 0.5  // コンテキストを50%に削減してリトライ
  }
};
```

### 6.6 並列処理パターン

```
┌─────────────────────────────────────────────────────────────────┐
│                   並列チェック実行パターン                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MCP Host                                                        │
│    │                                                             │
│    │══ 並列 Tool 呼び出し ═══════════════════════════════════   │
│    │                                                             │
│    ├──tools/call: vector_search────►rag Server                  │
│    │                                    │                        │
│    ├──tools/call: graph_search─────►rag Server                  │
│    │                                    │                        │
│    ├──tools/call: check_ontology───►knowledge Server            │
│    │                                    │                        │
│    │     (並列実行)                      │                        │
│    │                                    │                        │
│    │◄──result: vector_context──────────│                        │
│    │◄──result: graph_context───────────│                        │
│    │◄──result: ontology_result─────────│                        │
│    │                                                             │
│    │══ 結果統合 ═══════════════════════════════════════════════  │
│    │                                                             │
│    ├──Prompts/get: context_synthesis                            │
│    │                                                             │
│    └──sampling/createMessage (統合コンテキスト)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 技術選定

### 7.1 技術スタック（MCP準拠）

| カテゴリ | 技術 | 選定理由 |
|---------|------|----------|
| **言語** | TypeScript / Python | TypeScript: MCP Host/UI、Python: MCP Server実装 |
| **MCPフレームワーク** | MCP Python SDK (FastMCP) | 公式SDK、デコレータベースの簡潔な実装 |
| **MCP Transport** | STDIO / Streamable HTTP | ローカル開発: STDIO、本番: HTTP |
| **Embeddingモデル** | multilingual-e5-large / OpenAI text-embedding-3-small | 日本語対応、コスト効率（FR-003対応） |
| **ベクトルDB** | Qdrant | OSS、高性能、フィルタリング機能 |
| **グラフDB** | Neo4j | 成熟、Cypher言語、可視化ツール |
| **オントロジー** | RDF/OWL + rdflib + Owlready2 | 標準形式、推論サポート、Python連携 |
| **LLMフレームワーク** | MCP Sampling (Host側) | MCP標準のLLM推論インターフェース |
| **UI** | React + Next.js | 源内環境適合性要確認 |
| **テスト** | pytest / Vitest | 回帰テスト自動化 |

### 7.2 MCP Server実装詳細

#### MCP Python SDK構成

```python
# smartreviewer-core/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("smartreviewer-core")

@mcp.tool()
async def review_document(
    document_id: str,
    check_items: list[str] | None = None,
    options: dict | None = None
) -> dict:
    """
    文書のレビューを実行し、指摘事項を生成
    
    Args:
        document_id: 対象文書ID
        check_items: チェック項目ID配列（省略時: 全項目）
        options: レビューオプション
    
    Returns:
        review_id, status, findings, suggestions
    """
    # 実装...
    pass

@mcp.resource("smartreviewer://documents/{document_id}")
async def get_document(document_id: str) -> str:
    """アップロード済み文書の情報を取得"""
    # 実装...
    pass

@mcp.prompt()
async def review_document_template(
    document_type: str,
    focus_areas: str | None = None
) -> str:
    """文書レビュー実行用プロンプトテンプレート"""
    return f"""
    以下の{document_type}をレビューしてください。
    重点チェック領域: {focus_areas or "全領域"}
    
    デジタル・ガバメント推進標準ガイドラインに基づいて評価し、
    指摘事項と是正提案を構造化された形式で出力してください。
    """

if __name__ == "__main__":
    mcp.run()
```

#### MCP Server依存関係

```toml
# pyproject.toml
[project]
name = "smartreviewer-mcp"
version = "2.0.0"
requires-python = ">=3.10"

dependencies = [
    "mcp>=1.0.0",           # MCP Python SDK
    "fastmcp>=0.1.0",       # FastMCP decorator framework
    "qdrant-client>=1.7.0", # Vector DB
    "neo4j>=5.0.0",         # Graph DB
    "rdflib>=7.0.0",        # RDF/OWL処理
    "owlready2>=0.40",      # OWL推論
    "sentence-transformers>=2.2.0",  # Embedding
    "pydantic>=2.0.0",      # データバリデーション
    "httpx>=0.25.0",        # HTTP通信
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "mcp[cli]",             # MCP CLI tools
]
```

### 7.3 デプロイメント構成（MCP Server構成）

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server Deployment                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Docker Compose                        │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │             MCP Server Processes                  │   │   │
│  │  │                                                   │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │   │   │
│  │  │  │ core        │  │ rag         │  │knowledge │ │   │   │
│  │  │  │ Server      │  │ Server      │  │Server    │ │   │   │
│  │  │  │ (Python)    │  │ (Python)    │  │(Python)  │ │   │   │
│  │  │  │ STDIO/HTTP  │  │ STDIO       │  │STDIO     │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └──────────┘ │   │   │
│  │  │                                                   │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                         │                                │   │
│  │                         ▼                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  Qdrant     │  │  Neo4j      │  │  MinIO      │     │   │
│  │  │  (Vector)   │  │  (Graph)    │  │  (Storage)  │     │   │
│  │  │  :6333      │  │  :7474      │  │  :9000      │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  MCP Host (AIエージェント)                       │   │   │
│  │  │  - Claude Desktop / VS Code Copilot              │   │   │
│  │  │  - または カスタム MCP Client                    │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼ (MCP Sampling)                    │
│                    ┌─────────────────┐                          │
│                    │  源内LLM API    │                          │
│                    │  (GPT-4等)      │                          │
│                    └─────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 MCP Server起動設定

```json
// mcp-servers.json (MCP Host設定ファイル)
{
  "mcpServers": {
    "smartreviewer-core": {
      "command": "python",
      "args": ["-m", "smartreviewer.core.server"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "NEO4J_URL": "bolt://localhost:7687",
        "MINIO_URL": "http://localhost:9000"
      }
    },
    "smartreviewer-rag": {
      "command": "python",
      "args": ["-m", "smartreviewer.rag.server"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "EMBEDDING_MODEL": "multilingual-e5-large"
      }
    },
    "smartreviewer-knowledge": {
      "command": "python",
      "args": ["-m", "smartreviewer.knowledge.server"],
      "env": {
        "NEO4J_URL": "bolt://localhost:7687",
        "ONTOLOGY_PATH": "/data/ontology"
      }
    }
  }
}
```

### 7.5 テスト戦略（MCP対応）

```python
# tests/test_mcp_tools.py
import pytest
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.fixture
async def mcp_client():
    """MCP Server接続用フィクスチャ"""
    async with stdio_client(
        command="python",
        args=["-m", "smartreviewer.core.server"]
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

@pytest.mark.asyncio
async def test_review_document_tool(mcp_client):
    """review_document Tool の統合テスト"""
    # Tool一覧取得
    tools = await mcp_client.list_tools()
    assert any(t.name == "review_document" for t in tools)
    
    # Tool実行
    result = await mcp_client.call_tool(
        "review_document",
        arguments={
            "document_id": "test-doc-001",
            "check_items": ["CHK-001"]
        }
    )
    
    assert result.content[0].type == "text"
    response = json.loads(result.content[0].text)
    assert "review_id" in response
    assert response["status"] in ["pass", "fail", "warning"]

@pytest.mark.asyncio
async def test_resource_read(mcp_client):
    """Resource読み取りテスト"""
    resources = await mcp_client.list_resources()
    
    # documents リソースの存在確認
    doc_resources = [r for r in resources if "documents" in r.uri]
    assert len(doc_resources) > 0
```

---

## 8. セキュリティ設計

### 8.1 認証・認可

| 項目 | 方式 |
|------|------|
| 認証 | 源内環境連携（OAuth 2.0/OIDC） |
| 認可 | RBAC（Role-Based Access Control） |
| API認証 | Bearer Token |

### 8.2 データ保護（NFR-004対応）

| 項目 | 対策 | 対応要件 |
|------|------|----------|
| 通信暗号化 | TLS 1.3 | NFR-004 |
| 保存データ暗号化 | AES-256 | NFR-004 |
| ログ匿名化 | 個人情報マスキング | NFR-004 |
| AI学習除外 | LLM APIへのデータがモデル学習に使用されない設定を確認 | NFR-004 |
| データ保持期間 | 検証終了後のデータ削除ポリシー策定 | NFR-004 |
| アクセス制限 | 評価用データセットへのアクセスを承認者に限定 | NFR-004, NFR-005 |

#### 機密情報保護方針

```
┌─────────────────────────────────────────────────────────────────┐
│                    機密情報保護アーキテクチャ                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [入力段階]                                                      │
│    文書アップロード → 機密区分チェック → 匿名化処理              │
│                                                                  │
│  [処理段階]                                                      │
│    暗号化通信 → LLM API (学習除外設定) → 一時データ暗号化        │
│                                                                  │
│  [保存段階]                                                      │
│    AES-256暗号化 → アクセス制御 → 監査ログ記録                   │
│                                                                  │
│  [削除段階]                                                      │
│    保持期間経過 → セキュア削除 → 削除証跡記録                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 監査ログ

```typescript
interface AuditLog {
  timestamp: DateTime;
  userId: string;
  action: AuditAction;
  resourceType: string;
  resourceId: string;
  details: object;
  ipAddress: string;
  userAgent: string;
}

type AuditAction = 
  | 'DOCUMENT_UPLOAD'
  | 'REVIEW_START'
  | 'REVIEW_COMPLETE'
  | 'RESULT_VIEW'
  | 'REPORT_DOWNLOAD'
  | 'LLM_INFERENCE';
```

---

## 9. 制約・前提条件

### 9.1 前提条件

| ID | 前提条件 |
|----|----------|
| PRE-001 | 源内環境のLLM APIが利用可能であること |
| PRE-002 | 評価用文書データセットが提供されること |
| PRE-003 | デジタル・ガバメント推進標準ガイドラインの電子版が利用可能であること |
| PRE-004 | ISMAPクラウドサービスが利用可能であること |

### 9.2 設計上の制約

| ID | 制約 | 対応 |
|----|------|------|
| CON-001 | 2ヶ月間の検証期間 | MVPスコープに限定 |
| CON-002 | 特定ベンダー非依存 | 標準技術・OSS優先 |
| CON-003 | 機密情報を含まないデータ使用 | 匿名化データセット使用 |

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|------------|------|----------|--------|
| 1.0.0 | 2026-01-06 | 初版作成 | - |
| 1.1.0 | 2026-01-06 | レビュー指摘対応: コンポーネント追加(C-011,C-012)、API追加、トレーサビリティ強化、セキュリティ設計詳細化 | - |
| 1.2.0 | 2026-01-06 | Info指摘対応: C-011/C-012詳細設計追加、OpenAPIスキーマ定義完備 | - |
| 2.0.0 | 2026-01-06 | **MCP準拠への全面改訂**: FastAPI/REST API → Model Context Protocol (MCP) アーキテクチャへ移行。3つのMCP Server構成（smartreviewer-core, smartreviewer-rag, smartreviewer-knowledge）、Tools/Resources/Prompts定義、MCPプロトコル処理フロー、MCP Python SDK技術スタックへ変更 | - |

---

**トレーサビリティ**: REQ-001 要件定義書 v1.2.0
**MUSUBIX準拠**: Article I (Library-First), Article III (Test-First)
**MCP準拠**: Model Context Protocol Specification (https://modelcontextprotocol.io)
