"""Provider-neutral contracts for tools used by agent workflows."""

from collections.abc import Mapping
from typing import Protocol


class AgentTool(Protocol):
    """A named capability an agent can invoke with structured input."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    async def invoke(self, inputs: Mapping[str, object]) -> object: ...