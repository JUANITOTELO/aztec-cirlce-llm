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

    ROLE_KEY_MAP = {
        "YOUTH": "YOUTH_MODEL",
        "YOUTH_CHAOS": "YOUTH_CHAOS_MODEL",
        "CHAOS": "YOUTH_CHAOS_MODEL",
        "YOUTH_ADVOCATE": "YOUTH_ADVOCATE_MODEL",
        "ADVOCATE": "YOUTH_ADVOCATE_MODEL",
        "PEER": "PEER_MODEL",
        "PATCH": "PATCH_MODEL",
        "PATCH_AGENT": "PATCH_MODEL",
        "FIXER": "FIXER_MODEL",
        "FIX": "FIXER_MODEL",
        "BUILD_FIXER": "FIXER_MODEL",
        "ELDER": "ELDER_MODEL",
        "ELDER_SECURITY": "ELDER_SECURITY_MODEL",
        "SECURITY": "ELDER_SECURITY_MODEL",
        "ELDER_STRUCTURAL": "ELDER_STRUCTURAL_MODEL",
        "STRUCTURAL": "ELDER_STRUCTURAL_MODEL",
        "FALLBACK": "FALLBACK_MODEL",
    }

    @classmethod
    def normalize_role_key(cls, role_or_rank: str) -> str:
        """Map role or rank alias to standard setting key name."""
        cleaned = role_or_rank.strip().upper().replace("-", "_")
        return cls.ROLE_KEY_MAP.get(cleaned, f"{cleaned}_MODEL" if not cleaned.endswith("_MODEL") else cleaned)

    @classmethod
    def save_model_assignment(cls, role_or_rank: str, model_id: str) -> None:
        """Update model assignment in settings and persist to ~/.aztec/config.env."""
        setting_key = cls.normalize_role_key(role_or_rank)

        if hasattr(settings, setting_key):
            setattr(settings, setting_key, model_id)
            cls.save_api_key(setting_key, model_id)

    @classmethod
    def reset_model_assignment(cls, role_or_rank: str) -> None:
        """Reset a sub-role model assignment to None so it inherits from parent rank."""
        setting_key = cls.normalize_role_key(role_or_rank)
        if hasattr(settings, setting_key) and not setting_key.endswith(("_MODEL",)) or setting_key in ("YOUTH_CHAOS_MODEL", "YOUTH_ADVOCATE_MODEL", "ELDER_SECURITY_MODEL", "ELDER_STRUCTURAL_MODEL", "PATCH_MODEL", "FIXER_MODEL"):
            setattr(settings, setting_key, None)
            cfg_file = cls.get_config_file_path()
            if cfg_file.exists():
                with open(cfg_file, "r", encoding="utf-8") as f:
                    lines = [line for line in f if not line.strip().startswith(f"{setting_key}=")]
                with open(cfg_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            os.environ.pop(setting_key, None)

    @classmethod
    def get_granular_roles_status(cls) -> List[Dict[str, Any]]:
        """Return full status and model assignments across all ranks and granular roles."""
        role_definitions = [
            ("YOUTH", "Youth (Rank Default)", "YOUTH", settings.YOUTH_MODEL, "Exploratory brainstormers baseline"),
            ("YOUTH_CHAOS", "Youth (Chaos Brainstormer)", "YOUTH", settings.YOUTH_CHAOS_MODEL, "High-temperature divergent exploration"),
            ("YOUTH_ADVOCATE", "Youth (Devil's Advocate)", "YOUTH", settings.YOUTH_ADVOCATE_MODEL, "Contrarian stress tester & showstopper risk detection"),
            ("PEER", "Peer Drafter (Primary)", "PEER", settings.PEER_MODEL, "System architecture & atomic code synthesis"),
            ("PATCH", "Patch Agent (Precision Edit)", "PEER", settings.PATCH_MODEL, "2-round token-efficient line-range patch generator"),
            ("FIXER", "Build Fixer (Compiler Repair)", "PEER", settings.FIXER_MODEL, "Diagnostic parser & self-healing file repair"),
            ("ELDER", "Elder Council (Rank Default)", "ELDER", settings.ELDER_MODEL, "Security & structural auditing baseline"),
            ("ELDER_SECURITY", "Elder (Security Governance)", "ELDER", settings.ELDER_SECURITY_MODEL, "Security audit, injection defense & credential governance"),
            ("ELDER_STRUCTURAL", "Elder (Structural Architect)", "ELDER", settings.ELDER_STRUCTURAL_MODEL, "Architecture modularity, SRP & database schema auditing"),
            ("FALLBACK", "Fallback (Emergency Failover)", "AUXILIARY", settings.FALLBACK_MODEL, "Automatic failover provider upon rate-limits or timeouts"),
        ]

        roles_status = []
        for role_key, role_label, rank_group, configured_val, desc in role_definitions:
            effective = settings.get_effective_model(role_key)
            is_override = bool(configured_val is not None and not role_key.endswith(("DEFAULT", "PEER", "YOUTH", "ELDER", "FALLBACK")))
            info = ModelCatalog.get_model_info(effective)

            roles_status.append({
                "role_key": role_key,
                "role_label": role_label,
                "rank_group": rank_group,
                "configured_val": configured_val,
                "effective_model": effective,
                "is_override": is_override,
                "description": desc,
                "model_info": info,
            })
        return roles_status

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
