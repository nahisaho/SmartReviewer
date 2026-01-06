"""
Document Parser Module
======================

文書構造解析・セクション抽出機能
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SectionLevel(int, Enum):
    """セクションレベル"""
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


@dataclass
class Section:
    """文書セクション"""
    id: str
    level: int
    number: str
    title: str
    content: str
    start_line: int
    end_line: int
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    
    @property
    def full_title(self) -> str:
        """番号付きフルタイトル"""
        if self.number:
            return f"{self.number} {self.title}"
        return self.title


@dataclass
class DocumentStructure:
    """文書構造"""
    title: str
    sections: list[Section]
    total_lines: int
    section_tree: dict[str, list[str]]  # parent_id -> [child_ids]
    
    def get_section(self, section_id: str) -> Optional[Section]:
        """セクションをIDで取得"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_sections_by_level(self, level: int) -> list[Section]:
        """レベルでセクションを取得"""
        return [s for s in self.sections if s.level == level]
    
    def get_toc(self) -> list[dict]:
        """目次を生成"""
        return [
            {
                "id": s.id,
                "level": s.level,
                "number": s.number,
                "title": s.title,
            }
            for s in self.sections
        ]


class DocumentParser:
    """文書パーサー"""
    
    # Markdown見出しパターン
    MD_HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    # 番号付き見出しパターン（日本語文書用）
    NUMBERED_HEADING_PATTERNS = [
        re.compile(r'^第(\d+)章\s+(.+)$'),  # 第1章 タイトル
        re.compile(r'^第(\d+)節\s+(.+)$'),  # 第1節 タイトル
        re.compile(r'^(\d+)\.\s+(.+)$'),    # 1. タイトル
        re.compile(r'^(\d+\.\d+)\s+(.+)$'), # 1.1 タイトル
        re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)$'),  # 1.1.1 タイトル
    ]
    
    def __init__(self):
        self.section_counter = 0
    
    def parse(self, content: str) -> DocumentStructure:
        """
        文書を解析して構造を抽出
        
        Args:
            content: 文書内容（Markdown形式）
            
        Returns:
            DocumentStructure
        """
        self.section_counter = 0
        lines = content.split('\n')
        total_lines = len(lines)
        
        # タイトル抽出
        title = self._extract_title(content)
        
        # セクション抽出
        sections = self._extract_sections(content, lines)
        
        # セクションツリー構築
        section_tree = self._build_section_tree(sections)
        
        return DocumentStructure(
            title=title,
            sections=sections,
            total_lines=total_lines,
            section_tree=section_tree,
        )
    
    def _extract_title(self, content: str) -> str:
        """文書タイトルを抽出"""
        lines = content.strip().split('\n')
        
        for line in lines[:20]:
            line = line.strip()
            
            # Markdown H1
            if line.startswith('# '):
                return line[2:].strip()
            
            # 空でない最初の行
            if line and not line.startswith('#'):
                # 短い行ならタイトル候補
                if len(line) < 100:
                    return line
        
        return "Untitled"
    
    def _extract_sections(self, content: str, lines: list[str]) -> list[Section]:
        """セクションを抽出"""
        sections = []
        current_section_start = 0
        pending_section = None
        
        for i, line in enumerate(lines):
            heading = self._parse_heading(line)
            
            if heading:
                # 前のセクションを確定
                if pending_section:
                    pending_section.end_line = i - 1
                    pending_section.content = '\n'.join(
                        lines[pending_section.start_line:i]
                    )
                    sections.append(pending_section)
                
                # 新しいセクション開始
                self.section_counter += 1
                pending_section = Section(
                    id=f"sec-{self.section_counter:03d}",
                    level=heading['level'],
                    number=heading['number'],
                    title=heading['title'],
                    content="",
                    start_line=i,
                    end_line=len(lines) - 1,
                )
        
        # 最後のセクションを確定
        if pending_section:
            pending_section.end_line = len(lines) - 1
            pending_section.content = '\n'.join(
                lines[pending_section.start_line:]
            )
            sections.append(pending_section)
        
        return sections
    
    def _parse_heading(self, line: str) -> Optional[dict]:
        """見出し行をパース"""
        line = line.strip()
        
        # Markdown見出し
        md_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if md_match:
            level = len(md_match.group(1))
            title = md_match.group(2).strip()
            
            # 番号抽出
            number = ""
            num_match = re.match(r'^([\d\.]+)\s*(.+)$', title)
            if num_match:
                number = num_match.group(1)
                title = num_match.group(2)
            
            return {
                'level': level,
                'number': number,
                'title': title,
            }
        
        # 日本語番号付き見出し
        for pattern in self.NUMBERED_HEADING_PATTERNS:
            match = pattern.match(line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                
                # レベル推定
                if '章' in line:
                    level = 1
                elif '節' in line:
                    level = 2
                else:
                    level = number.count('.') + 1
                
                return {
                    'level': level,
                    'number': number,
                    'title': title,
                }
        
        return None
    
    def _build_section_tree(self, sections: list[Section]) -> dict[str, list[str]]:
        """セクションの親子関係を構築"""
        tree: dict[str, list[str]] = {"root": []}
        parent_stack: list[tuple[int, str]] = []  # (level, section_id)
        
        for section in sections:
            # 親を探す
            while parent_stack and parent_stack[-1][0] >= section.level:
                parent_stack.pop()
            
            if parent_stack:
                parent_id = parent_stack[-1][1]
                section.parent_id = parent_id
                
                if parent_id not in tree:
                    tree[parent_id] = []
                tree[parent_id].append(section.id)
            else:
                tree["root"].append(section.id)
            
            parent_stack.append((section.level, section.id))
        
        return tree


def parse_document(content: str) -> DocumentStructure:
    """文書をパースする（ショートカット関数）"""
    parser = DocumentParser()
    return parser.parse(content)


# 必須セクション定義
REQUIRED_SECTIONS_BASIC_DESIGN = [
    {"pattern": r"概要|システム概要|はじめに", "name": "概要"},
    {"pattern": r"システム構成|アーキテクチャ|構成", "name": "システム構成"},
    {"pattern": r"機能設計|機能一覧|機能", "name": "機能設計"},
    {"pattern": r"データ設計|データモデル|データベース", "name": "データ設計"},
    {"pattern": r"インターフェース|外部連携|API", "name": "インターフェース設計"},
    {"pattern": r"非機能|性能|セキュリティ|可用性", "name": "非機能設計"},
]

REQUIRED_SECTIONS_TEST_PLAN = [
    {"pattern": r"テスト方針|方針|目的", "name": "テスト方針"},
    {"pattern": r"スコープ|範囲|対象", "name": "テストスコープ"},
    {"pattern": r"テストレベル|レベル定義", "name": "テストレベル定義"},
    {"pattern": r"スケジュール|日程|計画", "name": "テストスケジュール"},
    {"pattern": r"体制|組織|役割", "name": "テスト体制"},
    {"pattern": r"環境|テスト環境", "name": "テスト環境"},
    {"pattern": r"管理|障害管理|進捗", "name": "テスト管理"},
]


def check_required_sections(
    structure: DocumentStructure,
    document_type: str,
) -> dict:
    """
    必須セクションの存在確認
    
    Args:
        structure: 文書構造
        document_type: 文書タイプ
        
    Returns:
        チェック結果
    """
    if document_type == "basic_design":
        required = REQUIRED_SECTIONS_BASIC_DESIGN
    elif document_type == "test_plan":
        required = REQUIRED_SECTIONS_TEST_PLAN
    else:
        return {"error": f"Unknown document type: {document_type}"}
    
    results = []
    found_count = 0
    
    for req in required:
        pattern = re.compile(req["pattern"], re.IGNORECASE)
        found = False
        found_section = None
        
        for section in structure.sections:
            if pattern.search(section.title):
                found = True
                found_section = section
                break
        
        results.append({
            "required_section": req["name"],
            "found": found,
            "matched_section": found_section.full_title if found_section else None,
        })
        
        if found:
            found_count += 1
    
    return {
        "document_type": document_type,
        "total_required": len(required),
        "found": found_count,
        "missing": len(required) - found_count,
        "coverage": found_count / len(required),
        "details": results,
    }
