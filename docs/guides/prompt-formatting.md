# Prompt formatting

`PromptFormat` is a small helper for composing reusable prompt templates with
Python-style `{variable}` placeholders. It is intentionally lightweight: it does
not perform retrieval, multi-step tool execution, or provider-specific prompt
engineering. Its main job is to keep prompts readable and to fail early if a
required value is missing.

## Why use it?

Prompt templates are helpful when you want to:

- reuse the same template across many requests,
- keep user or document variables separate from the prompt text,
- validate required inputs before sending a model call, and
- share a prompt skeleton between code paths without hard-coding values.

Useful patterns include product copy generation, system prompts with dynamic
context, evaluation instructions, and retrieval-grounded summarization.

## Importing

```python
from luckybrain.prompts import PromptFormat
```

## Basic usage

```python
from luckybrain.prompts import PromptFormat

prompt = PromptFormat(
    "Summarize the following article for a {audience} audience:\n\n{article}"
)

formatted = prompt.format(
    audience="technical",
    article="LuckyBrain keeps model integrations and retrieval contracts explicit.",
)
print(formatted)
```

If a required variable is absent, `PromptFormat.format()` raises a
`ValueError` before the prompt is sent to a model.

## Partial templates

Use `partial()` to fix one or more values now and fill the rest later:

```python
from luckybrain.prompts import PromptFormat

base_prompt = PromptFormat(
    "Rewrite this for a {audience} audience: {text}"
)

ready_prompt = base_prompt.partial(audience="executive")
print(ready_prompt.format(text="Vector search is a retrieval technique."))
```

This pattern is useful when many requests share the same system context or a
common variable such as topic, role, or output length.

## Sending directly to a chat model

`PromptFormat` can also format and send a prompt in one step when the model
implements the synchronous `think(prompt: str) -> str` interface:

```python
from luckybrain.core.models import OpenaiBrain
from luckybrain.prompts import PromptFormat

brain = OpenaiBrain(model="gpt-4o-mini")

prompt = PromptFormat(
    "Answer in {style} and keep it under {length} sentences: {question}"
)

answer = prompt.think(
    brain,
    style="plain English",
    length="three",
    question="What is a retriever in RAG?",
)
print(answer)
```

This is a convenience wrapper around `brain.think(prompt.format(...))`.

## Template syntax

The helper uses Python's standard `str.format` syntax. Examples include:

```python
PromptFormat("Hello {name}!")
PromptFormat("User {user.name} is active.")
PromptFormat("Primary item: {items[0]}")
```

The missing-variable check treats nested access like `{user.name}` as the
variable name `user`, which keeps validation simple and consistent with the
template's top-level inputs.

## Important limits

- It is only a prompt formatting helper; it does not enforce provider or model
  safety policies.
- It is designed for synchronous string templates, not complex structured
  message arrays.
- It keeps a lightweight in-memory representation of variables; it is not a
  prompt management system with versioning or storage.

Use it as a small building block, and compose it with the chat clients,
query-rewriting logic, or your own app-specific orchestration when needed.
