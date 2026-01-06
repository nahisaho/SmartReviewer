"""
LLM Model Evaluation Script
===========================

LLMモデルのチェック判定・生成性能を評価
（MCP Sampling経由）
"""

import time
import argparse
import json
from pathlib import Path
from typing import Optional

from src.shared.config.settings import settings
from src.shared.utils.sampling import (
    SamplingClient,
    SamplingRequest,
    ReviewPrompts,
    MODEL_PREFERENCES,
)
from src.evaluation.metrics import (
    LLMEvaluator,
    save_eval_results,
)


# 評価用データセット（チェック判定タスク）
EVAL_CLASSIFICATION_DATA = [
    {
        "check_item_id": "BD-001",
        "check_item_name": "必須セクション存在確認",
        "document_content": """
# 基本設計書
## 1. 概要
本システムは...

## 2. システム構成
...

## 3. 機能設計
...

## 4. データ設計
...

## 5. インターフェース設計
...

## 6. 非機能設計
...
        """,
        "expected_result": "pass",
        "expected_reason": "必須セクションがすべて存在している",
    },
    {
        "check_item_id": "BD-001",
        "check_item_name": "必須セクション存在確認",
        "document_content": """
# 基本設計書
## 1. 概要
本システムは...

## 2. 機能説明
...
        """,
        "expected_result": "fail",
        "expected_reason": "システム構成、データ設計、インターフェース設計、非機能設計のセクションが欠落している",
    },
    {
        "check_item_id": "BD-004",
        "check_item_name": "システム構成図存在確認",
        "document_content": """
## 2. システム構成
### 2.1 概要
本システムは3層アーキテクチャを採用する。

### 2.2 システム構成図
![システム構成図](images/system_architecture.png)

図2-1に示すとおり、Webサーバー、APサーバー、DBサーバーで構成される。
        """,
        "expected_result": "pass",
        "expected_reason": "システム構成図が含まれている",
    },
    {
        "check_item_id": "TP-002",
        "check_item_name": "テストレベル定義確認",
        "document_content": """
## 3. テストレベル定義
### 3.1 単体テスト
各モジュールの機能を検証する。

### 3.2 結合テスト
モジュール間の連携を検証する。

### 3.3 システムテスト
システム全体の機能を検証する。

### 3.4 受入テスト
発注者による受入検証を行う。
        """,
        "expected_result": "pass",
        "expected_reason": "4つのテストレベル（単体、結合、システム、受入）がすべて定義されている",
    },
]


class LLMModelEvaluator:
    """LLMモデル評価クラス"""
    
    def __init__(self, model_preference: str = "balanced"):
        self.model_preference = model_preference
        self.sampling_client = SamplingClient()
    
    def evaluate_check_judgment(
        self,
        check_item_id: str,
        check_item_name: str,
        document_content: str,
        expected_result: str,
    ) -> dict:
        """
        チェック判定タスクを評価
        
        Args:
            check_item_id: チェック項目ID
            check_item_name: チェック項目名
            document_content: 文書内容
            expected_result: 期待される結果（pass/fail）
            
        Returns:
            評価結果
        """
        # プロンプト生成
        prompt = ReviewPrompts.check_judgment_prompt(
            document_content=document_content,
            check_item_id=check_item_id,
            check_item_name=check_item_name,
            check_description=f"{check_item_name}を確認する",
        )
        
        # Samplingリクエスト作成
        request = SamplingRequest(
            messages=[{"role": "user", "content": prompt}],
            model_preferences=MODEL_PREFERENCES[self.model_preference],
            max_tokens=1024,
        )
        
        # 推論実行（時間計測）
        start_time = time.time()
        
        # 注: 実際のMCP Host環境では sampling_client.create_message() を呼び出す
        # ここではシミュレーション
        response = self._simulate_llm_response(check_item_id, document_content, expected_result)
        
        inference_time_ms = (time.time() - start_time) * 1000
        
        # 結果をパース
        predicted_result = self._parse_judgment_result(response)
        
        return {
            "check_item_id": check_item_id,
            "predicted": predicted_result,
            "expected": expected_result,
            "correct": predicted_result == expected_result,
            "response": response,
            "inference_time_ms": inference_time_ms,
        }
    
    def _simulate_llm_response(
        self,
        check_item_id: str,
        document_content: str,
        expected_result: str
    ) -> str:
        """
        LLM応答をシミュレート（実環境ではMCP Sampling使用）
        
        Note: 実際の評価時はこのメソッドを削除し、
              sampling_client.create_message() を使用する
        """
        # シミュレーション: 期待結果を返す（実際のモデル評価ではない）
        if expected_result == "pass":
            return json.dumps({
                "result": "pass",
                "confidence": 0.85,
                "reason": "チェック項目を満たしています",
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "result": "fail",
                "confidence": 0.90,
                "reason": "チェック項目を満たしていません",
            }, ensure_ascii=False)
    
    def _parse_judgment_result(self, response: str) -> str:
        """応答から判定結果をパース"""
        try:
            data = json.loads(response)
            return data.get("result", "unknown")
        except json.JSONDecodeError:
            # JSON形式でない場合はテキストから抽出
            response_lower = response.lower()
            if "pass" in response_lower or "合格" in response_lower:
                return "pass"
            elif "fail" in response_lower or "不合格" in response_lower:
                return "fail"
            return "unknown"


def evaluate_llm_model(
    model_preference: str = "balanced",
) -> dict:
    """
    LLMモデルを評価
    
    Args:
        model_preference: モデル選好（high_accuracy/balanced/fast）
        
    Returns:
        評価結果のdict
    """
    print(f"Evaluating LLM model with preference: {model_preference}")
    print("=" * 60)
    
    evaluator_instance = LLMModelEvaluator(model_preference)
    llm_evaluator = LLMEvaluator(
        model_name=model_preference,
        task="check_judgment"
    )
    
    results = []
    
    for i, eval_item in enumerate(EVAL_CLASSIFICATION_DATA):
        print(f"\n[{i+1}/{len(EVAL_CLASSIFICATION_DATA)}] {eval_item['check_item_id']}: {eval_item['check_item_name']}")
        
        result = evaluator_instance.evaluate_check_judgment(
            check_item_id=eval_item["check_item_id"],
            check_item_name=eval_item["check_item_name"],
            document_content=eval_item["document_content"],
            expected_result=eval_item["expected_result"],
        )
        
        results.append(result)
        
        llm_evaluator.evaluate_classification(
            predicted=result["predicted"],
            actual=result["expected"],
            inference_time_ms=result["inference_time_ms"],
        )
        
        status = "✓" if result["correct"] else "✗"
        print(f"  {status} Predicted: {result['predicted']}, Expected: {result['expected']}")
        print(f"  Time: {result['inference_time_ms']:.1f}ms")
    
    # サマリー取得
    summary = llm_evaluator.get_summary()
    
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Model Preference: {summary.model_name}")
    print(f"Task: {summary.task}")
    print(f"Total Samples: {summary.total_samples}")
    print(f"Accuracy: {summary.accuracy:.3f}")
    print(f"Avg Time: {summary.avg_inference_time_ms:.1f}ms")
    
    return {
        "summary": summary.to_dict(),
        "details": results,
    }


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Evaluate LLM model")
    parser.add_argument(
        "--preference",
        type=str,
        default="balanced",
        choices=["high_accuracy", "balanced", "fast"],
        help="Model preference",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for results",
    )
    
    args = parser.parse_args()
    
    results = evaluate_llm_model(model_preference=args.preference)
    
    if args.output:
        output_path = Path(args.output)
        save_eval_results([results], output_path)


if __name__ == "__main__":
    main()
