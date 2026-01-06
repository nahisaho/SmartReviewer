# SmartReviewer 開発規約・コーディングガイドライン

## 1. プロジェクト概要

本ドキュメントは、SmartReviewer プロジェクトにおける開発規約とコーディングガイドラインを定義します。
MUSUBIX憲法（Article I: Library-First, Article VIII: Anti-Abstraction）に準拠しています。

---

## 2. 技術スタック

| カテゴリ | 技術 | バージョン |
|----------|------|------------|
| 言語 | Python | 3.11+ |
| プロトコル | MCP (Model Context Protocol) | 1.0+ |
| Vector DB | Qdrant | 1.7+ |
| Graph DB | Neo4j | 5.15+ |
| Object Storage | MinIO | Latest |
| Ontology | RDFLib, Owlready2 | Latest |

---

## 3. コーディング規約

### 3.1 Python スタイルガイド

- **PEP 8** に準拠
- **Ruff** をリンター/フォーマッターとして使用
- 行の最大長: **120文字**
- インデント: **スペース4つ**

### 3.2 型ヒント

すべての関数・メソッドに型ヒントを付与すること。

```python
# Good
def process_document(document_id: str, options: ProcessOptions) -> ReviewResult:
    ...

# Bad
def process_document(document_id, options):
    ...
```

### 3.3 ドキュメンテーション

Google スタイルの docstring を使用:

```python
def vector_search(query: str, top_k: int = 5) -> list[SearchResult]:
    """ベクトル類似検索を実行する。

    Args:
        query: 検索クエリ文字列
        top_k: 返却する上位件数（デフォルト: 5）

    Returns:
        検索結果のリスト（スコア降順）

    Raises:
        QdrantConnectionError: Qdrantへの接続に失敗した場合
    """
    ...
```

### 3.4 命名規則

| 種類 | 規則 | 例 |
|------|------|-----|
| モジュール | snake_case | `vector_search.py` |
| クラス | PascalCase | `DocumentProcessor` |
| 関数/メソッド | snake_case | `get_check_items()` |
| 定数 | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE` |
| MCP Tool | snake_case | `review_document` |
| MCP Resource | path形式 | `documents/{id}` |

---

## 4. MCP 実装ガイドライン

### 4.1 Tool 実装

```python
from mcp.server import Server
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("smartreviewer-core")

@mcp.tool()
async def review_document(
    document_id: str,
    check_items: list[str] | None = None
) -> dict:
    """ドキュメントをレビューし、チェック結果を返す。
    
    Args:
        document_id: レビュー対象のドキュメントID
        check_items: チェック項目のリスト（省略時は全項目）
    
    Returns:
        レビュー結果を含む辞書
    """
    ...
```

### 4.2 Resource 実装

```python
@mcp.resource("documents/{document_id}")
async def get_document(document_id: str) -> str:
    """ドキュメントの内容を取得する。"""
    ...
```

### 4.3 Prompt 実装

```python
@mcp.prompt()
async def review_template(
    document_type: str,
    check_item: str
) -> str:
    """レビュー用プロンプトテンプレートを生成する。"""
    return f"""
    以下の{document_type}について、「{check_item}」の観点でレビューしてください。
    
    ## チェック観点
    {check_item}
    
    ## 出力形式
    - 問題箇所: 具体的な箇所を引用
    - 問題点: 何が問題か
    - 修正提案: どう修正すべきか
    """
```

---

## 5. テスト規約

### 5.1 テスト構成

```
tests/
├── unit/           # 単体テスト（外部依存なし）
├── integration/    # 統合テスト（DB等との連携）
└── e2e/           # E2Eテスト（全体フロー）
```

### 5.2 テストファイル命名

```
test_{module_name}.py
```

### 5.3 テスト関数命名

```python
def test_{機能}_{条件}_{期待結果}():
    ...

# 例
def test_vector_search_with_valid_query_returns_results():
    ...

def test_vector_search_with_empty_query_raises_error():
    ...
```

### 5.4 カバレッジ目標

- 単体テスト: **80%以上**
- 統合テスト: 主要パス網羅
- E2Eテスト: ユースケース網羅

---

## 6. Git 規約

### 6.1 ブランチ戦略

| ブランチ | 用途 |
|----------|------|
| `main` | 本番リリース |
| `develop` | 開発統合 |
| `feature/{issue-id}-{description}` | 機能開発 |
| `fix/{issue-id}-{description}` | バグ修正 |
| `hotfix/{issue-id}-{description}` | 緊急修正 |

### 6.2 コミットメッセージ

Conventional Commits に準拠:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

**例:**
```
feat(rag): vector_search Tool実装

- Qdrant連携による類似検索機能を実装
- top_k, thresholdパラメータ対応

Refs: #123
```

### 6.3 プルリクエスト

- タイトル: コミットメッセージと同様の形式
- 説明: 変更内容、テスト方法、関連Issue
- レビュー: 最低1名の承認が必要

---

## 7. ドキュメント規約

### 7.1 必須ドキュメント

| ドキュメント | 場所 | 更新タイミング |
|-------------|------|----------------|
| README.md | ルート | 機能追加時 |
| CONTRIBUTING.md | ルート | 規約変更時 |
| API Reference | docs/ | API変更時 |
| ADR (Architecture Decision Records) | steering/ | 設計判断時 |

### 7.2 steering/ ディレクトリ

MUSUBIX Article IV (Project Memory) に従い、以下を記録:

- `product.md`: プロダクトビジョン
- `tech.md`: 技術決定
- `structure.md`: 構造決定
- `rules/`: 運用ルール

---

## 8. セキュリティ規約

### 8.1 認証情報管理

- 認証情報は **絶対に** コードにハードコードしない
- 環境変数または `.env` ファイルで管理
- `.env` は `.gitignore` に含める

### 8.2 依存関係

- 定期的な脆弱性スキャン（Dependabot）
- 不要な依存関係の削除
- バージョン固定（`pyproject.toml`）

---

## 9. レビューチェックリスト

- [ ] 型ヒントが付与されているか
- [ ] docstring が記述されているか
- [ ] テストが追加/更新されているか
- [ ] lint/type check がパスするか
- [ ] MCP Tool/Resource/Prompt の設計は適切か
- [ ] エラーハンドリングは適切か
- [ ] ログ出力は適切か

---

**更新日**: 2026-01-06
**バージョン**: 1.0.0
