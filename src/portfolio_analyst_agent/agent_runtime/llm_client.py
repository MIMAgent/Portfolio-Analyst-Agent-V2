"""LLM client interfaces for the agent runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LLMResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    usage: dict[str, Any]
    raw: Any = None


class LLMClient(Protocol):
    def send(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send one Messages API turn and return normalized content blocks."""


class ScriptedLLMClient:
    """Deterministic test double that returns scripted response blocks."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def send(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        self.requests.append({"system": system, "messages": messages, "tools": tools})
        if not self._responses:
            raise RuntimeError("ScriptedLLMClient has no responses left.")
        return self._responses.pop(0)


class AnthropicMessagesClient:
    """Thin Anthropic Messages API wrapper.

    Anthropic tool use returns `tool_use` content blocks and expects a follow-up
    user message containing `tool_result` blocks for each requested tool.
    """

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 4096,
        api_key: str | None = None,
    ):
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the agent extra first: python -m pip install -e \".[agent]\"") from exc

        _load_dotenv()
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def send(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
            tools=tools,
        )
        content = [_normalize_block(block) for block in response.content]
        usage = response.usage.model_dump() if hasattr(response.usage, "model_dump") else dict(response.usage)
        return LLMResponse(
            content=content,
            stop_reason=response.stop_reason or "",
            usage=usage,
            raw=response,
        )


class BedrockClaudeClient:
    """AWS Bedrock Converse API wrapper for Claude tool use."""

    def __init__(
        self,
        *,
        model: str = "anthropic.claude-sonnet-4-6",
        region_name: str = "us-east-1",
        max_tokens: int = 4096,
        profile_name: str | None = None,
        read_timeout: int = 180,
        connect_timeout: int = 10,
    ):
        _load_dotenv()
        self.model = model
        self.region_name = region_name
        self.max_tokens = max_tokens
        self._bearer_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
        self._client = None
        if not self._bearer_token:
            try:
                import boto3  # type: ignore
            except ImportError as exc:
                raise RuntimeError("Install the Bedrock extra first: python -m pip install -e \".[bedrock]\"") from exc
            from botocore.config import Config  # type: ignore

            session = boto3.Session(profile_name=profile_name, region_name=region_name) if profile_name else boto3.Session(region_name=region_name)
            self._client = session.client(
                "bedrock-runtime",
                config=Config(
                    connect_timeout=connect_timeout,
                    read_timeout=read_timeout,
                    retries={"max_attempts": 2, "mode": "standard"},
                ),
            )

    def send(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        payload = _bedrock_converse_payload(
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=self.max_tokens,
        )
        if self._bearer_token:
            response = _send_bedrock_bearer_request(
                model=self.model,
                region_name=self.region_name,
                bearer_token=self._bearer_token,
                payload=payload,
            )
        else:
            response = self._client.converse(modelId=self.model, **payload)
        output_message = response.get("output", {}).get("message", {})
        content = [_from_bedrock_block(block) for block in output_message.get("content", [])]
        return LLMResponse(
            content=content,
            stop_reason=response.get("stopReason", ""),
            usage=response.get("usage", {}),
            raw=response,
        )


def _normalize_block(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    if hasattr(block, "model_dump"):
        return block.model_dump()
    data = {"type": getattr(block, "type", "")}
    for key in ("id", "name", "input", "text"):
        if hasattr(block, key):
            data[key] = getattr(block, key)
    return data


def _to_bedrock_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "toolSpec": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "inputSchema": {"json": tool.get("input_schema", {"type": "object"})},
        }
    }


def _bedrock_converse_payload(
    *,
    system: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    max_tokens: int,
) -> dict[str, Any]:
    return {
        "system": [{"text": system}],
        "messages": [_to_bedrock_message(message) for message in messages],
        "inferenceConfig": {"maxTokens": max_tokens},
        "toolConfig": {"tools": [_to_bedrock_tool(tool) for tool in tools]},
    }


def _send_bedrock_bearer_request(
    *,
    model: str,
    region_name: str,
    bearer_token: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    import json

    url = f"https://bedrock-runtime.{region_name}.amazonaws.com/model/{quote(model, safe='')}/converse"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        },
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _to_bedrock_message(message: dict[str, Any]) -> dict[str, Any]:
    role = message["role"]
    content = message.get("content", "")
    if isinstance(content, str):
        return {"role": role, "content": [{"text": content}]}

    converted = []
    for block in content:
        block_type = block.get("type")
        if block_type == "text":
            converted.append({"text": block.get("text", "")})
        elif block_type == "tool_use":
            converted.append(
                {
                    "toolUse": {
                        "toolUseId": block.get("id", ""),
                        "name": block.get("name", ""),
                        "input": block.get("input", {}),
                    }
                }
            )
        elif block_type == "tool_result":
            result_content = block.get("content", "")
            converted.append(
                {
                    "toolResult": {
                        "toolUseId": block.get("tool_use_id", ""),
                        "content": [{"json": _json_or_text(result_content)}],
                        "status": "error" if block.get("is_error") else "success",
                    }
                }
            )
    return {"role": role, "content": converted}


def _from_bedrock_block(block: dict[str, Any]) -> dict[str, Any]:
    if "text" in block:
        return {"type": "text", "text": block["text"]}
    if "toolUse" in block:
        tool_use = block["toolUse"]
        return {
            "type": "tool_use",
            "id": tool_use.get("toolUseId", ""),
            "name": tool_use.get("name", ""),
            "input": tool_use.get("input", {}),
        }
    return {"type": "unknown", "raw": block}


def _json_or_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    import json

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"text": value}


def _load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


__all__ = ["AnthropicMessagesClient", "BedrockClaudeClient", "LLMClient", "LLMResponse", "ScriptedLLMClient"]
