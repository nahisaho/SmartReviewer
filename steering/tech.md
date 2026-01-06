# SmartReviewer - Technology Stack

## 言語

- TypeScript 5.3+
- Node.js 20+
- Python 3.11+ (オントロジー処理・ML)

## AI/ML基盤

### LLM
- 庁内利用可能なLLM（源内環境で選定）
- Embedding モデル（ベクトル検索用）

### 知識表現・RAG
| コンポーネント | 技術候補 | 用途 |
|---------------|----------|------|
| ベクトルDB | Qdrant / Weaviate / pgvector | 通常RAG用ベクトル検索 |
| グラフDB | Neo4j / Amazon Neptune / NebulaGraph | GraphRAG用ナレッジグラフ |
| オントロジー | RDF/OWL (Protégé) | ドメイン知識の構造化 |
| GraphRAGフレームワーク | LangChain + Graph / LlamaIndex | ハイブリッドRAG実装 |

### ドメインオントロジー
| ドメイン | 内容 |
|----------|------|
| システム設計 | 設計パターン、アーキテクチャ、品質属性 |
| テスト計画 | テストレベル、技法、品質指標 |
| ガイドライン | デジ庁標準ガイドライン概念体系 |

## フレームワーク

- LangChain / LlamaIndex（RAGオーケストレーション）
- FastAPI（APIサーバー）
- React / Next.js（UI、庁内環境制約により要検討）

## ツール

- Vitest (テスト)
- ESLint (リント)
- pytest (Python テスト)
- Docker (コンテナ化)

## アーキテクチャパターン

```
[ハイブリッドRAGアーキテクチャ]

チェック項目 → ルーター → 単純チェック(通常RAG) → ベクトル検索
                       → 関係性チェック(GraphRAG) → グラフトラバース
                       → 網羅性チェック → オントロジー参照
```

---

**生成日**: 2026-01-06
**更新日**: 2026-01-06
