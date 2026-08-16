"""
Image utilities for Aztec Multimodal Vision Support.
Handles base64 data URI encoding, format validation, and multimodal message formatting.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from typing import Any, Dict, List, Optional, Union

SUPPORTED_IMAGE_EXTS = frozenset([
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".bmp",
])

MAX_IMAGE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


def is_image_path(path_or_url: str) -> bool:
    """Check if string points to a recognized image file, URL, or data URI."""
    clean = path_or_url.strip()
    if clean.startswith(("data:image/", "http://", "https://")):
        return True
    _, ext = os.path.splitext(clean.lower())
    return ext in SUPPORTED_IMAGE_EXTS


def encode_image_to_data_uri(path_or_url: str) -> str:
    """
    Convert a local image file or URL into a standard base64 data URI:
    'data:image/png;base64,...'
    Passes through existing data URIs and web URLs directly.
    """
    clean = path_or_url.strip()
    if clean.startswith(("data:image/", "http://", "https://")):
        return clean

    if not os.path.exists(clean):
        raise FileNotFoundError(f"Image file not found: {clean}")

    size = os.path.getsize(clean)
    if size > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(f"Image {clean} exceeds 15MB limit ({size / (1024 * 1024):.1f}MB)")

    mime_type, _ = mimetypes.guess_type(clean)
    if not mime_type or not mime_type.startswith("image/"):
        ext = os.path.splitext(clean.lower())[1]
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/png")

    with open(clean, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def parse_images_input(image_inputs: Optional[List[str]]) -> List[str]:
    """Validate and convert a list of image paths/URLs to data URIs or URLs."""
    if not image_inputs:
        return []
    result = []
    for img in image_inputs:
        if isinstance(img, str) and img.strip():
            result.append(encode_image_to_data_uri(img.strip()))
    return result


def format_multimodal_content(text_prompt: str, images: Optional[List[str]] = None) -> Union[str, List[Dict[str, Any]]]:
    """
    Structure user message content for LiteLLM / OpenAI / Anthropic / Gemini multimodal APIs.
    If no images, returns plain text string.
    If images present, returns standard list of text and image_url parts.
    """
    if not images:
        return text_prompt

    parts: List[Dict[str, Any]] = [
        {"type": "text", "text": text_prompt}
    ]

    for img in images:
        data_uri = encode_image_to_data_uri(img)
        parts.append({
            "type": "image_url",
            "image_url": {
                "url": data_uri
            }
        })

    return parts
