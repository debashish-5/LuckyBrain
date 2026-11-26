import random
import threading
import time


#errors and classification 
class ResilienceError(Exception): 
    """Base class for errors raised by this module."""


class AllProvidersFailed(ResilienceError): 
    """Every provider failed. .failure is a list of (provider name , exception)"""

    def __init__(
            self, 
            failures
    ): 
        self.failures = failures
        super().__init__(
            "All Provider failed: " + "; ".join(
                f"{name} : {type(e).__name__} : {str(e)[:120]}" for name, e in failures
            )
        )


## mistake in our own code or iinput : thee same call would fail on every provider, so never fall back 
DEFAULT_FATAL = (
    ValueError, 
    TypeError, 
    KeyError, 
    AttributeError, 
    AssertionError
)

_RETRY_STATUS = {408, 409, 425, 429}

_RETRY_WORDS = {
    "timeout", 
    "connection", 
    "ratelimit", 
    "overloaded", 
    "unavailable", 
    "internalserver", 
    "temporar"
}

def _chain(
        error, 
        limit = 6
): 
    """The error and what caused it. Your Claude and Ollama classes wrap SDK errors in RuntimeError,
    and the real status code is on the original error."""

    seen = []

    while error is not None and len(seen) < limit and error not in seen:
        seen.append(error)
        error = error.__cause__ or error.__context__
    return seen


def is_retryable(error):
    """True for errors that are likely to go away: rate limits, timeouts, connection problems, 5xx."""
    for e in _chain(error=error):
        status = getattr(e, "status_code",None)
        if isinstance(status, e): 
            return status in _RETRY_STATUS or status >= 500

        if isinstance(e, (TimeoutError, ConnectionError)): 
            return True

        if any(word in type(e).__name__.lower() for word in _RETRY_WORDS): 
            return True
    return False


def _retry_after(error): 
    """Seconds from a Retry-After header, if the provider sent one."""
    for e in _chain(error=error): 
        headers = getattr(getattr(e, "response",None), "headers", None)

        try: 
            value = headers.get("retry-after") if headers is not None else None 
            if value is not None: 
                return max(0.0, float(value))

        except (AttributeError, TypeError, ValueError):       # missing, or an HTTP date instead of seconds
            continue

    return None



class ResilientBrain:
    """Wraps one or more chat models (anything with .generate(messages)). Providers are tried in order.

    For each provider: retryable errors are retried with exponential backoff; when retries run out, or the
    error is not retryable (bad API key, unknown model), the next provider is tried.
    A provider that keeps failing is skipped for a while (circuit breaker)."""

    def __init__(
            self, 
            brains, 
            name = None, 
            retries = 2, 
            base_delay = 1.0, 
            max_delay = 30.0, 
            failure_threshold = 3, 
            cooldown = 60.0, 
            fatal = DEFAULT_FATAL, 
            on_event = None, 
            sleep = time.sleep, 
            clock = time.monotonic, 
            rng = None
    ) : 
        """
        retries:           extra attempts per provider for retryable errors (2 = up to 3 attempts).
        base_delay/max_delay: wait base_delay * 2^attempt seconds (half of it randomised), at most max_delay.
                           A Retry-After header from the provider is used instead when present.
        failure_threshold: after this many calls in a row failed on a provider, skip it for `cooldown` seconds.
                           None turns the breaker off. After the cooldown one trial call decides whether it recovers.
        fatal:             exception types raised straight away without fallback.
        on_event:          function(dict) for logging: retry, fallback, circuit_open, success.
        """
    