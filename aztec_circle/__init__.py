"""
Aztec Decision Circle: Production Multi-Generational LLM Debate Framework.
"""

# Apply LiteLLM / Pydantic >= 2.13 forward ref patch at package root
try:
    import litellm.types.utils as _litellm_utils
    from pydantic import BaseModel as _BaseModel

    if not hasattr(_litellm_utils, "ChatCompletionReasoningSummaryTextBlock"):
        class ChatCompletionReasoningSummaryTextBlock(_BaseModel):
            text: str = ""
        _litellm_utils.ChatCompletionReasoningSummaryTextBlock = ChatCompletionReasoningSummaryTextBlock
        _litellm_utils.Message.model_rebuild()
except Exception:
    pass

# Silence asyncio SSL transport closing race condition on Python 3.10+ shutdown
try:
    import asyncio.sslproto
    _orig_fatal_error = asyncio.sslproto.SSLProtocol._fatal_error

    def _safe_ssl_fatal_error(self, exc, message="Fatal error on transport"):
        if isinstance(exc, (OSError, RuntimeError)) or getattr(self, "_closed", False):
            return
        try:
            _orig_fatal_error(self, exc, message)
        except Exception:
            pass

    asyncio.sslproto.SSLProtocol._fatal_error = _safe_ssl_fatal_error
except Exception:
    pass

__version__ = "0.2.0"

