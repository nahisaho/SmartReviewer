"""
Check Executor
==============

チェック項目の実行エンジン
"""

import uuid
import asyncio
import time
from typing import Optional
from dataclasses import dataclass

from src.knowledge.schema import CHECK_ITEMS_DATA
from src.review.models import (
    CheckResult,
    CheckResultStatus,
    Finding,
    Suggestion,
    Severity,
    FindingType,
)


# ==============================================
# Check Logic Registry
# ==============================================

@dataclass
class CheckLogic:
    """チェックロジック定義"""
    check_item_id: str
    name: str
    description: str
    check_func: callable


# チェックロジックのレジストリ
_check_logic_registry: dict[str, CheckLogic] = {}


def register_check_logic(check_item_id: str):
    """チェックロジック登録デコレータ"""
    def decorator(func):
        _check_logic_registry[check_item_id] = CheckLogic(
            check_item_id=check_item_id,
            name=func.__name__,
            description=func.__doc__ or "",
            check_func=func,
        )
        return func
    return decorator


# ==============================================
# Check Executor
# ==============================================

class CheckExecutor:
    """チェック実行エンジン"""
    
    def __init__(
        self,
        use_llm: bool = True,
        llm_client: Optional[object] = None,
    ):
        """
        Args:
            use_llm: LLM推論を使用するか
            llm_client: LLMクライアント（MCP Sampling用）
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
    
    async def execute_check(
        self,
        check_item_id: str,
        document_content: str,
        document_type: str,
        context: Optional[dict] = None,
    ) -> CheckResult:
        """
        単一チェック項目を実行
        
        Args:
            check_item_id: チェック項目ID
            document_content: 文書内容
            document_type: 文書タイプ
            context: 追加コンテキスト（RAG結果等）
        
        Returns:
            CheckResult
        """
        start_time = time.time()
        
        # チェック項目情報取得
        check_item = self._get_check_item(check_item_id)
        if not check_item:
            return CheckResult(
                check_item_id=check_item_id,
                check_item_name="Unknown",
                status=CheckResultStatus.SKIP,
                confidence=0.0,
                error_message=f"Check item not found: {check_item_id}",
            )
        
        # 文書タイプチェック
        if check_item["document_type"] != document_type:
            return CheckResult(
                check_item_id=check_item_id,
                check_item_name=check_item["name"],
                status=CheckResultStatus.SKIP,
                confidence=1.0,
                error_message=f"Check item not applicable to {document_type}",
            )
        
        try:
            # カスタムチェックロジックがあれば実行
            if check_item_id in _check_logic_registry:
                logic = _check_logic_registry[check_item_id]
                result = await logic.check_func(
                    document_content=document_content,
                    check_item=check_item,
                    context=context,
                )
            else:
                # デフォルトチェック（ルールベース + LLM）
                result = await self._default_check(
                    document_content=document_content,
                    check_item=check_item,
                    context=context,
                )
            
            execution_time = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time
            return result
        
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_item_id=check_item_id,
                check_item_name=check_item["name"],
                status=CheckResultStatus.SKIP,
                confidence=0.0,
                execution_time_ms=execution_time,
                error_message=str(e),
            )
    
    async def execute_checks_parallel(
        self,
        check_item_ids: list[str],
        document_content: str,
        document_type: str,
        context: Optional[dict] = None,
        max_concurrency: int = 5,
    ) -> list[CheckResult]:
        """
        複数チェック項目を並列実行
        
        Args:
            check_item_ids: チェック項目IDリスト
            document_content: 文書内容
            document_type: 文書タイプ
            context: 追加コンテキスト
            max_concurrency: 最大並列数
        
        Returns:
            CheckResult リスト
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_with_semaphore(check_id: str) -> CheckResult:
            async with semaphore:
                return await self.execute_check(
                    check_item_id=check_id,
                    document_content=document_content,
                    document_type=document_type,
                    context=context,
                )
        
        tasks = [execute_with_semaphore(cid) for cid in check_item_ids]
        results = await asyncio.gather(*tasks)
        return list(results)
    
    def _get_check_item(self, check_item_id: str) -> Optional[dict]:
        """チェック項目情報を取得"""
        for item in CHECK_ITEMS_DATA:
            if item["id"] == check_item_id:
                return item
        return None
    
    async def _default_check(
        self,
        document_content: str,
        check_item: dict,
        context: Optional[dict] = None,
    ) -> CheckResult:
        """
        デフォルトチェック実行
        ルールベースチェック + LLM判定
        """
        check_item_id = check_item["id"]
        check_item_name = check_item["name"]
        category = check_item["category"]
        severity = Severity(check_item["severity"])
        
        findings = []
        suggestions = []
        status = CheckResultStatus.PASS
        confidence = 0.8  # デフォルト確信度
        
        # カテゴリに応じたルールベースチェック
        if category == "completeness":
            result = self._check_completeness(document_content, check_item)
            if result["issues"]:
                status = CheckResultStatus.FAIL
                findings.extend(result["findings"])
                suggestions.extend(result["suggestions"])
        
        elif category == "consistency":
            result = self._check_consistency(document_content, check_item)
            if result["issues"]:
                status = CheckResultStatus.WARNING
                findings.extend(result["findings"])
                suggestions.extend(result["suggestions"])
        
        elif category == "terminology":
            result = self._check_terminology(document_content, check_item)
            if result["issues"]:
                status = CheckResultStatus.WARNING
                findings.extend(result["findings"])
                suggestions.extend(result["suggestions"])
        
        elif category == "structure":
            result = self._check_structure(document_content, check_item)
            if result["issues"]:
                status = CheckResultStatus.FAIL
                findings.extend(result["findings"])
                suggestions.extend(result["suggestions"])
        
        else:
            # その他のカテゴリはPASSとする
            status = CheckResultStatus.PASS
        
        return CheckResult(
            check_item_id=check_item_id,
            check_item_name=check_item_name,
            status=status,
            confidence=confidence,
            findings=findings,
            suggestions=suggestions,
        )
    
    def _check_completeness(
        self,
        document_content: str,
        check_item: dict,
    ) -> dict:
        """完全性チェック"""
        issues = []
        findings = []
        suggestions = []
        
        # 必須セクションの存在確認
        required_sections = self._get_required_sections(check_item["document_type"])
        content_lower = document_content.lower()
        
        for section in required_sections:
            if section.lower() not in content_lower:
                issues.append(f"Missing section: {section}")
                findings.append(Finding(
                    id=f"f-{uuid.uuid4().hex[:8]}",
                    check_item_id=check_item["id"],
                    type=FindingType.ERROR,
                    severity=Severity(check_item["severity"]),
                    title=f"必須セクション「{section}」が見つかりません",
                    description=f"ガイドラインで必須とされている「{section}」セクションが文書内に見つかりませんでした。",
                    guideline_reference=check_item.get("guideline_section", ""),
                ))
                suggestions.append(Suggestion(
                    id=f"s-{uuid.uuid4().hex[:8]}",
                    finding_id=findings[-1].id,
                    title=f"「{section}」セクションを追加",
                    description=f"文書に「{section}」セクションを追加してください。",
                    priority=1,
                ))
        
        return {"issues": issues, "findings": findings, "suggestions": suggestions}
    
    def _check_consistency(
        self,
        document_content: str,
        check_item: dict,
    ) -> dict:
        """一貫性チェック"""
        issues = []
        findings = []
        suggestions = []
        
        # 用語の一貫性（簡易版）
        # 例: "ユーザ" と "ユーザー" の混在チェック
        inconsistent_terms = [
            ("ユーザ", "ユーザー"),
            ("サーバ", "サーバー"),
            ("データ", "データー"),
        ]
        
        for term1, term2 in inconsistent_terms:
            if term1 in document_content and term2 in document_content:
                issues.append(f"Inconsistent term: {term1} / {term2}")
                findings.append(Finding(
                    id=f"f-{uuid.uuid4().hex[:8]}",
                    check_item_id=check_item["id"],
                    type=FindingType.WARNING,
                    severity=Severity.MEDIUM,
                    title=f"用語の不統一: 「{term1}」と「{term2}」",
                    description=f"文書内で「{term1}」と「{term2}」が混在しています。統一してください。",
                ))
                suggestions.append(Suggestion(
                    id=f"s-{uuid.uuid4().hex[:8]}",
                    finding_id=findings[-1].id,
                    title="用語を統一",
                    description=f"「{term2}」に統一することを推奨します。",
                    priority=2,
                ))
        
        return {"issues": issues, "findings": findings, "suggestions": suggestions}
    
    def _check_terminology(
        self,
        document_content: str,
        check_item: dict,
    ) -> dict:
        """用語チェック"""
        issues = []
        findings = []
        suggestions = []
        
        # 非推奨用語のチェック
        deprecated_terms = {
            "パスワード": "認証情報",
            "ログインID": "ユーザーID",
            "管理者権限": "特権アクセス",
        }
        
        for old_term, new_term in deprecated_terms.items():
            if old_term in document_content:
                issues.append(f"Deprecated term: {old_term}")
                findings.append(Finding(
                    id=f"f-{uuid.uuid4().hex[:8]}",
                    check_item_id=check_item["id"],
                    type=FindingType.INFO,
                    severity=Severity.LOW,
                    title=f"推奨用語: 「{old_term}」→「{new_term}」",
                    description=f"「{old_term}」は「{new_term}」への置き換えを推奨します。",
                ))
                suggestions.append(Suggestion(
                    id=f"s-{uuid.uuid4().hex[:8]}",
                    finding_id=findings[-1].id,
                    title=f"「{new_term}」に置換",
                    description=f"「{old_term}」を「{new_term}」に置き換えてください。",
                    example=f"変更前: {old_term}\n変更後: {new_term}",
                    priority=3,
                ))
        
        return {"issues": issues, "findings": findings, "suggestions": suggestions}
    
    def _check_structure(
        self,
        document_content: str,
        check_item: dict,
    ) -> dict:
        """構造チェック"""
        issues = []
        findings = []
        suggestions = []
        
        # 見出し階層の確認（Markdown形式を想定）
        lines = document_content.split("\n")
        has_h1 = any(line.startswith("# ") for line in lines)
        has_h2 = any(line.startswith("## ") for line in lines)
        
        if not has_h1:
            issues.append("Missing H1 heading")
            findings.append(Finding(
                id=f"f-{uuid.uuid4().hex[:8]}",
                check_item_id=check_item["id"],
                type=FindingType.WARNING,
                severity=Severity.MEDIUM,
                title="文書タイトル（H1見出し）が見つかりません",
                description="文書の先頭に大見出し（#）でタイトルを記載してください。",
            ))
            suggestions.append(Suggestion(
                id=f"s-{uuid.uuid4().hex[:8]}",
                finding_id=findings[-1].id,
                title="H1見出しを追加",
                description="文書の先頭に「# タイトル」形式でタイトルを追加してください。",
                example="# 基本設計書\n\n## 1. はじめに",
                priority=1,
            ))
        
        return {"issues": issues, "findings": findings, "suggestions": suggestions}
    
    def _get_required_sections(self, document_type: str) -> list[str]:
        """文書タイプに応じた必須セクション一覧"""
        if document_type == "basic_design":
            return [
                "システム概要",
                "システム構成",
                "機能設計",
                "データ設計",
                "インターフェース設計",
            ]
        elif document_type == "test_plan":
            return [
                "テスト概要",
                "テスト範囲",
                "テスト環境",
                "テストスケジュール",
            ]
        return []


# ==============================================
# Built-in Check Logic Examples
# ==============================================

@register_check_logic("BD-001")
async def check_bd_001(
    document_content: str,
    check_item: dict,
    context: Optional[dict] = None,
) -> CheckResult:
    """BD-001: 基本設計書必須セクションの網羅性チェック"""
    findings = []
    suggestions = []
    
    # 基本設計書の必須セクション一覧
    required_sections = [
        ("システム概要", ["システム概要", "システムの概要", "概要"]),
        ("システム構成", ["システム構成", "アーキテクチャ", "構成"]),
        ("機能設計", ["機能設計", "機能一覧", "機能要件"]),
        ("データ設計", ["データ設計", "データモデル", "データベース設計"]),
        ("インターフェース設計", ["インターフェース設計", "インターフェイス設計", "IF設計", "API設計"]),
    ]
    
    missing_sections = []
    content_lower = document_content.lower()
    
    for section_name, keywords in required_sections:
        found = any(kw.lower() in content_lower for kw in keywords)
        if not found:
            missing_sections.append(section_name)
    
    if missing_sections:
        for section in missing_sections:
            findings.append(Finding(
                id=f"f-{uuid.uuid4().hex[:8]}",
                check_item_id="BD-001",
                type=FindingType.ERROR,
                severity=Severity.HIGH,
                title=f"必須セクション「{section}」が未記載",
                description=f"基本設計書には「{section}」の記載が必須です。",
                guideline_reference="DG推進標準ガイドライン 第3章",
            ))
            suggestions.append(Suggestion(
                id=f"s-{uuid.uuid4().hex[:8]}",
                finding_id=findings[-1].id,
                title=f"「{section}」セクションを追加",
                description=f"ガイドラインに従い「{section}」セクションを追加してください。",
                priority=1,
            ))
        
        return CheckResult(
            check_item_id="BD-001",
            check_item_name=check_item["name"],
            status=CheckResultStatus.FAIL,
            confidence=0.95,
            findings=findings,
            suggestions=suggestions,
        )
    
    return CheckResult(
        check_item_id="BD-001",
        check_item_name=check_item["name"],
        status=CheckResultStatus.PASS,
        confidence=0.95,
    )


@register_check_logic("TP-001")
async def check_tp_001(
    document_content: str,
    check_item: dict,
    context: Optional[dict] = None,
) -> CheckResult:
    """TP-001: テスト計画書必須セクションの網羅性チェック"""
    findings = []
    suggestions = []
    
    # テスト計画書の必須セクション一覧
    required_sections = [
        ("テスト概要", ["テスト概要", "概要", "目的"]),
        ("テスト範囲", ["テスト範囲", "テスト対象", "テストレベル", "テスト種別"]),
        ("テスト環境", ["テスト環境", "環境構成", "テスト環境構成"]),
        ("テストスケジュール", ["テストスケジュール", "スケジュール", "テスト日程"]),
    ]
    
    missing_sections = []
    content_lower = document_content.lower()
    
    for section_name, keywords in required_sections:
        found = any(kw.lower() in content_lower for kw in keywords)
        if not found:
            missing_sections.append(section_name)
    
    if missing_sections:
        for section in missing_sections:
            findings.append(Finding(
                id=f"f-{uuid.uuid4().hex[:8]}",
                check_item_id="TP-001",
                type=FindingType.ERROR,
                severity=Severity.HIGH,
                title=f"必須セクション「{section}」が未記載",
                description=f"テスト計画書には「{section}」の記載が必須です。",
                guideline_reference="DG推進標準ガイドライン 第5章",
            ))
            suggestions.append(Suggestion(
                id=f"s-{uuid.uuid4().hex[:8]}",
                finding_id=findings[-1].id,
                title=f"「{section}」セクションを追加",
                description=f"ガイドラインに従い「{section}」セクションを追加してください。",
                priority=1,
            ))
        
        return CheckResult(
            check_item_id="TP-001",
            check_item_name=check_item["name"],
            status=CheckResultStatus.FAIL,
            confidence=0.95,
            findings=findings,
            suggestions=suggestions,
        )
    
    return CheckResult(
        check_item_id="TP-001",
        check_item_name=check_item["name"],
        status=CheckResultStatus.PASS,
        confidence=0.95,
    )


@register_check_logic("BD-003")
async def check_bd_003(
    document_content: str,
    check_item: dict,
    context: Optional[dict] = None,
) -> CheckResult:
    """BD-003: システム目的の明記チェック"""
    findings = []
    suggestions = []
    
    # 目的に関するキーワードを検索
    purpose_keywords = ["目的", "背景", "対象範囲", "狙い", "ゴール"]
    content_lower = document_content.lower()
    
    has_purpose = any(kw in document_content for kw in purpose_keywords)
    
    # 目的セクションがあっても内容が薄い場合をチェック
    if has_purpose:
        # 目的の記述が十分かどうかを簡易チェック
        # 「目的」の後に続く文が30文字以上あるか
        import re
        purpose_pattern = r'目的[^\n]*\n([^\n#]*)'
        matches = re.findall(purpose_pattern, document_content)
        
        has_sufficient_description = False
        for match in matches:
            if len(match.strip()) >= 20:
                has_sufficient_description = True
                break
        
        if not has_sufficient_description:
            # システム概要内に詳細な説明があるかもチェック
            if "本システムは" in document_content or "本文書は" in document_content:
                has_sufficient_description = True
    
        if has_sufficient_description:
            return CheckResult(
                check_item_id="BD-003",
                check_item_name=check_item["name"],
                status=CheckResultStatus.PASS,
                confidence=0.9,
            )
    
    # 目的が不明確または未記載
    findings.append(Finding(
        id=f"f-{uuid.uuid4().hex[:8]}",
        check_item_id="BD-003",
        type=FindingType.ERROR,
        severity=Severity.HIGH,
        title="システム目的が不明確",
        description="基本設計書にはシステムの目的・背景を明記してください。",
        guideline_reference="DG推進標準ガイドライン 第3章",
    ))
    suggestions.append(Suggestion(
        id=f"s-{uuid.uuid4().hex[:8]}",
        finding_id=findings[-1].id,
        title="目的セクションを充実化",
        description="システム開発の目的、背景、期待される効果を記載してください。",
        priority=1,
    ))
    
    return CheckResult(
        check_item_id="BD-003",
        check_item_name=check_item["name"],
        status=CheckResultStatus.FAIL,
        confidence=0.85,
        findings=findings,
        suggestions=suggestions,
    )


@register_check_logic("BD-004")
async def check_bd_004(
    document_content: str,
    check_item: dict,
    context: Optional[dict] = None,
) -> CheckResult:
    """BD-004: システム構成図の存在チェック"""
    findings = []
    suggestions = []
    
    # 構成図に関するキーワードを検索
    diagram_indicators = [
        "```",  # コードブロック（図の可能性）
        "mermaid",  # Mermaidダイアグラム
        "┌", "└", "│", "─",  # ASCII図
        "構成図", "アーキテクチャ図", "システム構成図",
        "[図", "図1", "図2",  # 図の参照
    ]
    
    has_diagram = any(indicator in document_content for indicator in diagram_indicators)
    
    if has_diagram:
        return CheckResult(
            check_item_id="BD-004",
            check_item_name=check_item["name"],
            status=CheckResultStatus.PASS,
            confidence=0.9,
        )
    
    findings.append(Finding(
        id=f"f-{uuid.uuid4().hex[:8]}",
        check_item_id="BD-004",
        type=FindingType.ERROR,
        severity=Severity.MEDIUM,
        title="システム構成図が見つかりません",
        description="基本設計書にはシステム構成を示す図を含めてください。",
        guideline_reference="DG推進標準ガイドライン 第3章",
    ))
    suggestions.append(Suggestion(
        id=f"s-{uuid.uuid4().hex[:8]}",
        finding_id=findings[-1].id,
        title="システム構成図を追加",
        description="システムの全体構成を視覚的に示す図を追加してください。",
        example="Mermaid記法やASCII図で記述可能です。",
        priority=1,
    ))
    
    return CheckResult(
        check_item_id="BD-004",
        check_item_name=check_item["name"],
        status=CheckResultStatus.FAIL,
        confidence=0.9,
        findings=findings,
        suggestions=suggestions,
    )
