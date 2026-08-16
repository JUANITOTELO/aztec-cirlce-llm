"""
Prompt template registry with caching.
"""

from functools import lru_cache
from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def _load_template(name: str) -> Template:
    """Load prompt file once per process lifecycle for cache-friendly reuse."""
    filepath = PROMPTS_DIR / f"{name}.txt"
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt template '{name}' not found at {filepath}")
    return Template(filepath.read_text(encoding="utf-8"))


def render(name: str, **kwargs) -> str:
    """Render a named prompt template with variable substitution."""
    template = _load_template(name)
    return template.safe_substitute(**kwargs)


def get_raw_template(name: str) -> str:
    """Return raw template content."""
    filepath = PROMPTS_DIR / f"{name}.txt"
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt template '{name}' not found at {filepath}")
    return filepath.read_text(encoding="utf-8")
