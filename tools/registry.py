from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    parameters: dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning("Overwriting tool: %s", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def run(self, name: str, **kwargs) -> Any:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")
        logger.info("Running tool: %s with args: %s", name, kwargs)
        return tool.fn(**kwargs)

    def to_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def tool(
    name: str = "",
    description: str = "",
    **param_spec,
):
    def decorator(fn):
        tool_name = name or fn.__name__
        tool_desc = description or fn.__doc__ or ""
        t = Tool(name=tool_name, description=tool_desc, fn=fn, parameters=param_spec)
        get_registry().register(t)
        return fn
    return decorator
