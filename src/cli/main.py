"""
SmartReviewer CLI Main
======================

CLIエントリーポイント
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel

from src.review.engine import ReviewEngine
from src.review.models import ReviewRequest, ReviewOptions, ReviewStatus


# ==============================================
# Typer App
# ==============================================

app = typer.Typer(
    name="smartreviewer",
    help="SmartReviewer - 文書レビュー支援AIエージェント",
    add_completion=False,
)

console = Console()


# ==============================================
# Review Commands
# ==============================================

@app.command("review")
def review_document(
    file: Path = typer.Argument(..., help="レビュー対象の文書ファイル"),
    document_type: str = typer.Option(
        "basic_design",
        "--type", "-t",
        help="文書タイプ (basic_design / test_plan)",
    ),
    check_items: Optional[str] = typer.Option(
        None,
        "--checks", "-c",
        help="チェック項目ID（カンマ区切り）",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="結果出力ファイル（省略時は標準出力）",
    ),
    format: str = typer.Option(
        "markdown",
        "--format", "-f",
        help="出力形式 (json / markdown)",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        help="並列実行/順次実行",
    ),
) -> None:
    """
    文書をレビューする
    """
    # ファイル存在確認
    if not file.exists():
        console.print(f"[red]エラー: ファイルが見つかりません: {file}[/red]")
        raise typer.Exit(1)
    
    # 文書タイプ検証
    if document_type not in ["basic_design", "test_plan"]:
        console.print(f"[red]エラー: 無効な文書タイプ: {document_type}[/red]")
        raise typer.Exit(1)
    
    # 文書読み込み
    content = file.read_text(encoding="utf-8")
    
    # チェック項目解析
    check_item_ids = None
    if check_items:
        check_item_ids = [c.strip() for c in check_items.split(",")]
    
    # レビュー実行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("レビュー実行中...", total=None)
        
        result = asyncio.run(_run_review(
            document_id=str(file),
            document_content=content,
            document_type=document_type,
            check_item_ids=check_item_ids,
            parallel=parallel,
        ))
        
        progress.update(task, completed=True)
    
    # 結果出力
    if format == "json":
        output_content = json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
    else:
        output_content = _format_result_markdown(result)
    
    if output:
        output.write_text(output_content, encoding="utf-8")
        console.print(f"[green]結果を保存しました: {output}[/green]")
    else:
        if format == "markdown":
            console.print(Markdown(output_content))
        else:
            console.print(output_content)
    
    # 終了コード設定
    if result.status == ReviewStatus.FAILED:
        raise typer.Exit(2)
    elif result.metadata.checks_failed > 0:
        raise typer.Exit(1)


async def _run_review(
    document_id: str,
    document_content: str,
    document_type: str,
    check_item_ids: Optional[list[str]],
    parallel: bool,
):
    """レビュー実行（非同期）"""
    engine = ReviewEngine(use_llm=False)
    
    request = ReviewRequest(
        document_id=document_id,
        document_content=document_content,
        document_type=document_type,
        check_item_ids=check_item_ids,
        options=ReviewOptions(parallel=parallel),
    )
    
    return await engine.review_document(request)


def _format_result_markdown(result) -> str:
    """結果をMarkdown形式でフォーマット"""
    lines = [
        f"# レビュー結果",
        "",
        f"- **レビューID**: {result.review_id}",
        f"- **文書ID**: {result.document_id}",
        f"- **文書タイプ**: {result.document_type}",
        f"- **ステータス**: {result.status.value}",
        f"- **総合結果**: {result.overall_result.value}",
        f"- **実行時間**: {result.execution_time_ms}ms",
        "",
        "## サマリー",
        "",
        f"| 項目 | 件数 |",
        f"|------|------|",
        f"| 実行チェック数 | {result.metadata.checks_executed} |",
        f"| 合格 | {result.metadata.checks_passed} |",
        f"| 不合格 | {result.metadata.checks_failed} |",
        f"| 警告 | {result.metadata.checks_warning} |",
        f"| スキップ | {result.metadata.checks_skipped} |",
        f"| 総指摘数 | {result.total_findings} |",
        f"| 重大指摘 | {result.critical_findings} |",
        "",
    ]
    
    # チェック結果詳細
    if result.check_results:
        lines.append("## チェック結果詳細")
        lines.append("")
        
        for check_result in result.check_results:
            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "warning": "⚠️",
                "skip": "⏭️",
            }.get(check_result.status.value, "❓")
            
            lines.append(f"### {status_icon} {check_result.check_item_id}: {check_result.check_item_name}")
            lines.append(f"- 結果: **{check_result.status.value.upper()}**")
            lines.append(f"- 確信度: {check_result.confidence:.0%}")
            
            if check_result.findings:
                lines.append(f"- 指摘事項:")
                for finding in check_result.findings:
                    lines.append(f"  - [{finding.severity.value}] {finding.title}")
                    lines.append(f"    - {finding.description}")
            
            if check_result.suggestions:
                lines.append(f"- 改善提案:")
                for suggestion in check_result.suggestions:
                    lines.append(f"  - {suggestion.title}")
                    lines.append(f"    - {suggestion.description}")
            
            lines.append("")
    
    return "\n".join(lines)


# ==============================================
# Check Items Commands
# ==============================================

@app.command("check-items")
def list_check_items(
    document_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="文書タイプでフィルタ",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="カテゴリでフィルタ",
    ),
    format: str = typer.Option(
        "table",
        "--format", "-f",
        help="出力形式 (table / json)",
    ),
) -> None:
    """
    チェック項目一覧を表示
    """
    from src.knowledge.schema import CHECK_ITEMS_DATA
    
    items = CHECK_ITEMS_DATA
    
    if document_type:
        items = [i for i in items if i["document_type"] == document_type]
    
    if category:
        items = [i for i in items if i["category"] == category]
    
    if format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    
    # テーブル表示
    table = Table(title="チェック項目一覧")
    table.add_column("ID", style="cyan")
    table.add_column("名前", style="green")
    table.add_column("カテゴリ")
    table.add_column("重要度")
    table.add_column("文書タイプ")
    
    for item in items:
        severity_color = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "dim",
        }.get(item["severity"], "white")
        
        table.add_row(
            item["id"],
            item["name"],
            item["category"],
            f"[{severity_color}]{item['severity']}[/{severity_color}]",
            item["document_type"],
        )
    
    console.print(table)
    console.print(f"\n合計: {len(items)} 件")


# ==============================================
# Server Commands
# ==============================================

@app.command("server")
def server_info(
    server_name: Optional[str] = typer.Argument(
        None,
        help="サーバー名（省略時は全サーバー）",
    ),
) -> None:
    """
    MCP Server情報を表示
    """
    from src.host.config import get_default_config
    
    config = get_default_config()
    
    if server_name:
        if server_name not in config.servers:
            console.print(f"[red]エラー: サーバーが見つかりません: {server_name}[/red]")
            raise typer.Exit(1)
        
        server = config.servers[server_name]
        console.print(Panel(
            f"[cyan]名前:[/cyan] {server.name}\n"
            f"[cyan]コマンド:[/cyan] {server.command}\n"
            f"[cyan]引数:[/cyan] {' '.join(server.args)}\n"
            f"[cyan]ポート:[/cyan] {server.port or 'N/A'}\n"
            f"[cyan]トランスポート:[/cyan] {server.transport}\n"
            f"[cyan]有効:[/cyan] {'はい' if server.enabled else 'いいえ'}",
            title=f"MCP Server: {server_name}",
        ))
        return
    
    # 全サーバー一覧
    table = Table(title="MCP Servers")
    table.add_column("名前", style="cyan")
    table.add_column("コマンド")
    table.add_column("ポート")
    table.add_column("状態")
    
    for name, server in config.servers.items():
        status = "[green]有効[/green]" if server.enabled else "[dim]無効[/dim]"
        table.add_row(
            name,
            f"{server.command} {' '.join(server.args[:2])}...",
            str(server.port) if server.port else "-",
            status,
        )
    
    console.print(table)


# ==============================================
# Evaluation Commands
# ==============================================

@app.command("evaluate")
def run_evaluation(
    dataset: str = typer.Option(
        "basic_design",
        "--dataset", "-d",
        help="データセット (basic_design / test_plan / all)",
    ),
    repeat: int = typer.Option(
        1,
        "--repeat", "-r",
        help="繰り返し回数（再現性検証）",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="結果出力ファイル",
    ),
    format: str = typer.Option(
        "table",
        "--format", "-f",
        help="出力形式 (table / json)",
    ),
) -> None:
    """
    評価を実行
    """
    from src.evaluation import (
        EvaluationRunner,
        EvaluationConfig,
        create_basic_design_dataset,
        create_test_plan_dataset,
        get_all_sample_datasets,
    )
    
    runner = EvaluationRunner(use_llm=False)
    
    # データセット登録
    if dataset == "all":
        for ds in get_all_sample_datasets():
            runner.register_dataset(ds)
        datasets_to_run = [ds.id for ds in get_all_sample_datasets()]
    elif dataset == "basic_design":
        ds = create_basic_design_dataset()
        runner.register_dataset(ds)
        datasets_to_run = [ds.id]
    elif dataset == "test_plan":
        ds = create_test_plan_dataset()
        runner.register_dataset(ds)
        datasets_to_run = [ds.id]
    else:
        console.print(f"[red]エラー: 無効なデータセット: {dataset}[/red]")
        raise typer.Exit(1)
    
    all_results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for ds_id in datasets_to_run:
            task = progress.add_task(f"評価実行中: {ds_id}...", total=None)
            
            config = EvaluationConfig(
                name=f"CLI Evaluation - {ds_id}",
                dataset_id=ds_id,
                repeat_count=repeat,
            )
            
            result = asyncio.run(runner.run_evaluation(config))
            all_results.append(result)
            
            progress.update(task, completed=True)
    
    # 結果出力
    if format == "json":
        output_data = [r.model_dump() for r in all_results]
        output_content = json.dumps(output_data, ensure_ascii=False, indent=2)
        
        if output:
            output.write_text(output_content, encoding="utf-8")
            console.print(f"[green]結果を保存しました: {output}[/green]")
        else:
            print(output_content)
    else:
        # テーブル表示
        for result in all_results:
            _display_evaluation_result(result)
    
    # 終了コード
    for result in all_results:
        if result.summary.accuracy < 0.7:
            raise typer.Exit(1)


def _display_evaluation_result(result) -> None:
    """評価結果を表示"""
    console.print(Panel(
        f"[cyan]評価ID:[/cyan] {result.evaluation_id}\n"
        f"[cyan]ステータス:[/cyan] {result.status.value}\n"
        f"[cyan]データセット:[/cyan] {result.config.dataset_id}",
        title="評価結果",
    ))
    
    # サマリーテーブル
    summary = result.summary
    table = Table(title="評価サマリー")
    table.add_column("メトリクス", style="cyan")
    table.add_column("値", style="green")
    
    table.add_row("総文書数", str(summary.total_documents))
    table.add_row("総チェック数", str(summary.total_checks))
    table.add_row("正解数", str(summary.correct_checks))
    table.add_row("Accuracy", f"{summary.accuracy:.2%}")
    table.add_row("Precision", f"{summary.precision:.2%}")
    table.add_row("Recall", f"{summary.recall:.2%}")
    table.add_row("F1 Score", f"{summary.f1_score:.2%}")
    table.add_row("処理時間", f"{summary.total_processing_time_ms}ms")
    
    if result.config.repeat_count > 1:
        table.add_row("一貫性", f"{summary.consistency_rate:.2%}")
    
    console.print(table)
    
    # 詳細結果
    if result.document_results:
        detail_table = Table(title="文書別結果")
        detail_table.add_column("文書ID")
        detail_table.add_column("文書名")
        detail_table.add_column("チェック数")
        detail_table.add_column("正解数")
        detail_table.add_column("Accuracy")
        
        for doc_result in result.document_results:
            accuracy_color = "green" if doc_result.accuracy >= 0.8 else "yellow" if doc_result.accuracy >= 0.6 else "red"
            detail_table.add_row(
                doc_result.document_id,
                doc_result.document_name,
                str(doc_result.total_checks),
                str(doc_result.correct_checks),
                f"[{accuracy_color}]{doc_result.accuracy:.2%}[/{accuracy_color}]",
            )
        
        console.print(detail_table)


# ==============================================
# Version Command
# ==============================================

@app.command("version")
def show_version() -> None:
    """
    バージョン情報を表示
    """
    console.print(Panel(
        "[cyan]SmartReviewer[/cyan] v2.0.0\n"
        "文書レビュー支援AIエージェント\n\n"
        "[dim]MCP Protocol v1.0対応[/dim]",
        title="SmartReviewer",
    ))


# ==============================================
# Entry Point
# ==============================================

def cli() -> None:
    """CLIエントリーポイント"""
    app()


if __name__ == "__main__":
    cli()
