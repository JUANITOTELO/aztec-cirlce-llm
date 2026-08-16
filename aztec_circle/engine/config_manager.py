"""
Production-ready configuration and API key manager with 0600 secure permissions.
"""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import litellm
litellm.drop_params = True
from aztec_circle.config import settings
from aztec_circle.domain.model_catalog import ModelCatalog, PRESET_CONFIGURATIONS, PROVIDER_KEY_MAP


class ConfigManager:
    """Manages secure ~/.aztec/config.env persistence, key masking, and model setup."""

    @classmethod
    def get_config_dir(cls) -> Path:
        """Return ~/.aztec directory ensuring 0700 secure permissions."""
        p = Path("~/.aztec").expanduser()
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(p, stat.S_IRWXU)  # 0700: rwx------
            except Exception:
                pass
        return p

    @classmethod
    def get_config_file_path(cls) -> Path:
        """Return ~/.aztec/config.env path ensuring 0600 secure permissions."""
        p = cls.get_config_dir() / "config.env"
        if not p.exists():
            p.touch(mode=0o600, exist_ok=True)
        else:
            try:
                os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)  # 0600: rw-------
            except Exception:
                pass
        return p

    @classmethod
    def mask_key(cls, key: Optional[str]) -> str:
        """Mask an API key for safe display in UI tables and logs."""
        if not key or len(key.strip()) < 8:
            return "[dim]Not Set[/dim]"
        k = key.strip()
        if len(k) <= 12:
            return f"{k[:3]}...****"
        return f"{k[:6]}...{k[-4:]}"

    @classmethod
    def load_config_into_env(cls) -> None:
        """Read ~/.aztec/config.env and propagate into os.environ and settings."""
        cfg_file = cls.get_config_file_path()
        if not cfg_file.exists():
            return

        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if v and k:
                        os.environ[k] = v
                        # Sync settings
                        if hasattr(settings, k):
                            setattr(settings, k, v)
        except Exception:
            pass

    @classmethod
    def save_api_key(cls, key_name: str, key_val: str) -> None:
        """Securely write an API key to ~/.aztec/config.env with 0600 permissions."""
        cfg_file = cls.get_config_file_path()
        key_name = key_name.strip().upper()
        key_val = key_val.strip()

        # Update environment and settings immediately
        os.environ[key_name] = key_val
        if key_name == "GEMINI_API_KEY":
            os.environ["GOOGLE_API_KEY"] = key_val
        if hasattr(settings, key_name):
            setattr(settings, key_name, key_val)

        # Update file safely
        lines: List[str] = []
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

        found = False
        new_lines: List[str] = []
        for line in lines:
            if line.strip().startswith(f"{key_name}="):
                new_lines.append(f"{key_name}={key_val}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key_name}={key_val}\n")

        with open(cfg_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        try:
            os.chmod(cfg_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except Exception:
            pass

    @classmethod
    def save_model_assignment(cls, rank: str, model_id: str) -> None:
        """Update model assignment in settings and persist to ~/.aztec/config.env."""
        rank = rank.strip().upper()
        setting_key = f"{rank}_MODEL"

        if hasattr(settings, setting_key):
            setattr(settings, setting_key, model_id)
            cls.save_api_key(setting_key, model_id)

    @classmethod
    def apply_preset(cls, preset_id: str) -> bool:
        """Apply one-click model configuration preset across all agent ranks."""
        preset = PRESET_CONFIGURATIONS.get(preset_id)
        if not preset:
            return False

        cls.save_api_key("AZTEC_ACTIVE_PRESET", preset_id)
        models = preset["models"]
        for rank, model_id in models.items():
            cls.save_model_assignment(rank, model_id)
        return True

    @classmethod
    def get_active_preset(cls) -> Optional[str]:
        """Return the active preset ID if configured and valid."""
        val = os.environ.get("AZTEC_ACTIVE_PRESET")
        if val and val in PRESET_CONFIGURATIONS:
            return val
        cfg_file = cls.get_config_file_path()
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("AZTEC_ACTIVE_PRESET="):
                            cand = line.split("=", 1)[1].strip().strip("'\"")
                            if cand in PRESET_CONFIGURATIONS:
                                return cand
            except Exception:
                pass
        return None

    @classmethod
    def get_api_keys_status(cls) -> List[Dict[str, Any]]:
        """Return status and masked keys for all supported LLM providers."""
        tracked_keys = [
            ("GEMINI_API_KEY", "Google Gemini (Flash & Pro)", "https://aistudio.google.com/app/apikey"),
            ("ANTHROPIC_API_KEY", "Anthropic Claude (3.7 Sonnet & 3.5)", "https://console.anthropic.com/settings/keys"),
            ("OPENAI_API_KEY", "OpenAI (GPT-4o & o3-mini)", "https://platform.openai.com/api-keys"),
            ("DEEPSEEK_API_KEY", "DeepSeek (R1 & V3)", "https://platform.deepseek.com/api_keys"),
            ("GROQ_API_KEY", "Groq LPU (Ultra-fast Llama & Qwen)", "https://console.groq.com/keys"),
            ("MISTRAL_API_KEY", "Mistral AI (Codestral & Large)", "https://console.mistral.ai/api-keys"),
            ("OPENROUTER_API_KEY", "OpenRouter (Unified Gateway)", "https://openrouter.ai/keys"),
        ]

        result: List[Dict[str, Any]] = []
        for key_name, provider_label, doc_url in tracked_keys:
            val = os.environ.get(key_name) or getattr(settings, key_name, None)
            is_set = bool(val and len(str(val).strip()) > 5 and not str(val).startswith("sk-ant-..."))
            result.append({
                "key_name": key_name,
                "provider": provider_label,
                "is_set": is_set,
                "masked": cls.mask_key(val) if is_set else "[red]Not Set[/red]",
                "doc_url": doc_url,
            })
        return result

    @classmethod
    async def test_model_connection(cls, model_id: str) -> Tuple[bool, str, float]:
        """
        Send a lightweight 1-token test ping to verify model connectivity and credentials.
        Returns (success, message, latency_seconds).
        """
        t0 = time.time()
        try:
            # Check validation first
            val = litellm.validate_environment(model_id)
            if not val.get("keys_in_environment", True):
                missing = val.get("missing_keys", [])
                return False, f"Missing API key: {', '.join(missing)}", 0.0

            res = await litellm.acompletion(
                model=model_id,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=15.0,
            )
            latency = time.time() - t0
            return True, "Connected successfully", latency
        except Exception as exc:
            latency = time.time() - t0
            err_msg = str(exc)
            if "AuthenticationError" in err_msg or "API key" in err_msg or "401" in err_msg:
                return False, "Authentication Failed (Invalid API Key)", latency
            elif "not_found_error" in err_msg or "NotFoundError" in err_msg or "404" in err_msg:
                return False, "Model Not Found / No Access on Key", latency
            elif "RateLimitError" in err_msg or "429" in err_msg:
                return False, "Rate Limit Exceeded / Out of Credits", latency
            return False, f"Error: {err_msg[:50]}", latency
