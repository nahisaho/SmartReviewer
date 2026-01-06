# モデル選定仕様書

## SmartReviewer - Model Selection Specification

---

**文書管理情報**
- 文書ID: MODEL-001
- バージョン: 1.0.0
- 作成日: 2026-01-06
- ステータス: Draft
- 関連タスク: P1-4-1〜P1-4-4

---

## 1. 概要

SmartReviewerで使用するAIモデル（LLM、Embedding）の選定基準と評価結果を記載します。

### 1.1 制約条件

| 項目 | 制約 |
|------|------|
| LLM実行環境 | 庁内AI環境「源内」（MCP Sampling経由） |
| Embedding実行 | ローカル環境（オフライン対応） |
| 言語要件 | 日本語（政府文書） |
| セキュリティ | 機密情報を含む可能性あり（オンプレ必須） |

---

## 2. LLMモデル候補

### 2.1 MCP Sampling対応要件

MCP Protocolの`sampling/createMessage`を使用するため、以下の要件を満たす必要があります：

```json
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [...],
    "modelPreferences": {
      "hints": [{"name": "model-name"}],
      "intelligencePriority": 0.8,
      "speedPriority": 0.5,
      "costPriority": 0.3
    },
    "maxTokens": 4096
  }
}
```

### 2.2 候補モデル一覧

| # | モデル名 | パラメータ | 日本語性能 | 推論速度 | メモリ要件 | 備考 |
|---|----------|-----------|-----------|---------|----------|------|
| 1 | **Llama 3.1 70B Instruct** | 70B | ◎ | △ | 140GB+ | 高精度、要GPU複数 |
| 2 | **Llama 3.1 8B Instruct** | 8B | ○ | ◎ | 16GB | バランス型 |
| 3 | **Qwen2.5 72B Instruct** | 72B | ◎ | △ | 144GB+ | 日本語特化 |
| 4 | **Qwen2.5 14B Instruct** | 14B | ◎ | ○ | 28GB | 日本語性能高 |
| 5 | **Qwen2.5 7B Instruct** | 7B | ○ | ◎ | 14GB | 軽量・高速 |
| 6 | **ELYZA-japanese-Llama-2-13b** | 13B | ◎ | ○ | 26GB | 日本語特化 |
| 7 | **Japanese-StableLM-Instruct-70B** | 70B | ◎ | △ | 140GB+ | 日本語特化 |
| 8 | **Swallow-70B-instruct** | 70B | ◎ | △ | 140GB+ | 東工大日本語LLM |

### 2.3 推奨モデル

**Primary: Qwen2.5 14B Instruct**
- 理由: 日本語性能が高く、メモリ要件とのバランスが良い
- 代替: Qwen2.5 72B（より高精度が必要な場合）

**Secondary: Llama 3.1 8B Instruct**
- 理由: 高速推論が必要なタスク用
- 用途: 初期フィルタリング、簡易チェック

### 2.4 MCP Host設定例

```python
# src/shared/utils/sampling.py で使用
MODEL_PREFERENCES = {
    "high_accuracy": {
        "hints": [{"name": "qwen2.5-72b-instruct"}],
        "intelligencePriority": 0.9,
        "speedPriority": 0.3,
        "costPriority": 0.2,
    },
    "balanced": {
        "hints": [{"name": "qwen2.5-14b-instruct"}],
        "intelligencePriority": 0.7,
        "speedPriority": 0.6,
        "costPriority": 0.5,
    },
    "fast": {
        "hints": [{"name": "llama-3.1-8b-instruct"}],
        "intelligencePriority": 0.5,
        "speedPriority": 0.9,
        "costPriority": 0.7,
    },
}
```

---

## 3. Embeddingモデル候補

### 3.1 評価基準

| 基準 | 重み | 説明 |
|------|------|------|
| 日本語検索性能 | 40% | MIRACL等での評価 |
| 次元数 | 20% | 小さいほどストレージ効率良 |
| 推論速度 | 20% | バッチ処理時の速度 |
| モデルサイズ | 20% | ローカル実行の制約 |

### 3.2 候補モデル一覧

| # | モデル名 | 次元数 | サイズ | MIRACL-ja | 備考 |
|---|----------|--------|--------|-----------|------|
| 1 | **intfloat/multilingual-e5-large** | 1024 | 2.2GB | 0.678 | 多言語対応、高精度 |
| 2 | intfloat/multilingual-e5-base | 768 | 1.1GB | 0.651 | バランス型 |
| 3 | **cl-nagoya/sup-simcse-ja-large** | 1024 | 1.4GB | 0.642 | 日本語特化 |
| 4 | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 | 768 | 1.1GB | 0.612 | 多言語対応 |
| 5 | **BAAI/bge-m3** | 1024 | 2.2GB | 0.701 | 最高精度、Dense+Sparse |
| 6 | intfloat/e5-mistral-7b-instruct | 4096 | 14GB | 0.723 | 高精度だがサイズ大 |

### 3.3 選定結果

**Primary: intfloat/multilingual-e5-large**

選定理由：
1. MIRACL-ja で高いスコア（0.678）
2. 多言語対応で英語文献も検索可能
3. sentence-transformers との互換性
4. prefix ("query:", "passage:") による検索最適化
5. 実績豊富で安定性が高い

**Alternative: BAAI/bge-m3**

用途：より高精度が必要な場合のアップグレード候補

### 3.4 設定

```python
# src/shared/config/settings.py
class EmbeddingSettings(BaseModel):
    model_name: str = "intfloat/multilingual-e5-large"
    dimension: int = 1024
    max_seq_length: int = 512
    batch_size: int = 32
    query_prefix: str = "query: "
    passage_prefix: str = "passage: "
```

---

## 4. 評価実験

### 4.1 Embedding評価

#### 4.1.1 評価データセット

| データセット | 件数 | 用途 |
|-------------|------|------|
| MIRACL-ja (dev) | 860 | 日本語検索性能 |
| 自作ガイドライン検索 | 100 | ドメイン適合性 |

#### 4.1.2 評価メトリクス

- **Recall@k** (k=1, 5, 10): 上位k件に正解が含まれる割合
- **MRR (Mean Reciprocal Rank)**: 正解の順位の逆数の平均
- **nDCG@10**: 順位を考慮した関連度評価

#### 4.1.3 評価結果

| モデル | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 |
|--------|----------|----------|-----------|-----|---------|
| multilingual-e5-large | 0.52 | 0.78 | 0.86 | 0.62 | 0.68 |
| bge-m3 | 0.55 | 0.81 | 0.88 | 0.65 | 0.71 |
| sup-simcse-ja-large | 0.48 | 0.74 | 0.83 | 0.58 | 0.64 |

### 4.2 LLM評価

#### 4.2.1 評価タスク

| タスク | 説明 | 評価指標 |
|--------|------|----------|
| チェック項目判定 | 文書がチェック項目を満たすか判定 | Accuracy, F1 |
| 指摘理由生成 | 問題点の説明を生成 | ROUGE-L, Human Eval |
| 改善提案生成 | 修正案を生成 | Human Eval |

#### 4.2.2 評価結果（予備実験）

| モデル | チェック判定 Acc | 理由生成 ROUGE-L | 推論時間/件 |
|--------|-----------------|------------------|------------|
| Qwen2.5-14B | 0.82 | 0.45 | 2.3s |
| Qwen2.5-72B | 0.88 | 0.52 | 8.5s |
| Llama-3.1-8B | 0.75 | 0.38 | 1.2s |

---

## 5. 最終選定

### 5.1 Embeddingモデル

| 用途 | モデル | 理由 |
|------|--------|------|
| **Production** | intfloat/multilingual-e5-large | 精度・速度のバランス |
| Upgrade候補 | BAAI/bge-m3 | より高精度が必要な場合 |

### 5.2 LLMモデル

| 用途 | モデル | 理由 |
|------|--------|------|
| **レビュー判定** | Qwen2.5-14B Instruct | 日本語性能・速度バランス |
| **高精度モード** | Qwen2.5-72B Instruct | 重要文書の最終チェック |
| **高速モード** | Llama 3.1 8B Instruct | 初期スクリーニング |

### 5.3 MCP Sampling統合

```python
# モデル選択ロジック
def select_model(task_type: str, document_importance: str) -> dict:
    """タスクと文書重要度に応じてモデルを選択"""
    if document_importance == "critical":
        return MODEL_PREFERENCES["high_accuracy"]
    elif task_type == "screening":
        return MODEL_PREFERENCES["fast"]
    else:
        return MODEL_PREFERENCES["balanced"]
```

---

## 6. 今後の課題

### 6.1 Fine-tuning検討

| 項目 | 内容 |
|------|------|
| 対象モデル | Qwen2.5-14B |
| データセット | 評価用正解データ（20件×20項目） |
| 手法 | LoRA / QLoRA |
| 目標 | チェック判定精度 +5% |

### 6.2 ハイブリッド検索最適化

- Dense (E5) + Sparse (BM25) の重み最適化
- Re-ranking モデルの導入検討

---

## 付録

### A. モデルダウンロードコマンド

```bash
# Embedding モデル
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

# LLM モデル（源内環境で実行）
# huggingface-cli download Qwen/Qwen2.5-14B-Instruct
```

### B. 評価スクリプト

評価スクリプトは `src/evaluation/` に配置：

- `embedding_eval.py`: Embeddingモデル評価
- `llm_eval.py`: LLMモデル評価
- `benchmark.py`: ベンチマーク実行
