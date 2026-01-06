"""
SmartReviewer Core MCP Server
=============================

FastMCPを使用したMCPサーバー実装
"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from src.shared.config.settings import settings
from src.shared.config.clients import get_minio_client
from src.knowledge.schema import CHECK_ITEMS_DATA
from src.review.engine import ReviewEngine
from src.review.models import ReviewRequest, ReviewOptions


# ==============================================
# Pydantic Models
# ==============================================

class DocumentMetadata(BaseModel):
    """文書メタデータ"""
    id: str = Field(description="文書ID")
    filename: str = Field(description="ファイル名")
    document_type: str = Field(description="文書タイプ (basic_design / test_plan)")
    title: str = Field(default="", description="文書タイトル")
    version: str = Field(default="", description="バージョン")
    uploaded_at: str = Field(description="アップロード日時")
    file_size: int = Field(description="ファイルサイズ (bytes)")
    content_hash: str = Field(description="コンテンツハッシュ")
    status: str = Field(default="uploaded", description="ステータス")


class CheckItem(BaseModel):
    """チェック項目"""
    id: str = Field(description="チェック項目ID")
    name: str = Field(description="チェック項目名")
    description: str = Field(description="説明")
    category: str = Field(description="カテゴリ")
    severity: str = Field(description="重要度")
    document_type: str = Field(description="対象文書タイプ")
    guideline_section: str = Field(default="", description="関連ガイドラインセクション")


class CheckResult(BaseModel):
    """チェック結果"""
    check_item_id: str = Field(description="チェック項目ID")
    result: str = Field(description="結果 (pass / fail / warning / skip)")
    confidence: float = Field(description="確信度 (0.0-1.0)")
    evidence: str = Field(default="", description="根拠")
    location: str = Field(default="", description="該当箇所")
    issues: list[str] = Field(default_factory=list, description="指摘事項")
    suggestions: list[str] = Field(default_factory=list, description="改善提案")


class ReviewResult(BaseModel):
    """レビュー結果"""
    id: str = Field(description="レビュー結果ID")
    document_id: str = Field(description="対象文書ID")
    document_type: str = Field(description="文書タイプ")
    created_at: str = Field(description="作成日時")
    status: str = Field(description="ステータス")
    total_checks: int = Field(description="総チェック数")
    passed: int = Field(description="合格数")
    failed: int = Field(description="不合格数")
    warnings: int = Field(description="警告数")
    skipped: int = Field(description="スキップ数")
    check_results: list[CheckResult] = Field(default_factory=list, description="チェック結果一覧")


# ==============================================
# In-memory Storage (for PoC)
# ==============================================

_documents: dict[str, DocumentMetadata] = {}
_review_results: dict[str, ReviewResult] = {}

# Review Engine instance
_review_engine = ReviewEngine(use_llm=True)


# ==============================================
# FastMCP Server
# ==============================================

app = FastMCP("smartreviewer-core")


# ==============================================
# Tools
# ==============================================

@app.tool()
async def upload_document(
    content: str,
    filename: str,
    document_type: str,
    title: str = "",
    version: str = "",
) -> dict[str, Any]:
    """
    文書をアップロードして解析準備を行う
    
    Args:
        content: 文書内容（テキスト）
        filename: ファイル名
        document_type: 文書タイプ（basic_design / test_plan）
        title: 文書タイトル（省略可）
        version: バージョン（省略可）
        
    Returns:
        アップロード結果（文書ID、メタデータ）
    """
    # バリデーション
    if document_type not in ["basic_design", "test_plan"]:
        raise ValueError(f"Invalid document_type: {document_type}. Must be 'basic_design' or 'test_plan'")
    
    # 文書ID生成
    doc_id = f"doc-{uuid.uuid4().hex[:12]}"
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    # メタデータ作成
    metadata = DocumentMetadata(
        id=doc_id,
        filename=filename,
        document_type=document_type,
        title=title or _extract_title(content),
        version=version,
        uploaded_at=datetime.utcnow().isoformat(),
        file_size=len(content.encode()),
        content_hash=content_hash,
        status="uploaded",
    )
    
    # MinIOに保存（オプション）
    try:
        minio_client = get_minio_client()
        object_name = f"{document_type}/{doc_id}/{filename}"
        
        # コンテンツをバイトに変換
        content_bytes = content.encode("utf-8")
        
        from io import BytesIO
        minio_client.put_object(
            bucket_name="documents",
            object_name=object_name,
            data=BytesIO(content_bytes),
            length=len(content_bytes),
            content_type="text/plain",
        )
        
        # メタデータも保存
        metadata_json = metadata.model_dump_json()
        minio_client.put_object(
            bucket_name="documents",
            object_name=f"{document_type}/{doc_id}/metadata.json",
            data=BytesIO(metadata_json.encode()),
            length=len(metadata_json.encode()),
            content_type="application/json",
        )
    except Exception as e:
        # MinIO接続失敗時はインメモリのみ
        pass
    
    # インメモリに保存
    _documents[doc_id] = metadata
    
    return {
        "success": True,
        "document_id": doc_id,
        "metadata": metadata.model_dump(),
        "message": f"Document uploaded successfully: {filename}",
    }


@app.tool()
async def review_document(
    document_id: str,
    check_item_ids: list[str] | None = None,
    parallel: bool = True,
    include_evidence: bool = True,
    max_findings: int = 100,
) -> dict[str, Any]:
    """
    文書のレビューを実行し、指摘事項を生成する
    
    Args:
        document_id: 対象文書ID
        check_item_ids: チェック項目ID配列（省略時: 全項目）
        parallel: 並列実行フラグ
        include_evidence: 根拠情報を含める
        max_findings: 最大指摘数
    
    Returns:
        レビュー結果（review_id, status, findings, suggestions）
    """
    # 文書の存在確認
    if document_id not in _documents:
        raise ValueError(f"Document not found: {document_id}")
    
    doc_metadata = _documents[document_id]
    
    # 文書内容を取得（MinIOまたはキャッシュから）
    document_content = await _get_document_content(document_id)
    
    # レビューリクエスト作成
    request = ReviewRequest(
        document_id=document_id,
        document_content=document_content,
        document_type=doc_metadata.document_type,
        check_item_ids=check_item_ids,
        options=ReviewOptions(
            parallel=parallel,
            include_evidence=include_evidence,
            max_findings=max_findings,
        ),
    )
    
    # レビュー実行
    result = await _review_engine.review_document(request)
    
    # 結果を保存
    _review_results[result.review_id] = ReviewResult(
        id=result.review_id,
        document_id=document_id,
        document_type=doc_metadata.document_type,
        created_at=result.created_at,
        status=result.status.value,
        total_checks=result.metadata.checks_executed,
        passed=result.metadata.checks_passed,
        failed=result.metadata.checks_failed,
        warnings=result.metadata.checks_warning,
        skipped=result.metadata.checks_skipped,
        check_results=[],  # Simplified storage
    )
    
    # レスポンス構築
    findings = []
    suggestions = []
    for check_result in result.check_results:
        for finding in check_result.findings:
            findings.append(finding.model_dump())
        for suggestion in check_result.suggestions:
            suggestions.append(suggestion.model_dump())
    
    return {
        "success": True,
        "review_id": result.review_id,
        "document_id": document_id,
        "status": result.overall_result.value,
        "total_findings": result.total_findings,
        "critical_findings": result.critical_findings,
        "findings": findings[:max_findings],
        "suggestions": suggestions,
        "execution_time_ms": result.execution_time_ms,
        "metadata": {
            "checks_executed": result.metadata.checks_executed,
            "checks_passed": result.metadata.checks_passed,
            "checks_failed": result.metadata.checks_failed,
            "checks_warning": result.metadata.checks_warning,
            "checks_skipped": result.metadata.checks_skipped,
        },
    }


async def _get_document_content(document_id: str) -> str:
    """文書内容を取得（MinIOまたはキャッシュから）"""
    # TODO: MinIOから取得する実装
    # 現在はダミーコンテンツを返す
    return f"Document content for {document_id}"


@app.tool()
async def get_check_items(
    document_type: str | None = None,
    category: str | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    """
    チェック項目を取得する
    
    Args:
        document_type: 文書タイプでフィルタ（basic_design / test_plan）
        category: カテゴリでフィルタ（structure / completeness / traceability / quality / guideline）
        severity: 重要度でフィルタ（critical / high / medium / low）
        
    Returns:
        チェック項目一覧
    """
    items = CHECK_ITEMS_DATA.copy()
    
    # フィルタリング
    if document_type:
        items = [i for i in items if i["document_type"] == document_type]
    
    if category:
        items = [i for i in items if i["category"] == category]
    
    if severity:
        items = [i for i in items if i["severity"] == severity]
    
    return {
        "total": len(items),
        "filters": {
            "document_type": document_type,
            "category": category,
            "severity": severity,
        },
        "items": items,
    }


@app.tool()
async def create_report(
    document_id: str,
    check_results: list[dict[str, Any]],
    format: str = "json",
) -> dict[str, Any]:
    """
    レビュー結果レポートを生成する
    
    Args:
        document_id: 対象文書ID
        check_results: チェック結果一覧
        format: 出力形式（json / markdown）
        
    Returns:
        レポートデータ
    """
    # 文書メタデータ取得
    if document_id not in _documents:
        raise ValueError(f"Document not found: {document_id}")
    
    doc_metadata = _documents[document_id]
    
    # 結果集計
    results = [CheckResult(**r) for r in check_results]
    passed = sum(1 for r in results if r.result == "pass")
    failed = sum(1 for r in results if r.result == "fail")
    warnings = sum(1 for r in results if r.result == "warning")
    skipped = sum(1 for r in results if r.result == "skip")
    
    # レビュー結果作成
    review_id = f"review-{uuid.uuid4().hex[:12]}"
    review_result = ReviewResult(
        id=review_id,
        document_id=document_id,
        document_type=doc_metadata.document_type,
        created_at=datetime.utcnow().isoformat(),
        status="completed",
        total_checks=len(results),
        passed=passed,
        failed=failed,
        warnings=warnings,
        skipped=skipped,
        check_results=results,
    )
    
    # インメモリに保存
    _review_results[review_id] = review_result
    
    # レポート生成
    if format == "markdown":
        report_content = _generate_markdown_report(review_result, doc_metadata)
    else:
        report_content = review_result.model_dump()
    
    # MinIOに保存（オプション）
    try:
        minio_client = get_minio_client()
        result_json = review_result.model_dump_json()
        
        from io import BytesIO
        minio_client.put_object(
            bucket_name="results",
            object_name=f"{document_id}/{review_id}.json",
            data=BytesIO(result_json.encode()),
            length=len(result_json.encode()),
            content_type="application/json",
        )
    except Exception:
        pass
    
    return {
        "success": True,
        "review_id": review_id,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
            "pass_rate": passed / len(results) if results else 0,
        },
        "report": report_content,
    }


@app.tool()
async def get_document(document_id: str) -> dict[str, Any]:
    """
    文書メタデータを取得する
    
    Args:
        document_id: 文書ID
        
    Returns:
        文書メタデータ
    """
    if document_id not in _documents:
        raise ValueError(f"Document not found: {document_id}")
    
    return _documents[document_id].model_dump()


@app.tool()
async def list_documents(
    document_type: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    文書一覧を取得する
    
    Args:
        document_type: 文書タイプでフィルタ
        limit: 取得件数上限
        
    Returns:
        文書一覧
    """
    docs = list(_documents.values())
    
    if document_type:
        docs = [d for d in docs if d.document_type == document_type]
    
    docs = docs[:limit]
    
    return {
        "total": len(docs),
        "documents": [d.model_dump() for d in docs],
    }


@app.tool()
async def get_review_result(review_id: str) -> dict[str, Any]:
    """
    レビュー結果を取得する
    
    Args:
        review_id: レビュー結果ID
        
    Returns:
        レビュー結果
    """
    if review_id not in _review_results:
        raise ValueError(f"Review result not found: {review_id}")
    
    return _review_results[review_id].model_dump()


# ==============================================
# Resources
# ==============================================

@app.resource("documents://{document_id}")
async def get_document_resource(document_id: str) -> str:
    """文書リソースを取得"""
    if document_id not in _documents:
        raise ValueError(f"Document not found: {document_id}")
    
    return json.dumps(_documents[document_id].model_dump(), ensure_ascii=False, indent=2)


@app.resource("results://{review_id}")
async def get_result_resource(review_id: str) -> str:
    """レビュー結果リソースを取得"""
    if review_id not in _review_results:
        raise ValueError(f"Review result not found: {review_id}")
    
    return json.dumps(_review_results[review_id].model_dump(), ensure_ascii=False, indent=2)


@app.resource("check-items://all")
async def get_all_check_items() -> str:
    """全チェック項目を取得"""
    return json.dumps(CHECK_ITEMS_DATA, ensure_ascii=False, indent=2)


@app.resource("check-items://{document_type}")
async def get_check_items_by_type(document_type: str) -> str:
    """文書タイプ別チェック項目を取得"""
    items = [i for i in CHECK_ITEMS_DATA if i["document_type"] == document_type]
    return json.dumps(items, ensure_ascii=False, indent=2)


# ==============================================
# Helper Functions
# ==============================================

def _extract_title(content: str) -> str:
    """文書内容からタイトルを抽出"""
    lines = content.strip().split("\n")
    for line in lines[:10]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line and not line.startswith("#"):
            return line[:100]
    return "Untitled Document"


def _generate_markdown_report(review: ReviewResult, doc: DocumentMetadata) -> str:
    """Markdownレポートを生成"""
    lines = [
        f"# レビュー結果レポート",
        f"",
        f"## 文書情報",
        f"- 文書ID: {doc.id}",
        f"- ファイル名: {doc.filename}",
        f"- 文書タイプ: {doc.document_type}",
        f"- タイトル: {doc.title}",
        f"- レビュー日時: {review.created_at}",
        f"",
        f"## サマリー",
        f"| 項目 | 件数 |",
        f"|------|------|",
        f"| 総チェック数 | {review.total_checks} |",
        f"| 合格 | {review.passed} |",
        f"| 不合格 | {review.failed} |",
        f"| 警告 | {review.warnings} |",
        f"| スキップ | {review.skipped} |",
        f"| **合格率** | **{review.passed / review.total_checks * 100:.1f}%** |",
        f"",
        f"## チェック結果詳細",
        f"",
    ]
    
    for result in review.check_results:
        status_icon = {
            "pass": "✅",
            "fail": "❌",
            "warning": "⚠️",
            "skip": "⏭️",
        }.get(result.result, "❓")
        
        lines.extend([
            f"### {status_icon} {result.check_item_id}",
            f"- 結果: **{result.result.upper()}**",
            f"- 確信度: {result.confidence:.0%}",
        ])
        
        if result.evidence:
            lines.append(f"- 根拠: {result.evidence}")
        
        if result.location:
            lines.append(f"- 該当箇所: {result.location}")
        
        if result.issues:
            lines.append(f"- 指摘事項:")
            for issue in result.issues:
                lines.append(f"  - {issue}")
        
        if result.suggestions:
            lines.append(f"- 改善提案:")
            for suggestion in result.suggestions:
                lines.append(f"  - {suggestion}")
        
        lines.append("")
    
    return "\n".join(lines)


# ==============================================
# Server Factory
# ==============================================

def create_server() -> FastMCP:
    """MCPサーバーインスタンスを作成"""
    return app


if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream=read_stream,
                write_stream=write_stream,
            )
    
    asyncio.run(main())
