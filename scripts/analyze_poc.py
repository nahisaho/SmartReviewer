#!/usr/bin/env python
"""
PoC分析レポート生成スクリプト
=============================

P3-3: 評価・分析
- P3-3-1: チェック結果レビュー
- P3-3-2: 是正提案妥当性評価
- P3-3-3: False Positive/Negative分析
- P3-3-4: RAG方式別精度比較分析
- P3-3-5: 改善点特定・優先度付け
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationResult,
    create_analysis_report,
    format_analysis_report,
)


def load_evaluation_results(result_dir: Path) -> list[EvaluationResult]:
    """評価結果ファイルを読み込む"""
    results = []
    
    for json_file in result_dir.glob("poc_*.json"):
        # サマリーファイルはスキップ
        if "summary" in json_file.name:
            continue
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = EvaluationResult.model_validate(data)
            results.append(result)
            print(f"📂 読み込み: {json_file.name}")
        except Exception as e:
            print(f"⚠️ 読み込みエラー: {json_file.name} - {e}")
    
    return results


def generate_analysis_report(
    result_dir: Path,
    output_dir: Path,
    verbose: bool = False,
):
    """分析レポートを生成"""
    print(f"\n{'='*60}")
    print(f"📊 SmartReviewer PoC 分析レポート生成")
    print(f"   実行日時: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    # 評価結果読み込み
    results = load_evaluation_results(result_dir)
    
    if not results:
        print("❌ 評価結果ファイルが見つかりません")
        return
    
    print(f"\n📋 {len(results)}件の評価結果を読み込みました")
    
    # 分析レポート生成
    print("\n🔍 分析実行中...")
    report = create_analysis_report(results)
    
    # テキストレポート表示
    formatted_report = format_analysis_report(report)
    print(formatted_report)
    
    # JSON出力
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON形式で保存
    json_file = output_dir / f"analysis_report_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
    print(f"\n📁 JSONレポート保存: {json_file}")
    
    # テキスト形式で保存
    text_file = output_dir / f"analysis_report_{timestamp}.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(formatted_report)
    print(f"📁 テキストレポート保存: {text_file}")
    
    # Markdownレポート生成
    md_report = generate_markdown_report(report)
    md_file = output_dir / f"analysis_report_{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"📁 Markdownレポート保存: {md_file}")
    
    print(f"\n{'='*60}")
    print(f"✅ 分析レポート生成完了")
    print(f"{'='*60}")


def generate_markdown_report(report) -> str:
    """Markdown形式のレポートを生成"""
    lines = []
    
    lines.append("# SmartReviewer PoC 評価分析レポート")
    lines.append("")
    lines.append(f"**レポートID**: {report.report_id}")
    lines.append(f"**作成日時**: {report.created_at}")
    lines.append("")
    
    lines.append("## 1. 総合メトリクス")
    lines.append("")
    lines.append("| メトリクス | 値 | 目標 | 達成状況 |")
    lines.append("|-----------|-----|-----|---------|")
    lines.append(f"| Accuracy | {report.overall_accuracy:.1%} | ≥70% | {'✅' if report.overall_accuracy >= 0.7 else '❌'} |")
    lines.append(f"| Precision | {report.overall_precision:.1%} | ≥70% | {'✅' if report.overall_precision >= 0.7 else '❌'} |")
    lines.append(f"| Recall | {report.overall_recall:.1%} | ≥70% | {'✅' if report.overall_recall >= 0.7 else '❌'} |")
    lines.append(f"| F1 Score | {report.overall_f1_score:.1%} | ≥70% | {'✅' if report.overall_f1_score >= 0.7 else '❌'} |")
    lines.append("")
    
    if report.error_analysis:
        lines.append("## 2. False Positive/Negative分析")
        lines.append("")
        lines.append("| チェック項目 | False Positive | False Negative |")
        lines.append("|-------------|----------------|----------------|")
        for error in report.error_analysis:
            lines.append(f"| {error.check_item_id} | {error.false_positive_count} | {error.false_negative_count} |")
        lines.append("")
    
    if report.check_item_analysis:
        lines.append("## 3. チェック項目別分析")
        lines.append("")
        lines.append("| チェック項目 | Accuracy | Precision | Recall | F1 Score |")
        lines.append("|-------------|----------|-----------|--------|----------|")
        for check_id, analysis in report.check_item_analysis.items():
            lines.append(
                f"| {check_id} | "
                f"{analysis['accuracy']:.1%} | "
                f"{analysis['precision']:.1%} | "
                f"{analysis['recall']:.1%} | "
                f"{analysis['f1_score']:.1%} |"
            )
        lines.append("")
    
    lines.append("## 4. 再現性分析")
    lines.append("")
    lines.append(f"**再現性率**: {report.reproducibility_rate:.1%}")
    lines.append("")
    if report.reproducibility_notes:
        for note in report.reproducibility_notes:
            lines.append(f"- {note}")
        lines.append("")
    
    if report.improvement_suggestions:
        lines.append("## 5. 改善提案")
        lines.append("")
        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            priority_badge = {
                "high": "🔴 HIGH",
                "medium": "🟡 MEDIUM",
                "low": "🟢 LOW"
            }.get(suggestion.priority, suggestion.priority)
            
            lines.append(f"### {i}. {suggestion.description}")
            lines.append("")
            lines.append(f"- **優先度**: {priority_badge}")
            lines.append(f"- **カテゴリ**: {suggestion.category}")
            lines.append(f"- **期待効果**: {suggestion.expected_impact}")
            lines.append(f"- **工数見積**: {suggestion.effort_estimate}")
            lines.append("")
    
    lines.append("## 6. 結論")
    lines.append("")
    
    # 結論の自動生成
    if report.overall_accuracy >= 0.7 and report.overall_precision >= 0.7 and report.overall_recall >= 0.7:
        lines.append("✅ **PoCの目標精度を達成しました。**")
        lines.append("")
        lines.append("ルールベースチェックにより、基本設計書・テスト計画書のレビューが")
        lines.append("一定の精度で自動化可能であることが確認されました。")
    else:
        lines.append("⚠️ **一部のメトリクスが目標値に到達していません。**")
        lines.append("")
        lines.append("改善提案に従って以下の対策を実施することを推奨します：")
        if report.overall_accuracy < 0.7:
            lines.append("- チェックロジックの精度向上")
        if report.overall_precision < 0.7:
            lines.append("- False Positive削減のための判定条件厳密化")
        if report.overall_recall < 0.7:
            lines.append("- False Negative削減のためのチェック網羅性向上")
    
    lines.append("")
    lines.append("### 次のステップ")
    lines.append("")
    lines.append("1. 改善提案の優先度High項目への対応")
    lines.append("2. LLM統合による高精度チェックの実装")
    lines.append("3. 評価データセットの拡充")
    lines.append("4. Phase 4（改善・報告書作成）への移行")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartReviewer PoC分析レポート生成")
    parser.add_argument(
        "--input",
        type=str,
        default="storage/poc_results",
        help="評価結果ディレクトリ (default: storage/poc_results)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="storage/analysis_reports",
        help="レポート出力ディレクトリ (default: storage/analysis_reports)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細出力",
    )
    
    args = parser.parse_args()
    
    generate_analysis_report(
        result_dir=Path(args.input),
        output_dir=Path(args.output),
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
