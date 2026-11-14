import math
import re 
import threading
from collections import Counter, deque






#error
class RegulationError(Exception): 
    """Base class for every rule violation."""

class TokenLimitError(RegulationError): 
    """The input is longer than max_input_tokens."""

class BudgetExceeded(RegulationError): 
    """The call would go over max_total_tokens."""

class ForbiddenContentError(RegulationError): 
    """The answer contains a forbidden keyword."""


class ApproxCounter: 
    """No dependencies. About 4 characters per token for English; it undercounts Hindi, Odia and other
    non-Latin scripts. Good for limits and budgets, not for exact billing."""
    name, exact = "approx (chars/4)", False

    def __call__(self, text): 
        return math.ceil(len(text)/4) if text else 0


class TikTokenCounter: 
    """Exact for OpenAI models (o200k_base = GPT-4o and newer, cl100k_base = GPT-4/3.5).
    Only an estimate for Claude, Llama, Grok, etc. Needs: pip install tiktoken"""
    exacrt = False

    def __init__(self,encoding="o200k_base"):
        import tiktoken
        self.enc = tiktoken.get_encoding(encoding)
        self.name = f'tiktoken: {encoding}'

    def __call__(self, text):
        return len(self.enc.encode(text=text, disallowed_special=())) if text else 0

    def pieces(self,text): 
        """The actual tokens the text is split into."""
        return [
            self.enc.decode_single_token_bytes(t).decode("utf-8",errors="replace")
            for t in self.enc.encode(text=text, disallowed_special=())
        ]


def default_counter(): 
    try: 
        return TikTokenCounter()
    except Exception:                  # not installed, or its data files cannot be downloaded
        return ApproxCounter()


#the regulator 
class TokenRegulator: 
    """Wraps a chat model (anything with .generate(messages)) and regulates what goes in and what comes out.
    It has the same .generate() as your models, so it plugs into Agent, RAGPipeline, Evaluator and the compressor."""

    def __init__(self,
                 brain = None, 
                 counter = None, 
                 max_input_tokens = None, 
                 max_output_tokens = None,
                 max_total_tokens = None, 
                 on_input_overflow = "raise", 
                 forbidden = (), 
                 on_forbidden = "redact", 
                 required = (), 
                 track_keywords = (), 
                 price_in = None, 
                 price_out = None, 
                 message_overhead = 4, 
                 keep_reports = 100

    ): 
        """
        max_input_tokens:  limit for one request.   on_input_overflow: "raise" or "trim" (drop the oldest turns).
        max_output_tokens: longer answers are cut (at a sentence end when possible).
        max_total_tokens:  budget for everything this regulator sends and receives. Raises BudgetExceeded.
        forbidden:         words that must not appear in answers.   on_forbidden: "redact", "raise" or "flag".
        required:          words the answer should contain (missing ones are reported, not enforced).
        track_keywords:    words whose token cost is reported for every call (input and output).
        price_in/out:      your price per MILLION tokens, to estimate cost. No defaults, because prices change.
        message_overhead:  extra tokens per chat message for role markers (about 3-4 on OpenAI-style APIs).
        """
        for name, value in (('max_input_tokens',max_input_tokens), ('max_output_tokens',max_output_tokens), ('max_total_tokens',max_total_tokens)): 
            if value is not None and value < 1: 
                raise ValueError(f"{name} must be at least 1.")

        if on_input_overflow not in ('raise','trim'): 
            raise ValueError("on_input_overflow must be 'raise' or 'trim'")

        if on_forbidden not in ("redact", "raise", "flag"):
            raise ValueError("on_forbidden must be 'redact', 'raise' or 'flag'")


        self.brain = brain
        self.counter = counter or default_counter()
        self.max_input_tokens,self.max_output_tokens = max_input_tokens, max_output_tokens
        self.max_total_tokens = max_total_tokens
        self.on_input_overflow,self.on_forbidden = on_input_overflow, on_forbidden
        self.track_keywords = list(track_keywords)
        self.price_in, self.price_out, self.message_overhead = price_in, price_out, message_overhead

        self._lock = threading.Lock()
        self.reports = deque(maxlen=keep_reports)
        self.last_report = None
        self.reset_usage()


    #counting 

    def count(self, text): 
        """Token count of a message list, in total, per role and per message."""
        return self.counter(text=text)

    def measure(self,messages): 
        """Token count of a message list, in total, per role and per message."""
        per_message = [{'role':m['role'],'tokens':self.count(m['content']) + self.message_overhead} for m in messages]
        by_role = {}
        for m in per_message: 
            by_role[m['role']] = by_role.get(m['role'], 0) + m['tokens']
        return {'total':sum(m['tokens'] for m in per_message), 'by_role':by_role, 'messages':per_message}

    def tokenizer(self, text): 
        """Show how the text is split into tokens."""
        if not hasattr(self.counter, "pieces"):
            raise NotImplementedError("This counter cannot show token pieces. Use TiktokenCounter.")
        return self.counter.pieces(text)


    # soonnnonn
    #sooneer 