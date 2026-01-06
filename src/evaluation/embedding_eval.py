"""
Embedding Model Evaluation Script
=================================

Embeddingモデルの日本語検索性能を評価
"""

import time
import argparse
from pathlib import Path

from src.shared.config.settings import settings
from src.shared.config.clients import get_qdrant_client
from src.shared.processing.embedding import EmbeddingModel
from src.evaluation.metrics import (
    EmbeddingEvaluator,
    save_eval_results,
)


# 評価用クエリセット（ガイドライン検索）
EVAL_QUERIES = [
    {
        "query": "基本設計書に必須のセクション構成は何ですか",
        "relevant_sections": ["第3編 3.2.2", "第3編 3.2.1"],
    },
    {
        "query": "システム構成図の記載要件について",
        "relevant_sections": ["第3編 3.2.2"],
    },
    {
        "query": "データモデル設計の指針",
        "relevant_sections": ["第3編 3.2.4"],
    },
    {
        "query": "外部インターフェースの設計方法",
        "relevant_sections": ["第3編 3.2.5"],
    },
    {
        "query": "非機能要件の設計における注意点",
        "relevant_sections": ["第3編 3.2.6"],
    },
    {
        "query": "テスト計画書のテストレベル定義",
        "relevant_sections": ["第3編 3.3.2"],
    },
    {
        "query": "テスト開始基準と終了基準の設定",
        "relevant_sections": ["第3編 3.3.3"],
    },
    {
        "query": "テスト環境構築のガイドライン",
        "relevant_sections": ["第3編 3.3.6"],
    },
    {
        "query": "障害管理の手順について",
        "relevant_sections": ["第3編 3.3.7"],
    },
    {
        "query": "セキュリティ設計の要件",
        "relevant_sections": ["第4編 第5章"],
    },
]


def evaluate_embedding_model(
    model_name: str = None,
    collection_name: str = "guidelines",
    top_k: int = 10,
) -> dict:
    """
    Embeddingモデルを評価
    
    Args:
        model_name: 評価対象モデル名（Noneの場合は設定から取得）
        collection_name: 検索対象コレクション
        top_k: 検索件数
        
    Returns:
        評価結果のdict
    """
    model_name = model_name or settings.embedding.model_name
    print(f"Evaluating embedding model: {model_name}")
    print(f"Collection: {collection_name}")
    print("=" * 60)
    
    # モデルとクライアント初期化
    embedding_model = EmbeddingModel()
    qdrant_client = get_qdrant_client()
    
    evaluator = EmbeddingEvaluator(model_name)
    
    for i, eval_item in enumerate(EVAL_QUERIES):
        query = eval_item["query"]
        relevant_sections = eval_item["relevant_sections"]
        
        print(f"\n[{i+1}/{len(EVAL_QUERIES)}] Query: {query}")
        
        # 検索実行と時間計測
        start_time = time.time()
        query_embedding = embedding_model.embed_query(query)
        
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        inference_time_ms = (time.time() - start_time) * 1000
        
        # 検索結果からセクション情報を取得
        retrieved_sections = []
        for result in results:
            section = result.payload.get("section", "")
            if section:
                retrieved_sections.append(section)
        
        # 評価
        evaluator.evaluate_query(
            query=query,
            relevant_docs=relevant_sections,
            retrieved_docs=retrieved_sections,
            inference_time_ms=inference_time_ms,
        )
        
        # 結果表示
        print(f"  Retrieved: {retrieved_sections[:5]}")
        print(f"  Relevant: {relevant_sections}")
        print(f"  Time: {inference_time_ms:.1f}ms")
    
    # サマリー取得
    summary = evaluator.get_summary()
    
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Model: {summary.model_name}")
    print(f"Total Queries: {summary.total_queries}")
    print(f"Recall@1:  {summary.recall_at_1:.3f}")
    print(f"Recall@5:  {summary.recall_at_5:.3f}")
    print(f"Recall@10: {summary.recall_at_10:.3f}")
    print(f"MRR:       {summary.mrr:.3f}")
    print(f"Avg Time:  {summary.avg_inference_time_ms:.1f}ms")
    
    return summary.to_dict()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Evaluate embedding model")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to evaluate",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="guidelines",
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to retrieve",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for results",
    )
    
    args = parser.parse_args()
    
    results = evaluate_embedding_model(
        model_name=args.model,
        collection_name=args.collection,
        top_k=args.top_k,
    )
    
    if args.output:
        output_path = Path(args.output)
        save_eval_results([results], output_path)


if __name__ == "__main__":
    main()
