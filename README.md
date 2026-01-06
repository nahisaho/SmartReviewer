# SmartReviewer - Document Review AI Agent

ドキュメントレビュー支援AIエージェント（MCP準拠）

## 概要

SmartReviewerは、基本設計書・テスト計画書などのドキュメントレビューを支援するAIエージェントです。
Model Context Protocol (MCP) に基づくNeuro-Symbolicアーキテクチャを採用しています。

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (CLI/Web UI)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol (JSON-RPC 2.0)
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ smartreviewer-  │ │ smartreviewer-  │ │ smartreviewer-  │
│ core            │ │ rag             │ │ knowledge       │
│                 │ │                 │ │                 │
│ Tools:          │ │ Tools:          │ │ Tools:          │
│ - review_doc    │ │ - vector_search │ │ - query_graph   │
│ - get_items     │ │ - graph_search  │ │ - check_ontol   │
│ - create_report │ │ - hybrid_retr   │ │ - get_coverage  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  Qdrant (Vector) │ Neo4j (Graph) │ MinIO │ RDF/OWL          │
└─────────────────────────────────────────────────────────────┘
```

## ディレクトリ構成

```
SmartReviewer/
├── src/
│   ├── servers/           # MCP Servers
│   │   ├── core/          # smartreviewer-core
│   │   │   ├── tools/     # review_document, get_check_items, etc.
│   │   │   ├── resources/ # documents/*, results/*
│   │   │   └── prompts/   # review templates
│   │   ├── rag/           # smartreviewer-rag
│   │   │   ├── tools/     # vector_search, graph_search, hybrid_retrieve
│   │   │   ├── resources/ # embeddings/*, chunks/*
│   │   │   └── prompts/   # RAG queries
│   │   └── knowledge/     # smartreviewer-knowledge
│   │       ├── tools/     # query_knowledge_graph, check_ontology_coverage
│   │       ├── resources/ # ontology/*, graph/*
│   │       └── prompts/   # reasoning templates
│   ├── host/              # MCP Host implementation
│   ├── cli/               # Command-line interface
│   └── shared/            # Shared utilities
│       ├── models/        # Data models
│       ├── config/        # Configuration
│       └── utils/         # Utilities
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── data/
│   ├── documents/         # Input documents
│   ├── ontologies/        # OWL/RDF ontology files
│   ├── embeddings/        # Generated embeddings
│   └── evaluation/        # Evaluation datasets
├── docker/                # Docker configurations
├── steering/              # MUSUBIX project memory
└── storage/specs/         # Requirements, Design, Tasks
```

## クイックスタート

```bash
# 依存関係のインストール
pip install -e ".[dev]"

# MCP Serverの起動（ローカル開発）
python -m smartreviewer.servers.core

# CLIの使用
smartreviewer review --file document.pdf
```

## ライセンス

Proprietary - All rights reserved.
