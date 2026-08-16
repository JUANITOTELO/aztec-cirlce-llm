"""
Cross-platform clipboard image extraction utilities.
Supports Pillow ImageGrab, Linux Wayland (wl-paste), Linux X11 (xclip), macOS (osascript), Windows (PowerShell),
and text-based image path resolution.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List
import structlog

log = structlog.get_logger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}


def clean_image_path(raw_path: str) -> str:
    """Sanitize dragged or pasted image path string, removing file:// URIs, quotes, and whitespace."""
    cleaned = raw_path.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("file://"):
        cleaned = cleaned[7:].strip()
    return cleaned


def has_clipboard_image() -> bool:
    """Fast check to determine if the clipboard currently contains image data."""
    # 1. Linux Wayland check
    if sys.platform.startswith("linux") and shutil.which("wl-paste"):
        try:
            res = subprocess.run(["wl-paste", "--list-types"], capture_output=True, text=True, timeout=1.0)
            if res.returncode == 0:
                output = res.stdout.lower()
                if "image/png" in output or "image/jpeg" in output or "image/webp" in output:
                    return True
        except Exception:
            pass

    # 2. Linux X11 check
    if sys.platform.startswith("linux") and shutil.which("xclip"):
        try:
            res = subprocess.run(["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"], capture_output=True, text=True, timeout=1.0)
            if res.returncode == 0:
                output = res.stdout.lower()
                if "image/png" in output or "image/jpeg" in output:
                    return True
        except Exception:
            pass

    # 3. Pillow ImageGrab check
    try:
        from PIL import ImageGrab, Image
        data = ImageGrab.grabclipboard()
        if isinstance(data, Image.Image):
            return True
        if isinstance(data, list) and data:
            for item in data:
                if isinstance(item, str) and Path(item).suffix.lower() in IMAGE_EXTENSIONS:
                    return True
    except Exception:
        pass

    return False


def get_clipboard_image(cache_dir: str = ".aztec_images") -> Optional[str]:
    """
    Extracts image data or image path from system clipboard and saves it to cache_dir.
    Returns the absolute or relative path to the saved image file, or None if no image found.
    """
    os.makedirs(cache_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    target_filename = f"clipboard_{timestamp}.png"
    target_path = os.path.join(cache_dir, target_filename)

    # ----------------------------------------------------
    # Method 1: Pillow ImageGrab (Cross-platform)
    # ----------------------------------------------------
    try:
        from PIL import ImageGrab, Image
        clip_data = ImageGrab.grabclipboard()
        if isinstance(clip_data, Image.Image):
            clip_data.save(target_path, format="PNG")
            log.info("clipboard.saved_via_pillow", path=target_path)
            return target_path

        if isinstance(clip_data, list) and clip_data:
            for item in clip_data:
                if isinstance(item, str):
                    cleaned = clean_image_path(item)
                    if os.path.exists(cleaned) and Path(cleaned).suffix.lower() in IMAGE_EXTENSIONS:
                        return cleaned
    except Exception as exc:
        log.debug("clipboard.pillow_attempt_failed", error=str(exc))

    # ----------------------------------------------------
    # Method 2: Linux Wayland (wl-paste)
    # ----------------------------------------------------
    if sys.platform.startswith("linux") and shutil.which("wl-paste"):
        try:
            types_res = subprocess.run(["wl-paste", "--list-types"], capture_output=True, text=True, timeout=1.0)
            if types_res.returncode == 0:
                types_out = types_res.stdout.lower()
                mime_type = None
                if "image/png" in types_out:
                    mime_type = "image/png"
                elif "image/jpeg" in types_out or "image/jpg" in types_out:
                    mime_type = "image/jpeg"
                elif "image/webp" in types_out:
                    mime_type = "image/webp"

                if mime_type:
                    with open(target_path, "wb") as f:
                        proc = subprocess.run(["wl-paste", "--type", mime_type], stdout=f, stderr=subprocess.PIPE, timeout=2.0)
                    if proc.returncode == 0 and os.path.getsize(target_path) > 0:
                        log.info("clipboard.saved_via_wl_paste", path=target_path)
                        return target_path
                    else:
                        if os.path.exists(target_path):
                            os.remove(target_path)
        except Exception as exc:
            log.debug("clipboard.wl_paste_failed", error=str(exc))

    # ----------------------------------------------------
    # Method 3: Linux X11 (xclip)
    # ----------------------------------------------------
    if sys.platform.startswith("linux") and shutil.which("xclip"):
        try:
            with open(target_path, "wb") as f:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=2.0,
                )
            if proc.returncode == 0 and os.path.getsize(target_path) > 0:
                log.info("clipboard.saved_via_xclip", path=target_path)
                return target_path
            else:
                if os.path.exists(target_path):
                    os.remove(target_path)
        except Exception as exc:
            log.debug("clipboard.xclip_failed", error=str(exc))

    # ----------------------------------------------------
    # Method 4: macOS (osascript / pngpaste)
    # ----------------------------------------------------
    if sys.platform == "darwin":
        if shutil.which("pngpaste"):
            try:
                proc = subprocess.run(["pngpaste", target_path], capture_output=True, timeout=2.0)
                if proc.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                    log.info("clipboard.saved_via_pngpaste", path=target_path)
                    return target_path
            except Exception:
                pass

        try:
            apple_script = f"""
            set theFile to (POSIX file "{os.path.abspath(target_path)}")
            try
                open for access theFile with write permission
                write (the clipboard as «class PNGf») to theFile
                close access theFile
            on error
                try
                    close access theFile
                end try
            end try
            """
            proc = subprocess.run(["osascript", "-e", apple_script], capture_output=True, timeout=2.0)
            if proc.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                log.info("clipboard.saved_via_osascript", path=target_path)
                return target_path
            else:
                if os.path.exists(target_path):
                    os.remove(target_path)
        except Exception as exc:
            log.debug("clipboard.osascript_failed", error=str(exc))

    # ----------------------------------------------------
    # Method 5: Windows PowerShell
    # ----------------------------------------------------
    if sys.platform == "win32" or shutil.which("powershell.exe"):
        try:
            ps_cmd = (
                f"Add-Type -AssemblyName System.Windows.Forms; "
                f"$img = [System.Windows.Forms.Clipboard]::GetImage(); "
                f"if ($img -ne $null) {{ $img.Save('{os.path.abspath(target_path)}', [System.Drawing.Imaging.ImageFormat]::Png); exit 0 }} else {{ exit 1 }}"
            )
            proc = subprocess.run(["powershell.exe", "-Command", ps_cmd], capture_output=True, timeout=3.0)
            if proc.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                log.info("clipboard.saved_via_powershell", path=target_path)
                return target_path
            else:
                if os.path.exists(target_path):
                    os.remove(target_path)
        except Exception as exc:
            log.debug("clipboard.powershell_failed", error=str(exc))

    # ----------------------------------------------------
    # Method 6: Inspect text in clipboard for file path or URL
    # ----------------------------------------------------
    try:
        text_content = ""
        if sys.platform.startswith("linux") and shutil.which("wl-paste"):
            t_proc = subprocess.run(["wl-paste", "--type", "text/plain"], capture_output=True, text=True, timeout=1.0)
            if t_proc.returncode == 0:
                text_content = t_proc.stdout.strip()
        elif sys.platform.startswith("linux") and shutil.which("xclip"):
            t_proc = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=1.0)
            if t_proc.returncode == 0:
                text_content = t_proc.stdout.strip()

        if text_content:
            clean = clean_image_path(text_content)
            if clean.startswith("http://") or clean.startswith("https://") or clean.startswith("data:image/"):
                return clean
            if os.path.exists(clean) and Path(clean).suffix.lower() in IMAGE_EXTENSIONS:
                return clean
    except Exception:
        pass

    return None
