"""Simple string templates for model prompts."""

from string import Formatter

from luckybrain.core.models import BaseChatModel


def _find_variables(template: str) -> list[str]:
    """Return unique variable names used by a template in insertion order."""
    names: list[str] = []
    for _, field, _, _ in Formatter().parse(template):
        if not field:
            continue
        name = field.split(".")[0].split("[")[0]
        if name and name not in names:
            names.append(name)
    return names


class PromptFormat:
    """Store a prompt template and validate the variables needed to format it.

    The template uses Python's standard ``str.format`` syntax, so values such as
    ``{topic}``, ``{user.name}``, and ``{items[0]}`` are supported. Nested fields
    resolve to the top-level variable name when validating missing values.
    """

    def __init__(self, template: str, partial_variables: dict[str, object] | None = None) -> None:
        if not isinstance(template, str) or not template.strip():
            raise ValueError("Prompt template must not be empty.")

        self.template = template
        self.partial_variables = dict(partial_variables or {})
        self.input_variables = [
            variable for variable in _find_variables(template=template) if variable not in self.partial_variables
        ]

    @classmethod
    def from_template(cls, template: str) -> "PromptFormat":
        """Create a prompt formatter from a template string."""
        return cls(template)

    def partial(self, **kwargs: object) -> "PromptFormat":
        """Freeze some variables now and fill in the remaining ones later."""
        return PromptFormat(self.template, {**self.partial_variables, **kwargs})

    def format(self, **kwargs: object) -> str:
        """Render the template after validating all required variables."""
        values = {**self.partial_variables, **kwargs}
        missing = [variable for variable in self.input_variables if variable not in values]
        if missing:
            raise ValueError(f"Missing variables:{missing}")
        return self.template.format(**values)

    def think(self, brain: BaseChatModel, **kwargs: object) -> str:
        """Format the prompt and send it directly to a chat model."""
        return brain.think(self.format(**kwargs))

    def __repr__(self) -> str:
        return f"PromptFormat(variables={self.input_variables})"
