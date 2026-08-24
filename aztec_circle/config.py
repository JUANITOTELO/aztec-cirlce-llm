import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

# Load local .env and user ~/.aztec/config.env
load_dotenv()
_user_cfg = Path("~/.aztec/config.env").expanduser()
if _user_cfg.exists():
    load_dotenv(dotenv_path=_user_cfg)


def is_valid_key(key: Optional[str]) -> bool:
    """Check whether a key is non-empty and not a template placeholder."""
    if not key:
        return False
    k = key.strip()
    if k.startswith("sk-ant-...") or k.startswith("sk-...") or k.startswith("AIza...") or len(k) < 15:
        return False
    return True


def normalize_model_name(model: str) -> str:
    """Ensure LiteLLM provider prefix is present."""
    m = model.strip()
    if m.startswith("claude-") and not m.startswith("anthropic/"):
        return f"anthropic/{m}"
    if (m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3")) and not m.startswith("openai/"):
        return f"openai/{m}"
    if m.startswith("gemini-") and not m.startswith("gemini/"):
        return f"gemini/{m}"
    return m


class Settings(BaseSettings):
    # LLM Provider Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_AI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Model configuration (Rank baselines)
    YOUTH_MODEL: str = "gemini/gemini-3.7-flash"
    PEER_MODEL: str = "gemini/gemini-3.7-flash"
    ELDER_MODEL: str = "gemini/gemini-2.5-pro"
    FALLBACK_MODEL: Optional[str] = "gemini/gemini-3.7-flash"

    # Granular Sub-Role Overrides (Optional - inherit from rank if None)
    YOUTH_CHAOS_MODEL: Optional[str] = None
    YOUTH_ADVOCATE_MODEL: Optional[str] = None
    ELDER_SECURITY_MODEL: Optional[str] = None
    ELDER_STRUCTURAL_MODEL: Optional[str] = None
    PATCH_MODEL: Optional[str] = None
    FIXER_MODEL: Optional[str] = None

    def get_effective_model(self, role_or_rank: str) -> str:
        """
        Resolve the effective model for a specific rank or sub-role with hierarchical fallback.
        Hierarchy:
        - YOUTH_CHAOS -> YOUTH_CHAOS_MODEL or YOUTH_MODEL
        - YOUTH_ADVOCATE -> YOUTH_ADVOCATE_MODEL or YOUTH_MODEL
        - PEER -> PEER_MODEL
        - PATCH -> PATCH_MODEL or PEER_MODEL
        - FIXER -> FIXER_MODEL or PEER_MODEL
        - ELDER_SECURITY -> ELDER_SECURITY_MODEL or ELDER_MODEL
        - ELDER_STRUCTURAL -> ELDER_STRUCTURAL_MODEL or ELDER_MODEL
        - FALLBACK -> FALLBACK_MODEL or PEER_MODEL
        """
        r = role_or_rank.strip().upper()
        if r in ("YOUTH_CHAOS", "CHAOS_BRAINSTORMER"):
            return normalize_model_name(self.YOUTH_CHAOS_MODEL or self.YOUTH_MODEL)
        elif r in ("YOUTH_ADVOCATE", "DEVILS_ADVOCATE"):
            return normalize_model_name(self.YOUTH_ADVOCATE_MODEL or self.YOUTH_MODEL)
        elif r in ("ELDER_SECURITY", "SECURITY_GOVERNANCE"):
            return normalize_model_name(self.ELDER_SECURITY_MODEL or self.ELDER_MODEL)
        elif r in ("ELDER_STRUCTURAL", "STRUCTURAL_PERF", "STRUCTURAL_ARCHITECT"):
            return normalize_model_name(self.ELDER_STRUCTURAL_MODEL or self.ELDER_MODEL)
        elif r in ("PATCH", "PATCH_AGENT"):
            return normalize_model_name(self.PATCH_MODEL or self.PEER_MODEL)
        elif r in ("FIXER", "BUILD_FIXER"):
            return normalize_model_name(self.FIXER_MODEL or self.PEER_MODEL)
        elif r == "YOUTH":
            return normalize_model_name(self.YOUTH_MODEL)
        elif r == "PEER":
            return normalize_model_name(self.PEER_MODEL)
        elif r == "ELDER":
            return normalize_model_name(self.ELDER_MODEL)
        elif r == "FALLBACK":
            return normalize_model_name(self.FALLBACK_MODEL or self.PEER_MODEL)
        else:
            attr = f"{r}_MODEL"
            if hasattr(self, attr) and getattr(self, attr):
                return normalize_model_name(str(getattr(self, attr)))
            return normalize_model_name(self.PEER_MODEL)

    # Debate governance
    MAX_DEBATE_LOOPS: int = 2
    BUDGET_LIMIT_USD: float = 1.00
    ELDER_THINKING_BUDGET: int = 1024
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_STREAMING: bool = True
    LLM_CHUNK_TIMEOUT_SECONDS: float = 90.0

    # Neuroplasticity subsystem (adaptive weights / thresholds / routing / memory)
    PLASTICITY_ENABLED: bool = True
    PLASTICITY_STATE_PATH: str = "~/.aztec/plasticity_state.json"
    PLASTICITY_DB_PATH: str = "~/.aztec/experience.db"
    PEER_ESCALATION_MODEL: Optional[str] = None  # defaults to ELDER_MODEL at runtime
    PLASTICITY_BASE_THRESHOLD: float = 8.0
    PLASTICITY_THRESHOLD_FLOOR: float = 7.0
    PLASTICITY_THRESHOLD_CEILING: float = 9.0
    LLM_MODEL_CASCADE: Optional[str] = None  # comma-separated extra failover models

    # Dynamic model discovery (OpenRouter live catalog + local servers)
    LMSTUDIO_BASE_URL: str = ""  # e.g. "http://localhost:1234/v1" (opt-in)
    LLAMACPP_BASE_URL: str = "http://localhost:8080"  # llama.cpp server (docker or native)
    MODEL_DISCOVERY_TTL_HOURS: float = 6.0
    MODEL_DISCOVERY_TIMEOUT_SECONDS: float = 8.0

    # MCP Client
    MCP_SERVER_URI: str = "http://localhost:8765"
    MCP_TOOL_TIMEOUT_SECONDS: float = 15.0

    # Persistence
    CHECKPOINT_DB_PATH: str = "./aztec_runs.db"

    model_config = SettingsConfigDict(
        env_file=(".env", str(_user_cfg)),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Clean up placeholder keys from environment and propagate valid ones
if is_valid_key(settings.GOOGLE_AI_API_KEY):
    os.environ["GEMINI_API_KEY"] = settings.GOOGLE_AI_API_KEY
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_AI_API_KEY
elif not is_valid_key(os.environ.get("GEMINI_API_KEY")):
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_API_KEY", None)

if is_valid_key(settings.ANTHROPIC_API_KEY):
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
else:
    os.environ.pop("ANTHROPIC_API_KEY", None)

if is_valid_key(settings.OPENAI_API_KEY):
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
else:
    os.environ.pop("OPENAI_API_KEY", None)

if is_valid_key(settings.DEEPSEEK_API_KEY):
    os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY

if is_valid_key(settings.GROQ_API_KEY):
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

if is_valid_key(settings.MISTRAL_API_KEY):
    os.environ["MISTRAL_API_KEY"] = settings.MISTRAL_API_KEY

if is_valid_key(settings.OPENROUTER_API_KEY):
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY

has_anthropic = is_valid_key(os.environ.get("ANTHROPIC_API_KEY"))
has_openai = is_valid_key(os.environ.get("OPENAI_API_KEY"))
has_gemini = is_valid_key(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

# If Anthropic is unavailable, route Claude models to Gemini
if not has_anthropic and has_gemini:
    if "claude" in settings.PEER_MODEL.lower():
        settings.PEER_MODEL = "gemini/gemini-2.5-flash"
    if "claude" in settings.ELDER_MODEL.lower():
        settings.ELDER_MODEL = "gemini/gemini-2.5-pro"
    if "claude" in settings.YOUTH_MODEL.lower():
        settings.YOUTH_MODEL = "gemini/gemini-2.5-flash"

# If OpenAI is unavailable, route GPT fallback to Gemini
if not has_openai and has_gemini:
    if settings.FALLBACK_MODEL and "gpt" in settings.FALLBACK_MODEL.lower():
        settings.FALLBACK_MODEL = "gemini/gemini-2.5-flash"

# Normalize model names with provider prefixes
settings.YOUTH_MODEL = normalize_model_name(settings.YOUTH_MODEL)
settings.PEER_MODEL = normalize_model_name(settings.PEER_MODEL)
settings.ELDER_MODEL = normalize_model_name(settings.ELDER_MODEL)
if settings.FALLBACK_MODEL:
    settings.FALLBACK_MODEL = normalize_model_name(settings.FALLBACK_MODEL)

for sub_role in ("YOUTH_CHAOS_MODEL", "YOUTH_ADVOCATE_MODEL", "ELDER_SECURITY_MODEL", "ELDER_STRUCTURAL_MODEL", "PATCH_MODEL", "FIXER_MODEL"):
    val = getattr(settings, sub_role, None)
    if val:
        setattr(settings, sub_role, normalize_model_name(str(val)))

