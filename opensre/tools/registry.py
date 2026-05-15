"""Tool registry for managing and discovering available SRE tools."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from opensre.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available SRE tools.

    Provides registration, discovery, and execution of tools
    that can be used by the opensre agent.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance in the registry.

        Args:
            tool: An instance of BaseTool to register.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        name = tool.tool_name
        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered. "
                "Use replace=True to overwrite."
            )
        self._tools[name] = tool
        logger.debug("Registered tool: %s", name)

    def register_class(self, tool_cls: Type[BaseTool], **kwargs) -> None:
        """Instantiate and register a tool from its class.

        Args:
            tool_cls: A subclass of BaseTool to instantiate and register.
            **kwargs: Additional keyword arguments passed to the constructor.
        """
        instance = tool_cls(**kwargs)
        self.register(instance)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry by name.

        Args:
            name: The tool name to remove.

        Raises:
            KeyError: If no tool with the given name exists.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        del self._tools[name]
        logger.debug("Unregistered tool: %s", name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name.

        Args:
            name: The tool name to look up.

        Returns:
            The tool instance, or None if not found.
        """
        return self._tools.get(name)

    def list_available(self) -> List[str]:
        """Return names of all tools that report themselves as available.

        Returns:
            Sorted list of available tool names.
        """
        return sorted(
            name
            for name, tool in self._tools.items()
            if tool.is_available()
        )

    def list_all(self) -> List[str]:
        """Return names of all registered tools regardless of availability.

        Returns:
            Sorted list of all registered tool names.
        """
        return sorted(self._tools.keys())

    def execute(self, name: str, **params) -> ToolResult:
        """Execute a registered tool by name with the given parameters.

        Args:
            name: The name of the tool to execute.
            **params: Parameters forwarded to the tool's run method.

        Returns:
            A ToolResult containing the output or error information.
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' is not registered.",
            )

        if not tool.is_available():
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' is not currently available.",
            )

        logger.info("Executing tool '%s' with params: %s", name, params)
        return tool.run(**params)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Module-level default registry instance
default_registry = ToolRegistry()
