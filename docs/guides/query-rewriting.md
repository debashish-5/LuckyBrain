# Query rewriting

`QueryRewriting` is a small, experimental helper in
`luckybrain.query_imp`. It asks a chat model to rephrase search text. It does
not retrieve data, validate the model's factual accuracy, or guarantee
semantic equivalence.

## Usage

Pass an object that implements the synchronous `think(prompt: str) -> str`
method, such as either built-in chat client:

```python
from luckybrain.core.models import OpenaiBrain
from luckybrain.query_imp import QueryRewriting

rewriter = QueryRewriting(
    model=OpenaiBrain(model="gpt-4o-mini"),
    style="search",
)

clean_query = rewriter.improve("  how do i reset password?? ")
alternatives = rewriter.variants("reset account password", n=3)
```

## Constructor

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `model` | object with `think(prompt: str) -> str` | Required | Synchronous model used to generate rewrites. |
| `style` | `str \| None` | `"search"` | Exactly `"search"` requests keyword-focused wording. Any other value requests a well-formed question. |

## Methods

| Method | Input | Result |
| --- | --- | --- |
| `improve(query)` | A string. Whitespace-only input returns an empty string without a model call. | One rewritten string, stripped of surrounding whitespace and quote characters. |
| `variants(query, n=3)` | Search text and an optional result cap. | Up to `n` non-empty lines from the model, with common bullet prefixes removed. |

The number and quality of returned variants are not guaranteed. The helper
does not validate the model output or retry when fewer than `n` variants are
returned. The model controls cost, latency, privacy handling, and failure
behavior; its exceptions propagate to the caller.

## When to use it

Use query rewriting as an optional step when broadening or cleaning a search
query is useful. Preserve the original query as a fallback, and evaluate
retrieval quality with your own data before relying on rewrites. Do not use
generated alternatives as evidence or silently discard the user's intent.

This API is experimental and is not re-exported from the root `luckybrain`
package. Import it from `luckybrain.query_imp`.
