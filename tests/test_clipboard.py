"""
Unit tests for Aztec clipboard image extraction, TUI paste command, and CLI --paste options.
"""

import os
import subprocess
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from rich.console import Console
from typer.testing import CliRunner
from PIL import Image

from aztec_circle.adapters.clipboard_utils import (
    clean_image_path,
    has_clipboard_image,
    get_clipboard_image,
)
from aztec_circle.cli import app
from aztec_circle.tui.commands import cmd_paste, cmd_image
from aztec_circle.tui.session import SessionState

runner = CliRunner()


def test_clean_image_path():
    assert clean_image_path('"/home/user/photo.png"') == "/home/user/photo.png"
    assert clean_image_path("'/path/to/img.jpg'") == "/path/to/img.jpg"
    assert clean_image_path("file:///home/user/diagram.png") == "/home/user/diagram.png"
    assert clean_image_path("  https://example.com/asset.png  ") == "https://example.com/asset.png"


def test_get_clipboard_image_from_pillow(tmp_path):
    img = Image.new("RGB", (100, 100), color="blue")
    cache_dir = str(tmp_path / "aztec_images")

    with patch("PIL.ImageGrab.grabclipboard", return_value=img):
        saved_path = get_clipboard_image(cache_dir=cache_dir)
        assert saved_path is not None
        assert os.path.exists(saved_path)
        assert saved_path.endswith(".png")
        assert os.path.getsize(saved_path) > 0


def test_get_clipboard_image_from_file_path_in_clipboard(tmp_path):
    cache_dir = str(tmp_path / "aztec_images")
    sample_file = tmp_path / "sample.png"
    sample_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    with patch("PIL.ImageGrab.grabclipboard", return_value=[str(sample_file)]):
        saved_path = get_clipboard_image(cache_dir=cache_dir)
        assert saved_path == str(sample_file)


def test_get_clipboard_image_from_wl_paste(tmp_path):
    cache_dir = str(tmp_path / "aztec_images")

    def mock_run(args, **kwargs):
        if "--list-types" in args:
            return MagicMock(returncode=0, stdout="image/png\ntext/plain\n")
        if "--type" in args:
            stdout_file = kwargs.get("stdout")
            if stdout_file:
                stdout_file.write(b"\x89PNG\r\n\x1a\nfake_png_data")
            return MagicMock(returncode=0)
        return MagicMock(returncode=1)

    with patch("PIL.ImageGrab.grabclipboard", side_effect=Exception("Pillow not available")), \
         patch("shutil.which", return_value="/usr/bin/wl-paste"), \
         patch("sys.platform", "linux"), \
         patch("subprocess.run", side_effect=mock_run):
        saved = get_clipboard_image(cache_dir=cache_dir)
        assert saved is not None
        assert os.path.exists(saved)
        assert os.path.getsize(saved) > 0


def test_has_clipboard_image_true():
    img = Image.new("RGB", (10, 10))
    with patch("PIL.ImageGrab.grabclipboard", return_value=img):
        assert has_clipboard_image() is True


def test_has_clipboard_image_false():
    with patch("PIL.ImageGrab.grabclipboard", return_value=None), \
         patch("shutil.which", return_value=None):
        assert has_clipboard_image() is False


@pytest.mark.asyncio
async def test_cmd_paste_attaches_clipboard_image(tmp_path):
    img_file = tmp_path / "clip.png"
    img = Image.new("RGB", (20, 20), color="red")
    img.save(str(img_file))

    console = Console()
    state = SessionState()
    assert len(state.attached_images) == 0

    with patch("aztec_circle.adapters.clipboard_utils.get_clipboard_image", return_value=str(img_file)):
        await cmd_paste("", state, console)

    assert len(state.attached_images) == 1
    assert state.attached_images[0].startswith("data:image/png;base64,")
    assert "📷 1" in state.prompt_text()


@pytest.mark.asyncio
async def test_cmd_paste_no_image_reports_warning():
    console = Console(record=True)
    state = SessionState()

    with patch("aztec_circle.adapters.clipboard_utils.get_clipboard_image", return_value=None):
        await cmd_paste("", state, console)

    assert len(state.attached_images) == 0
    out = console.export_text()
    assert "No image data found" in out


@pytest.mark.asyncio
async def test_cmd_image_paste_delegates_to_cmd_paste(tmp_path):
    img_file = tmp_path / "clip.png"
    img = Image.new("RGB", (20, 20), color="green")
    img.save(str(img_file))

    console = Console()
    state = SessionState()

    with patch("aztec_circle.adapters.clipboard_utils.get_clipboard_image", return_value=str(img_file)):
        await cmd_image("paste", state, console)

    assert len(state.attached_images) == 1


def test_cli_edit_paste_flag(tmp_path):
    img_file = tmp_path / "screenshot.png"
    img = Image.new("RGB", (10, 10))
    img.save(str(img_file))

    with patch("aztec_circle.adapters.clipboard_utils.get_clipboard_image", return_value=str(img_file)), \
         patch("aztec_circle.cli._edit_async", new_callable=AsyncMock) as mock_edit:
        res = runner.invoke(app, ["edit", "Add a button", "--paste"])
        assert res.exit_code == 0
        mock_edit.assert_called_once()
        call_images = mock_edit.call_args[0][5]
        assert str(img_file) in call_images
