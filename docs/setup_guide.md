# SmartReviewer 設定・デプロイメントガイド

**バージョン**: 1.0  
**最終更新**: 2026年1月6日

---

## 1. 動作環境

### 1.1 必須要件

| 項目 | 要件 |
|-----|------|
| Python | 3.12以上 |
| OS | Linux, macOS, Windows (WSL2推奨) |
| メモリ | 4GB以上推奨 |
| ディスク | 1GB以上 |

### 1.2 推奨環境

| 項目 | 推奨 |
|-----|------|
| Python | 3.12.x |
| パッケージマネージャ | pip + venv |
| IDE | VS Code + Python拡張 |

---

## 2. インストール

### 2.1 リポジトリのクローン

```bash
git clone https://github.com/your-org/SmartReviewer.git
cd SmartReviewer
```

### 2.2 仮想環境の作成

```bash
# 仮想環境の作成
python3.12 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 2.3 依存関係のインストール

```bash
# 開発環境（テストツール含む）
pip install -e ".[dev]"

# 本番環境（最小構成）
pip install -e .
```

### 2.4 依存パッケージ一覧

**メインパッケージ:**

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| mcp | >=1.0.0 | MCP SDK |
| typer | >=0.9.0 | CLI |
| pydantic | >=2.0.0 | データモデル |
| httpx | >=0.25.0 | HTTPクライアント |

**開発用パッケージ:**

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| pytest | >=7.0.0 | テスト |
| pytest-asyncio | >=0.21.0 | 非同期テスト |
| ruff | >=0.1.0 | リンター |
| mypy | >=1.0.0 | 型チェック |

---

## 3. 設定ファイル

### 3.1 musubix.config.json

MUSUBIX開発プロセス設定ファイル。

```json
{
  "version": "1.7.5",
  "projectName": "SmartReviewer",
  "mode": "development",
  "features": {
    "requirements": true,
    "design": true,
    "codegen": true,
    "testing": true
  }
}
```

### 3.2 pyproject.toml

Python プロジェクト設定ファイル。主要な設定:

```toml
[project]
name = "smartreviewer"
version = "0.1.0"
requires-python = ">=3.12"

[project.scripts]
smartreviewer = "smartreviewer.cli.main:app"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 3.3 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `SMARTREVIEWER_CONFIG` | `./config.json` | 設定ファイルパス |
| `SMARTREVIEWER_LOG_LEVEL` | `INFO` | ログレベル |
| `SMARTREVIEWER_DATA_DIR` | `./data` | データディレクトリ |

---

## 4. プロジェクト構造

### 4.1 ソースコード構成

```
src/
├── smartreviewer/          # メインパッケージ
│   ├── __init__.py
│   ├── cli/                # CLIコマンド
│   │   ├── __init__.py
│   │   └── main.py         # エントリポイント
│   ├── servers/            # MCPサーバー
│   │   ├── core/           # smartreviewer-core
│   │   ├── rag/            # smartreviewer-rag
│   │   └── knowledge/      # smartreviewer-knowledge
│   ├── review/             # レビューエンジン
│   │   ├── check_items.py  # チェック項目定義
│   │   └── executor.py     # チェック実行ロジック
│   ├── evaluation/         # 評価システム
│   │   ├── runner.py       # 評価実行
│   │   ├── analyzer.py     # 結果分析
│   │   └── datasets.py     # 評価データセット
│   └── shared/             # 共通ユーティリティ
│       ├── models/         # データモデル
│       └── utils/          # ユーティリティ
├── tests/                  # テストコード
└── scripts/                # ユーティリティスクリプト
```

### 4.2 データ構成

```
data/
├── documents/              # 入力文書
├── evaluation/             # 評価データセット
└── results/                # 実行結果

storage/
├── specs/                  # 仕様書
│   ├── requirements.md     # 要件定義
│   ├── design.md           # 設計書
│   └── tasks.md            # タスク定義
├── poc_results/            # PoC実行結果
└── analysis_reports/       # 分析レポート
```

---

## 5. コマンドリファレンス

### 5.1 CLIコマンド

```bash
# ヘルプ表示
smartreviewer --help

# 文書レビュー
smartreviewer review --file <document.md>

# 評価実行
smartreviewer evaluate --dataset <dataset_name>

# 分析レポート生成
smartreviewer analyze --results <results_dir>
```

### 5.2 開発用コマンド

```bash
# テスト実行
pytest

# 特定テストの実行
pytest tests/test_review_engine.py

# カバレッジ付きテスト
pytest --cov=src

# リンター
ruff check src/

# 型チェック
mypy src/
```

### 5.3 PoC評価コマンド

```bash
# PoC評価の実行
python scripts/run_poc.py --repeat 3 --output storage/poc_results

# 分析レポート生成
python scripts/analyze_poc.py --input storage/poc_results --output storage/analysis_reports
```

---

## 6. MCPサーバー設定

### 6.1 サーバー一覧

| サーバー名 | ポート | 機能 |
|-----------|--------|------|
| smartreviewer-core | 8001 | 文書管理・レビュー実行 |
| smartreviewer-rag | 8002 | ベクトル検索・RAG |
| smartreviewer-knowledge | 8003 | ナレッジグラフ |

### 6.2 サーバー起動

```bash
# 個別起動
python -m smartreviewer.servers.core
python -m smartreviewer.servers.rag
python -m smartreviewer.servers.knowledge

# 一括起動（開発用）
./scripts/start_servers.sh
```

### 6.3 MCP設定（mcp.json）

```json
{
  "servers": {
    "smartreviewer-core": {
      "command": "python",
      "args": ["-m", "smartreviewer.servers.core"],
      "env": {}
    },
    "smartreviewer-rag": {
      "command": "python",
      "args": ["-m", "smartreviewer.servers.rag"],
      "env": {}
    },
    "smartreviewer-knowledge": {
      "command": "python",
      "args": ["-m", "smartreviewer.servers.knowledge"],
      "env": {}
    }
  }
}
```

---

## 7. テスト設定

### 7.1 テスト構成

```
tests/
├── conftest.py             # 共通フィクスチャ
├── test_review_engine.py   # レビューエンジンテスト
├── test_check_items.py     # チェック項目テスト
├── test_evaluation.py      # 評価システムテスト
├── test_mcp_core.py        # MCP Coreサーバーテスト
├── test_mcp_rag.py         # MCP RAGサーバーテスト
└── test_mcp_knowledge.py   # MCP Knowledgeサーバーテスト
```

### 7.2 pytest設定

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

---

## 8. トラブルシューティング

### 8.1 よくある問題

#### Python バージョンエラー

```
ERROR: Requires Python 3.12+
```

**解決策**: Python 3.12以上をインストール

```bash
# pyenvの場合
pyenv install 3.12.3
pyenv local 3.12.3
```

#### MCP接続エラー

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**解決策**: MCPサーバーが起動しているか確認

```bash
# サーバーの起動状況確認
ps aux | grep smartreviewer

# サーバーの再起動
./scripts/start_servers.sh
```

#### テスト失敗

```
FAILED tests/test_*.py - AssertionError
```

**解決策**: 最新コードをpull、依存関係を再インストール

```bash
git pull
pip install -e ".[dev]"
pytest
```

### 8.2 ログの確認

```bash
# デバッグログの有効化
export SMARTREVIEWER_LOG_LEVEL=DEBUG
smartreviewer review --file test.md
```

---

## 9. 連絡先

- **技術的な質問**: GitHub Issues
- **セキュリティ問題**: security@example.com

---

**以上**
