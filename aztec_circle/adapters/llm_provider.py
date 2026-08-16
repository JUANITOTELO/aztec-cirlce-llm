"""
LLM provider resilience layer using LiteLLM, exponential backoff, and failover.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import litellm
import litellm.types.utils as _litellm_utils
from pydantic import BaseModel as _BaseModel

# LiteLLM compatibility with Pydantic >= 2.13
if not hasattr(_litellm_utils, "ChatCompletionReasoningSummaryTextBlock"):
    class ChatCompletionReasoningSummaryTextBlock(_BaseModel):
        text: str = ""
    _litellm_utils.ChatCompletionReasoningSummaryTextBlock = ChatCompletionReasoningSummaryTextBlock
    try:
        _litellm_utils.Message.model_rebuild()
    except Exception:
        pass

import logging
import structlog

# Suppress verbose LiteLLM debug output and deprecation warnings
litellm.suppress_debug_info = True
litellm.drop_params = True
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aztec_circle.config import settings
from aztec_circle.domain.exceptions import LLMProviderFailure

log = structlog.get_logger(__name__)

# Errors that warrant retry
RETRYABLE_EXCEPTIONS = (
    litellm.RateLimitError,
    litellm.APIConnectionError,
    litellm.Timeout,
    litellm.ServiceUnavailableError,
    asyncio.TimeoutError,
)


class LLMResponse:
    def __init__(
        self,
        content: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cached_tokens: int = 0,
        model: str = "",
        raw: Any = None,
    ):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens or (prompt_tokens + completion_tokens)
        self.cached_tokens = cached_tokens
        self.model = model
        self.raw = raw


class LLMProvider:
    def __init__(
        self,
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        chunk_timeout_seconds: Optional[float] = None,
        streaming: Optional[bool] = None,
    ):
        self.primary_model = primary_model or settings.PEER_MODEL
        self.fallback_model = fallback_model if fallback_model is not None else settings.FALLBACK_MODEL
        self.timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.chunk_timeout_seconds = chunk_timeout_seconds or settings.LLM_CHUNK_TIMEOUT_SECONDS
        self.streaming = streaming if streaming is not None else settings.LLM_STREAMING

    @classmethod
    def supports_prompt_caching(cls, model_id: str) -> bool:
        """Check if target model supports prompt caching."""
        m_lower = model_id.lower()
        if "claude" in m_lower or "anthropic" in m_lower or "gemini-2.5" in m_lower or "gemini-3" in m_lower:
            return True
        try:
            info = litellm.get_model_info(model_id)
            return bool(info.get("supports_prompt_caching"))
        except Exception:
            return False

    @classmethod
    def optimize_messages_for_prompt_caching(
        cls, messages: List[Dict[str, Any]], target_model: str
    ) -> List[Dict[str, Any]]:
        """
        Inject cache_control blocks into system prompts and context prefixes
        for models that support prompt caching (e.g. Anthropic Claude).
        """
        if not cls.supports_prompt_caching(target_model):
            return messages

        import copy
        optimized = []
        for msg in messages:
            msg_copy = copy.deepcopy(msg)
            role = msg_copy.get("role")
            content = msg_copy.get("content")

            if role == "system":
                if isinstance(content, str):
                    msg_copy["content"] = [
                        {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                    ]
                elif isinstance(content, list):
                    has_cache = any(isinstance(b, dict) and "cache_control" in b for b in content)
                    if not has_cache and len(content) > 0:
                        if isinstance(content[-1], dict) and content[-1].get("type") == "text":
                            content[-1]["cache_control"] = {"type": "ephemeral"}
                        elif isinstance(content[-1], str):
                            content[-1] = {"type": "text", "text": content[-1], "cache_control": {"type": "ephemeral"}}

            elif role == "user" and isinstance(content, list):
                has_cache = any(isinstance(b, dict) and "cache_control" in b for b in content)
                if not has_cache and len(content) >= 2:
                    first_block = content[0]
                    if isinstance(first_block, dict) and first_block.get("type") == "text":
                        if len(first_block.get("text", "")) > 300:
                            first_block["cache_control"] = {"type": "ephemeral"}

            optimized.append(msg_copy)
        return optimized

    async def _stream_response(
        self,
        stream_iter: Any,
        on_chunk: Optional[Callable[[str], None]] = None,
        chunk_timeout: Optional[float] = None,
    ) -> Tuple[str, Optional[Any], Any]:
        """
        Consume an async SSE stream chunk-by-chunk with heartbeat inactivity watchdog.
        Returns (full_content, usage_obj, last_raw_chunk).
        """
        # If stream_iter is not an async iterator or is a mock object representing a unary response
        if not hasattr(stream_iter, "__anext__"):
            return "", None, stream_iter

        # If it's a mock with choices/usage but not a generator (e.g. standard test AsyncMock)
        if hasattr(stream_iter, "choices") and hasattr(stream_iter, "usage"):
            return "", None, stream_iter

        timeout = chunk_timeout or self.chunk_timeout_seconds
        content_chunks: List[str] = []
        last_chunk_obj: Any = None
        usage_obj: Any = None

        while True:
            try:
                chunk = await asyncio.wait_for(stream_iter.__anext__(), timeout=timeout)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError as exc:
                log.error("llm.stream_chunk_timeout", timeout=timeout)
                raise TimeoutError(f"Streaming stalled: No chunk received for {timeout}s") from exc

            last_chunk_obj = chunk

            # Extract usage if delivered in streaming chunk
            if hasattr(chunk, "usage") and chunk.usage:
                usage_obj = chunk.usage
            elif isinstance(chunk, dict) and "usage" in chunk and chunk["usage"]:
                usage_obj = chunk["usage"]

            # Extract text delta
            delta_text = ""
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                delta = getattr(choice, "delta", None)
                if delta:
                    delta_text = getattr(delta, "content", "") or ""
                elif hasattr(choice, "text"):
                    delta_text = choice.text or ""
            elif isinstance(chunk, dict) and "choices" in chunk and chunk["choices"]:
                choice = chunk["choices"][0]
                delta = choice.get("delta", {})
                delta_text = delta.get("content", "") if isinstance(delta, dict) else ""

            if delta_text:
                content_chunks.append(delta_text)
                if on_chunk:
                    try:
                        on_chunk(delta_text)
                    except Exception as cb_err:
                        log.warning("llm.stream_callback_failed", error=str(cb_err))

        full_content = "".join(content_chunks)
        return full_content, usage_obj, last_chunk_obj

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    async def _call_litellm(
        self,
        target_model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float],
        thinking_budget: Optional[int],
        stream: bool = True,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> Any:
        # Enable automatic dropping of unsupported params across providers
        litellm.drop_params = True

        extra_kwargs: Dict[str, Any] = dict(kwargs)
        if thinking_budget and thinking_budget > 0:
            m_lower = target_model.lower()
            if "-5" in m_lower or "claude-fable" in m_lower or "claude-haiku-4-5" in m_lower:
                extra_kwargs["thinking"] = {"type": "adaptive"}
            else:
                extra_kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

        # Gemini 3+ models and Claude 5 models manage temperature/thinking adaptively
        is_gemini_3_plus = "gemini-3" in target_model.lower()
        if not is_gemini_3_plus and temperature is not None:
            extra_kwargs["temperature"] = temperature

        optimized_messages = self.optimize_messages_for_prompt_caching(messages, target_model)

        if stream:
            extra_kwargs["stream"] = True
            extra_kwargs["stream_options"] = {"include_usage": True}

            raw_stream = await asyncio.wait_for(
                litellm.acompletion(
                    model=target_model,
                    messages=optimized_messages,
                    **extra_kwargs,
                ),
                timeout=self.timeout_seconds,
            )
            # Stream chunks with inactivity heartbeat watchdog
            return await self._stream_response(raw_stream, on_chunk=on_chunk)

        # Unary non-streaming mode
        return await asyncio.wait_for(
            litellm.acompletion(
                model=target_model,
                messages=optimized_messages,
                **extra_kwargs,
            ),
            timeout=self.timeout_seconds,
        )

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
        stream: Optional[bool] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Execute completion with automatic streaming, retries, and fallback failover.
        """
        target = model or self.primary_model
        use_stream = self.streaming if stream is None else stream

        try:
            resp = await self._call_litellm(
                target_model=target,
                messages=messages,
                temperature=temperature,
                thinking_budget=thinking_budget,
                stream=use_stream,
                on_chunk=on_chunk,
                **kwargs,
            )
            return self._parse_response(resp, target)
        except Exception as exc:
            log.warning("llm.primary_attempt_failed", model=target, error=str(exc))
            if self.fallback_model and target != self.fallback_model:
                log.info("llm.attempting_failover", fallback_model=self.fallback_model)
                try:
                    fallback_resp = await self._call_litellm(
                        target_model=self.fallback_model,
                        messages=messages,
                        temperature=temperature,
                        thinking_budget=None,
                        stream=use_stream,
                        on_chunk=on_chunk,
                        **kwargs,
                    )
                    return self._parse_response(fallback_resp, self.fallback_model)
                except Exception as fallback_exc:
                    log.error("llm.fallback_failed", error=str(fallback_exc))
                    raise LLMProviderFailure(
                        f"Both primary '{target}' and fallback '{self.fallback_model}' failed: {fallback_exc}"
                    ) from fallback_exc
            raise LLMProviderFailure(f"LLM request to '{target}' failed: {exc}") from exc

    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        images: Optional[List[str]] = None,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
        stream: Optional[bool] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Convenience method for system + user message invocations with optional vision images and streaming.
        """
        from aztec_circle.adapters.image_utils import format_multimodal_content
        formatted_content = format_multimodal_content(user_message, images=images)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_content},
        ]
        return await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            thinking_budget=thinking_budget,
            stream=stream,
            on_chunk=on_chunk,
            **kwargs,
        )

    def _parse_response(self, raw_resp: Any, model: str) -> LLMResponse:
        content = ""
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cached_tokens = 0

        # Handle streaming response tuple (full_content, usage_obj, last_chunk)
        if isinstance(raw_resp, tuple) and len(raw_resp) == 3:
            stream_content, stream_usage, raw_item = raw_resp
            if stream_content:
                content = stream_content
            if stream_usage:
                prompt_tokens = getattr(stream_usage, "prompt_tokens", 0) or (stream_usage.get("prompt_tokens", 0) if isinstance(stream_usage, dict) else 0)
                completion_tokens = getattr(stream_usage, "completion_tokens", 0) or (stream_usage.get("completion_tokens", 0) if isinstance(stream_usage, dict) else 0)
                total_tokens = getattr(stream_usage, "total_tokens", 0) or (stream_usage.get("total_tokens", 0) if isinstance(stream_usage, dict) else 0)
                cached_tokens = getattr(stream_usage, "cache_read_input_tokens", 0) or (stream_usage.get("cache_read_input_tokens", 0) if isinstance(stream_usage, dict) else 0)
                if not cached_tokens and hasattr(stream_usage, "prompt_tokens_details"):
                    ptd = getattr(stream_usage, "prompt_tokens_details", None)
                    if isinstance(ptd, dict):
                        cached_tokens = ptd.get("cached_tokens", 0) or 0
                    elif hasattr(ptd, "cached_tokens"):
                        cached_tokens = getattr(ptd, "cached_tokens", 0) or 0
            raw_resp = raw_item

        # Handle standard LiteLLM ModelResponse or dict-like
        if hasattr(raw_resp, "choices") and len(raw_resp.choices) > 0:
            choice = raw_resp.choices[0]
            if not content:
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                elif isinstance(choice, dict) and "message" in choice:
                    content = choice["message"].get("content", "")

            if hasattr(raw_resp, "usage") and raw_resp.usage and prompt_tokens == 0 and completion_tokens == 0:
                usage = raw_resp.usage
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
                cached_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
                if not cached_tokens and hasattr(usage, "prompt_tokens_details"):
                    ptd = getattr(usage, "prompt_tokens_details", None)
                    if isinstance(ptd, dict):
                        cached_tokens = ptd.get("cached_tokens", 0) or 0
                    elif hasattr(ptd, "cached_tokens"):
                        cached_tokens = getattr(ptd, "cached_tokens", 0) or 0
        elif isinstance(raw_resp, dict):
            if not content and "choices" in raw_resp and len(raw_resp["choices"]) > 0:
                content = raw_resp["choices"][0].get("message", {}).get("content", "")
            if "usage" in raw_resp and prompt_tokens == 0 and completion_tokens == 0:
                usage = raw_resp["usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                cached_tokens = usage.get("cache_read_input_tokens", 0) or usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)

        # Accurate fallback estimation if tokens are 0
        if completion_tokens == 0 and content:
            completion_tokens = max(1, len(content) // 4)
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cached_tokens=cached_tokens,
            model=model,
            raw=raw_resp,
        )
