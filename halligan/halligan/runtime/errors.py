from __future__ import annotations


class HalliganError(Exception):
    """Base error for runtime-related failures."""


class ConfigError(HalliganError):
    """Raised when runtime configuration is missing or unsafe."""


class ParseError(HalliganError):
    """Raised when a model response cannot be parsed into the expected JSON."""


class ValidationError(HalliganError):
    """Raised when parsed JSON does not conform to the expected schema."""


class UnsafeTargetError(HalliganError):
    """Raised when unsafe execution targets (e.g., non-local benchmark) are detected."""


class ToolError(HalliganError):
    """Raised when a tool invocation fails or is invalid."""
