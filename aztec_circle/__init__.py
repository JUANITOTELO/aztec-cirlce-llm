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

__version__ = "0.1.0"
