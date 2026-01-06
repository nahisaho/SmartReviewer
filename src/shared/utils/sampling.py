"""
SmartReviewer - MCP Sampling Client
Interface for LLM operations via MCP Sampling protocol

MCP Sampling allows Server to request LLM completions from Host.
The actual LLM (源内) runs on Host side - this module provides
the Server-side interface for requesting completions.

Reference: https://modelcontextprotocol.io/docs/concepts/sampling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from ..config import settings


logger = structlog.get_logger(__name__)


# ==============================================
# Model Preferences for MCP Sampling
# ==============================================

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


class MessageRole(str, Enum):
    """Message role for sampling requests."""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class SamplingMessage:
    """Message in sampling conversation."""
    role: MessageRole
    content: str


@dataclass
class SamplingRequest:
    """Request for MCP Sampling.
    
    Attributes:
        messages: Conversation messages
        model_hint: Hint for which model to use (Host decides actual model)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        stop_sequences: Sequences that stop generation
        system_prompt: System prompt for the conversation
        metadata: Additional metadata for the request
    """
    messages: list[SamplingMessage]
    model_hint: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.1
    stop_sequences: list[str] = field(default_factory=list)
    system_prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP Sampling request format."""
        request = {
            "messages": [
                {"role": msg.role.value, "content": {"type": "text", "text": msg.content}}
                for msg in self.messages
            ],
            "maxTokens": self.max_tokens,
        }
        
        if self.model_hint:
            request["modelPreferences"] = {
                "hints": [{"name": self.model_hint}]
            }
        
        if self.system_prompt:
            request["systemPrompt"] = self.system_prompt
        
        if self.stop_sequences:
            request["stopSequences"] = self.stop_sequences
        
        if self.metadata:
            request["metadata"] = self.metadata
        
        # Include sampling params if non-default temperature
        if self.temperature != 0.1:
            request["samplingParams"] = {"temperature": self.temperature}
        
        return request


@dataclass
class SamplingResponse:
    """Response from MCP Sampling.
    
    Attributes:
        content: Generated text content
        model: Actual model used by Host
        stop_reason: Reason for stopping generation
        usage: Token usage information
    """
    content: str
    model: str | None = None
    stop_reason: str | None = None
    usage: dict[str, int] | None = None
    
    @classmethod
    def from_mcp_format(cls, data: dict[str, Any]) -> "SamplingResponse":
        """Create from MCP Sampling response format."""
        content = ""
        if "content" in data:
            content_data = data["content"]
            if isinstance(content_data, dict) and content_data.get("type") == "text":
                content = content_data.get("text", "")
            elif isinstance(content_data, str):
                content = content_data
        
        return cls(
            content=content,
            model=data.get("model"),
            stop_reason=data.get("stopReason"),
            usage=data.get("usage"),
        )


class SamplingClient:
    """Client for MCP Sampling operations.
    
    This client provides a convenient interface for requesting
    LLM completions via MCP Sampling protocol. The actual LLM
    execution happens on the Host side.
    
    Note: This is used within MCP Server context where the
    server has access to sampling capabilities.
    """
    
    def __init__(self, context: Any = None):
        """Initialize sampling client.
        
        Args:
            context: MCP server context with sampling capability
        """
        self._context = context
        self._default_model = settings.llm.default_model
        self._default_max_tokens = settings.llm.max_tokens
        self._default_temperature = settings.llm.temperature
    
    def create_request(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model_hint: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SamplingRequest:
        """Create a sampling request.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            model_hint: Model preference hint
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            stop_sequences: Stop sequences
            metadata: Additional metadata
            
        Returns:
            SamplingRequest ready to be sent
        """
        return SamplingRequest(
            messages=[SamplingMessage(role=MessageRole.USER, content=prompt)],
            model_hint=model_hint or self._default_model,
            max_tokens=max_tokens or self._default_max_tokens,
            temperature=temperature if temperature is not None else self._default_temperature,
            stop_sequences=stop_sequences or [],
            system_prompt=system_prompt,
            metadata=metadata or {},
        )
    
    def create_chat_request(
        self,
        messages: list[tuple[str, str]],
        *,
        system_prompt: str | None = None,
        **kwargs,
    ) -> SamplingRequest:
        """Create a chat-style sampling request.
        
        Args:
            messages: List of (role, content) tuples
            system_prompt: Optional system prompt
            **kwargs: Additional request parameters
            
        Returns:
            SamplingRequest for chat completion
        """
        sampling_messages = [
            SamplingMessage(
                role=MessageRole(role),
                content=content,
            )
            for role, content in messages
        ]
        
        return SamplingRequest(
            messages=sampling_messages,
            model_hint=kwargs.get("model_hint", self._default_model),
            max_tokens=kwargs.get("max_tokens", self._default_max_tokens),
            temperature=kwargs.get("temperature", self._default_temperature),
            stop_sequences=kwargs.get("stop_sequences", []),
            system_prompt=system_prompt,
            metadata=kwargs.get("metadata", {}),
        )


# Pre-built prompts for SmartReviewer
class ReviewPrompts:
    """Pre-built prompts for document review tasks."""
    
    SYSTEM_REVIEWER = """あなたは政府情報システムの設計書レビューを支援するAIアシスタントです。
デジタル・ガバメント推進標準ガイドラインに基づき、文書の品質をチェックします。

レビューは以下の観点で行います：
1. 文書構成・形式の適切性
2. 内容の完全性・網羅性
3. 記述品質・一貫性
4. ガイドライン準拠

指摘事項は具体的な箇所と改善提案を含めて回答してください。"""
    
    CHECK_TEMPLATE = """以下のチェック項目について、文書をレビューしてください。

## チェック項目
{check_item_name}
{check_item_description}

## 対象文書（抜粋）
{document_content}

## 関連ガイドライン
{guideline_content}

## 回答形式
以下のJSON形式で回答してください：
{{
  "result": "OK" または "NG" または "要確認",
  "confidence": 0.0〜1.0の確信度,
  "evidence": "判断根拠となる文書内の記述",
  "location": "該当箇所（セクション名、ページ番号等）",
  "issues": ["指摘事項1", "指摘事項2", ...],
  "suggestions": ["改善提案1", "改善提案2", ...]
}}"""
    
    COVERAGE_CHECK_TEMPLATE = """以下の必須項目について、文書の網羅性をチェックしてください。

## 必須項目リスト
{required_items}

## 対象文書
{document_content}

## 回答形式
以下のJSON形式で回答してください：
{{
  "coverage_rate": 0.0〜1.0の網羅率,
  "covered_items": [
    {{"item": "項目名", "location": "記載箇所", "quality": "十分/不十分/部分的"}}
  ],
  "missing_items": [
    {{"item": "項目名", "importance": "必須/推奨", "suggestion": "追加すべき内容"}}
  ]
}}"""

    @staticmethod
    def check_judgment_prompt(
        document_content: str,
        check_item_id: str,
        check_item_name: str,
        check_description: str,
        guideline_content: str = "",
    ) -> str:
        """チェック項目判定用プロンプトを生成"""
        return f"""以下のチェック項目について、文書をレビューしてください。

## チェック項目
ID: {check_item_id}
名前: {check_item_name}
説明: {check_description}

## 対象文書
{document_content}

{f"## 関連ガイドライン{chr(10)}{guideline_content}" if guideline_content else ""}

## 回答形式
以下のJSON形式で回答してください：
{{
  "result": "pass" または "fail",
  "confidence": 0.0〜1.0の確信度,
  "reason": "判断理由",
  "evidence": "根拠となる文書内の記述（引用）",
  "suggestions": ["改善提案1", "改善提案2", ...]
}}"""
