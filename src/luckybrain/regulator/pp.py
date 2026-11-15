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

    #keyword details 
    @staticmethod
    def _pattern(keyword): 
        return re.compile(r'(?!\w)' + re.escape(keyword) + r'(?!\w)', re.IGNORECASE)

    def keyword_report(self, text, keywords): 
        """For each keyword: how often it appears and how many tokens it costs in this text
        (tokens of the text minus tokens of the text with the keyword removed). Biggest first."""
        total  = self.count(text=text)

        rows = []
        for kw in dict.fromkeys(k.strip() for k in self.keywords if k.strip()):
            pattern = self._pattern(kw)
            occurrences = len(pattern.findall(text))
            tokens = max(0, total - self.count(pattern.sub("", text))) if occurrences else 0
            row = {"keyword": kw, "occurrences": occurrences, "tokens": tokens,
                   "tokens_per_occurrence": round(tokens / occurrences, 2) if occurrences else 0,
                   "share": round(tokens / total, 4) if total else 0.0}

            if hasattr(self.counter, "pieces"): 
                row['pieces'] = self.counter.pieces(" "+kw)

            rows.append(row)

        return sorted(rows, key=lambda r: -r['tokens'])
    
    def top_terms(self, text, n=10, min_len=3):
        """Which words cost the most tokens in this text (occurrences x tokens per word)."""
        words = Counter(w.lower() for w in re.findall(r"\w+", text) if len(w) >= min_len)
        rows = []
        for word, occurrences in words.items():
            each = self.count(" " + word)
            rows.append({"term": word, "occurrences": occurrences, "tokens": each * occurrences})
        return sorted(rows, key=lambda r: (-r["tokens"], r["term"]))[:n]


    def _tracked(self,text): 
        if not self.track_keywords: 
            return []
        return [r for r in self.keyword_report(text, self.track_keywords) if r['occurrences']]

    # ---------- regulate the input ----------
    def regulate_input(self, messages):
        """Returns (messages_to_send, info). Raises TokenLimitError if it cannot fit."""
        messages = self._normalize(messages)
        info = self.measure(messages)
        limit, dropped = self.max_input_tokens, 0

        if limit is not None and info["total"] > limit:
            if self.on_input_overflow == "raise":
                raise TokenLimitError(f"Input is {info['total']} tokens, the limit is {limit}")
            system = [(m, t["tokens"]) for m, t in zip(messages, info["messages"]) if m["role"] == "system"]
            rest = [(m, t["tokens"]) for m, t in zip(messages, info["messages"]) if m["role"] != "system"]
            total = lambda: sum(t for _, t in system) + sum(t for _, t in rest)
            while len(rest) > 1 and total() > limit:             # drop the oldest turns, keep the newest
                rest.pop(0)
                dropped += 1
            while len(rest) > 1 and rest[0][0]["role"] != "user":     # models expect the first turn to be the user's
                rest.pop(0)
                dropped += 1
            if total() > limit:
                raise TokenLimitError(f"Even after trimming, the input is {total()} tokens, the limit is {limit}")
            messages = [m for m, _ in system + rest]
            info = self.measure(messages)

        info["trimmed"] = dropped
        info["keywords"] = self._tracked("\n".join(m["content"] for m in messages))
        return messages, info


    def regulate_output(self, text):
        """Returns (text, info). Applies forbidden words, then the length limit."""
        original_tokens = self.count(text)
        info = {"original_tokens": original_tokens, "truncated": False, "forbidden_found": [],
                "redacted": {}, "missing_required": [], "keywords": self._tracked(text)}

        for kw in self.forbidden:
            pattern = self._pattern(kw)
            found = len(pattern.findall(text))
            if not found:
                continue
            info["forbidden_found"].append(kw)
            if self.on_forbidden == "raise":
                raise ForbiddenContentError(f"The answer contains a forbidden word: {kw!r}")
            if self.on_forbidden == "redact":
                text = pattern.sub("[removed]", text)
                info["redacted"][kw] = found

        if self.max_output_tokens is not None and self.count(text) > self.max_output_tokens:
            text = self._truncate(text, self.max_output_tokens)
            info["truncated"] = True

        info["missing_required"] = [kw for kw in self.required if not self._pattern(kw).search(text)]
        info["tokens"] = self.count(text)
        return text, info


    def _truncate(self, text, limit):
        lo, hi = 0, len(text)
        while lo < hi:                                           # longest prefix that fits
            mid = (lo + hi + 1) // 2
            if self.count(text[:mid]) <= limit:
                lo = mid
            else:
                hi = mid - 1
        cut = text[:lo]
        ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)|\n", cut)]
        if ends and ends[-1] > len(cut) * 0.5:                   # prefer to stop at the end of a sentence
            cut = cut[:ends[-1]]
        return cut.rstrip()

    # ---------- the regulated call ----------
    def generate(self, messages):
        if self.brain is None:
            raise RuntimeError("Give the regulator a brain: TokenRegulator(brain=...)")
        messages, in_info = self.regulate_input(messages)
        self._check_budget(in_info["total"])

        raw = self.brain.generate(messages)
        raw_tokens = self.count(raw)
        self._add_usage(in_info["total"], raw_tokens)            # billed for what the model produced, even if we then cut it

        text, out_info = self.regulate_output(raw)
        report = {"input": in_info, "output": out_info,
                  "cost": self._cost(in_info["total"], raw_tokens), "counter": self.counter.name}
        with self._lock:
            self.last_report = report
            self.reports.append(report)
        return text

    # ---------- usage and budget ----------
    def reset_usage(self):
        with self._lock:
            self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": None}

    def _cost(self, tokens_in, tokens_out):
        if self.price_in is None and self.price_out is None:
            return None
        return (tokens_in * (self.price_in or 0) + tokens_out * (self.price_out or 0)) / 1_000_000

    def _check_budget(self, input_tokens):
        if self.max_total_tokens is None:
            return
        with self._lock:
            projected = self.usage["total_tokens"] + input_tokens + (self.max_output_tokens or 0)
        if projected > self.max_total_tokens:
            raise BudgetExceeded(f"This call would bring usage to about {projected} tokens, "
                                 f"the budget is {self.max_total_tokens}")

    def _add_usage(self, tokens_in, tokens_out):
        cost = self._cost(tokens_in, tokens_out)
        with self._lock:
            u = self.usage
            u["calls"] += 1
            u["input_tokens"] += tokens_in
            u["output_tokens"] += tokens_out
            u["total_tokens"] += tokens_in + tokens_out
            if cost is not None:
                u["cost"] = (u["cost"] or 0) + cost

    def summary(self):
        with self._lock:
            return {**self.usage, "counter": self.counter.name,
                    "budget_left": None if self.max_total_tokens is None
                    else max(0, self.max_total_tokens - self.usage["total_tokens"])}

    @staticmethod
    def _normalize(messages):
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        return [{"role": m["role"], "content": m["content"]} for m in messages]