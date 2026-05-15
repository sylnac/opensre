"""Base tool interface for opensre integrations.

All tools must inherit from BaseTool and implement the required methods.
This follows the contract defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Encapsulates the result of a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must implement:
        - my_tool_name (property)
        - is_available (method)
        - extract_params (method)
        - run (method)

    Example usage::

        class MyTool(BaseTool):
            @property
            def my_tool_name(self) -> str:
                return "my_tool"

            def is_available(self) -> bool:
                return True

            def extract_params(self, raw: dict) -> dict:
                return {"key": raw.get("key")}

            def run(self, params: dict) -> ToolResult:
                return ToolResult(success=True, data=params)
    """

    @property
    @abstractmethod
    def my_tool_name(self) -> str:
        """Unique identifier for this tool."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the tool's dependencies/credentials are present."""
        ...

    @abstractmethod
    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate and extract parameters from a raw input dict.

        Args:
            raw: Unvalidated input dictionary, typically from an API request
                 or graph node payload.

        Returns:
            A cleaned parameter dictionary ready to pass to ``run``.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        ...

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            params: Validated parameters produced by ``extract_params``.

        Returns:
            A :class:`ToolResult` describing the outcome.
        """
        ...

    # ------------------------------------------------------------------
    # Convenience helpers available to all subclasses
    # ------------------------------------------------------------------

    def safe_run(self, raw: dict[str, Any]) -> ToolResult:
        """Validate params then run, catching any exception as a failed result.

        This is the recommended entry-point when calling tools from graph nodes
        so that a single misbehaving tool does not crash the whole pipeline.
        """
        if not self.is_available():
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available in this environment.",
            )
        try:
            params = self.extract_params(raw)
            return self.run(params)
        except ValueError as exc:
            return ToolResult(success=False, error=f"Parameter error: {exc}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                success=False,
                error=f"Unexpected error in '{self.my_tool_name}': {exc}",
            )

    def __repr__(self) -> str:  # pragma: no cover
        available = "available" if self.is_available() else "unavailable"
        return f"<{self.__class__.__name__} name={self.my_tool_name!r} {available}>"
