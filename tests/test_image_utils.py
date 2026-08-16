"""
Unit tests for Aztec image encoding and multimodal formatting utilities.
"""

import base64
import pytest
from aztec_circle.adapters.image_utils import (
    encode_image_to_data_uri,
    format_multimodal_content,
    is_image_path,
    parse_images_input,
)


def test_is_image_path():
    assert is_image_path("mockup.png") is True
    assert is_image_path("/path/to/diagram.jpg") is True
    assert is_image_path("https://example.com/spec.webp") is True
    assert is_image_path("data:image/png;base64,AAAA") is True
    assert is_image_path("main.tsx") is False
    assert is_image_path("package.json") is False


def test_encode_local_image_png(tmp_path):
    img_file = tmp_path / "mockup.png"
    # Write a tiny 1x1 dummy PNG payload
    dummy_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    img_file.write_bytes(dummy_bytes)

    data_uri = encode_image_to_data_uri(str(img_file))
    assert data_uri.startswith("data:image/png;base64,")
    b64_part = data_uri.split("base64,")[1]
    decoded = base64.b64decode(b64_part)
    assert decoded == dummy_bytes


def test_encode_image_preserves_data_uri():
    raw_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    assert encode_image_to_data_uri(raw_uri) == raw_uri


def test_encode_image_preserves_url():
    web_url = "https://assets.example.com/mockups/robot_ui.png"
    assert encode_image_to_data_uri(web_url) == web_url


def test_non_existent_image_raises_error():
    with pytest.raises(FileNotFoundError):
        encode_image_to_data_uri("/path/that/does/not/exist/image_9999.png")


def test_format_multimodal_content_text_only():
    content = format_multimodal_content("Build a 3D app", images=None)
    assert isinstance(content, str)
    assert content == "Build a 3D app"

    content_empty = format_multimodal_content("Build a 3D app", images=[])
    assert isinstance(content_empty, str)


def test_format_multimodal_content_with_images(tmp_path):
    img_file = tmp_path / "spec.png"
    img_file.write_bytes(b"dummy")

    content = format_multimodal_content("Build UI matching spec", images=[str(img_file)])
    assert isinstance(content, list)
    assert len(content) == 2
    assert content[0] == {"type": "text", "text": "Build UI matching spec"}
    assert content[1]["type"] == "image_url"
    assert "data:image/png;base64," in content[1]["image_url"]["url"]


def test_parse_images_input(tmp_path):
    img_file = tmp_path / "wireframe.jpg"
    img_file.write_bytes(b"image content")

    uris = parse_images_input([str(img_file), "https://example.com/logo.png"])
    assert len(uris) == 2
    assert uris[0].startswith("data:image/jpeg;base64,")
    assert uris[1] == "https://example.com/logo.png"
