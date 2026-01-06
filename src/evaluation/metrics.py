"""
Model Evaluation Module
=======================

Embedding / LLM モデル評価用ユーティリティ
"""

import time
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

import numpy as np


@dataclass
class EmbeddingEvalResult:
    """Embedding評価結果"""
    model_name: str
    recall_at_1: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    mrr: float = 0.0
    ndcg_at_10: float = 0.0
    avg_inference_time_ms: float = 0.0
    total_queries: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class LLMEvalResult:
    """LLM評価結果"""
    model_name: str
    task: str
    accuracy: float = 0.0
    f1_score: float = 0.0
    rouge_l: float = 0.0
    avg_inference_time_ms: float = 0.0
    total_samples: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


def calculate_recall_at_k(
    relevant_docs: list[str],
    retrieved_docs: list[str],
    k: int
) -> float:
    """
    Recall@k を計算
    
    Args:
        relevant_docs: 正解文書IDリスト
        retrieved_docs: 検索結果文書IDリスト
        k: 上位k件
        
    Returns:
        Recall@k スコア
    """
    if not relevant_docs:
        return 0.0
    
    retrieved_set = set(retrieved_docs[:k])
    relevant_set = set(relevant_docs)
    
    hits = len(retrieved_set & relevant_set)
    return hits / len(relevant_set)


def calculate_mrr(
    relevant_docs: list[str],
    retrieved_docs: list[str]
) -> float:
    """
    Mean Reciprocal Rank を計算
    
    Args:
        relevant_docs: 正解文書IDリスト
        retrieved_docs: 検索結果文書IDリスト
        
    Returns:
        MRRスコア
    """
    relevant_set = set(relevant_docs)
    
    for i, doc_id in enumerate(retrieved_docs):
        if doc_id in relevant_set:
            return 1.0 / (i + 1)
    
    return 0.0


def calculate_ndcg_at_k(
    relevance_scores: list[float],
    k: int
) -> float:
    """
    nDCG@k を計算
    
    Args:
        relevance_scores: 検索結果の関連度スコアリスト（降順）
        k: 上位k件
        
    Returns:
        nDCG@k スコア
    """
    if not relevance_scores:
        return 0.0
    
    # DCG計算
    dcg = 0.0
    for i, score in enumerate(relevance_scores[:k]):
        dcg += (2 ** score - 1) / np.log2(i + 2)
    
    # Ideal DCG計算
    ideal_scores = sorted(relevance_scores, reverse=True)[:k]
    idcg = 0.0
    for i, score in enumerate(ideal_scores):
        idcg += (2 ** score - 1) / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def calculate_f1(
    precision: float,
    recall: float
) -> float:
    """F1スコアを計算"""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def calculate_rouge_l(
    reference: str,
    hypothesis: str
) -> float:
    """
    ROUGE-L (LCS based) を計算
    
    Args:
        reference: 参照テキスト
        hypothesis: 生成テキスト
        
    Returns:
        ROUGE-L F1スコア
    """
    def lcs_length(x: str, y: str) -> int:
        """最長共通部分列の長さを計算"""
        m, n = len(x), len(y)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if x[i-1] == y[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    if not reference or not hypothesis:
        return 0.0
    
    # 文字単位でLCS計算
    lcs_len = lcs_length(reference, hypothesis)
    
    precision = lcs_len / len(hypothesis) if hypothesis else 0.0
    recall = lcs_len / len(reference) if reference else 0.0
    
    return calculate_f1(precision, recall)


class EmbeddingEvaluator:
    """Embeddingモデル評価クラス"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.results: list[dict] = []
    
    def evaluate_query(
        self,
        query: str,
        relevant_docs: list[str],
        retrieved_docs: list[str],
        inference_time_ms: float
    ):
        """
        1クエリの評価結果を記録
        """
        result = {
            "query": query,
            "recall_at_1": calculate_recall_at_k(relevant_docs, retrieved_docs, 1),
            "recall_at_5": calculate_recall_at_k(relevant_docs, retrieved_docs, 5),
            "recall_at_10": calculate_recall_at_k(relevant_docs, retrieved_docs, 10),
            "mrr": calculate_mrr(relevant_docs, retrieved_docs),
            "inference_time_ms": inference_time_ms,
        }
        self.results.append(result)
    
    def get_summary(self) -> EmbeddingEvalResult:
        """評価サマリーを取得"""
        if not self.results:
            return EmbeddingEvalResult(model_name=self.model_name)
        
        return EmbeddingEvalResult(
            model_name=self.model_name,
            recall_at_1=np.mean([r["recall_at_1"] for r in self.results]),
            recall_at_5=np.mean([r["recall_at_5"] for r in self.results]),
            recall_at_10=np.mean([r["recall_at_10"] for r in self.results]),
            mrr=np.mean([r["mrr"] for r in self.results]),
            avg_inference_time_ms=np.mean([r["inference_time_ms"] for r in self.results]),
            total_queries=len(self.results),
        )


class LLMEvaluator:
    """LLMモデル評価クラス"""
    
    def __init__(self, model_name: str, task: str):
        self.model_name = model_name
        self.task = task
        self.results: list[dict] = []
    
    def evaluate_classification(
        self,
        predicted: str,
        actual: str,
        inference_time_ms: float
    ):
        """分類タスクの評価結果を記録"""
        result = {
            "predicted": predicted,
            "actual": actual,
            "correct": predicted == actual,
            "inference_time_ms": inference_time_ms,
        }
        self.results.append(result)
    
    def evaluate_generation(
        self,
        generated: str,
        reference: str,
        inference_time_ms: float
    ):
        """生成タスクの評価結果を記録"""
        result = {
            "generated": generated,
            "reference": reference,
            "rouge_l": calculate_rouge_l(reference, generated),
            "inference_time_ms": inference_time_ms,
        }
        self.results.append(result)
    
    def get_summary(self) -> LLMEvalResult:
        """評価サマリーを取得"""
        if not self.results:
            return LLMEvalResult(model_name=self.model_name, task=self.task)
        
        # 分類タスクの場合
        if "correct" in self.results[0]:
            correct = sum(1 for r in self.results if r["correct"])
            accuracy = correct / len(self.results)
            
            return LLMEvalResult(
                model_name=self.model_name,
                task=self.task,
                accuracy=accuracy,
                avg_inference_time_ms=np.mean([r["inference_time_ms"] for r in self.results]),
                total_samples=len(self.results),
            )
        
        # 生成タスクの場合
        else:
            return LLMEvalResult(
                model_name=self.model_name,
                task=self.task,
                rouge_l=np.mean([r["rouge_l"] for r in self.results]),
                avg_inference_time_ms=np.mean([r["inference_time_ms"] for r in self.results]),
                total_samples=len(self.results),
            )


def save_eval_results(
    results: list[dict],
    output_path: Path
):
    """評価結果をJSONファイルに保存"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {output_path}")


def load_eval_results(input_path: Path) -> list[dict]:
    """評価結果をJSONファイルから読み込み"""
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)
