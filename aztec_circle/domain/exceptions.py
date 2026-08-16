"""
Domain exceptions for the Aztec Decision Circle.
"""


class AztecBaseException(Exception):
    """Base exception for all Aztec errors."""
    pass


class LoopLimitExceeded(AztecBaseException):
    """Raised when debate loops exceed MAX_DEBATE_LOOPS without consensus."""
    pass


class BudgetExceeded(AztecBaseException):
    """Raised when token spend exceeds BUDGET_LIMIT_USD."""
    pass


class YouthOverrideHalt(AztecBaseException):
    """Raised when Youth agents detect a critical showstopper anomaly."""
    def __init__(self, rationale: str):
        self.rationale = rationale
        super().__init__(f"Youth Override triggered: {rationale}")


class LLMProviderFailure(AztecBaseException):
    """Raised when primary and fallback LLM completions fail."""
    pass


class MCPToolTimeout(AztecBaseException):
    """Raised when an MCP tool invocation exceeds timeout."""
    pass


class MCPInjectionRisk(AztecBaseException):
    """Raised when an MCP tool payload triggers injection pattern filters."""
    pass
