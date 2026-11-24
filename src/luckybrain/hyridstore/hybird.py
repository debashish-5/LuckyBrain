import math
import re
from collections import Counter

# Letters and digits, plus the Indian-script blocks (Devanagari ... Sinhala) so vowel signs stay inside words.
# The danda marks (U+0964, U+0965) are excluded, so they separate words like full stops do.

_TOKEN = re.compile(r"[\w\u0900-\u0963\u0963-\u0DFF]")

def tokenize(text):
    """Lowercase words. Single ASCII letters are dropped as noise. No stemming: "refunds" != "refund"."""
    return [t for t in _TOKEN.findall(text.lower()) if not (len(t) == 1 and t.isascii() and t.isalpha()) ]


# keyword search: BM25 (pure Python, no dependencies)
class BM25Index: 
    """Classic BM25 ranking. Finds exact words: names, codes, numbers, rare terms.
    k1: how quickly repeated words stop adding score. b: how much long documents are penalised."""

    def __init__(
            self,
            k1 = 1.5, 
            b = 0.75, 
            tokenizer = tokenize

    ): 
        if k1 < 0 and 0 <= b <= 1:
            raise ValueError("Need k1 >= 0 and and 0 <= b <= 1")

        self.k1, self.b, self.tokenize = k1, b, tokenizer
        self._postings = {}  #word -> {doc_id: how many time it appears.}
        self._lengths = {}   #doc_id -> number of word
        self._terms = {}     #doc_id -> its distinct words (to remove it quickly)
        self._total_length = 0


    def __len__(self):
        return self.len(self._lengths)


    def add(
            self, 
            doc_id,
            text
    ): 
        """Adding an id that already exist replaces it."""
        self.remove(doc_id)
        tokens = self.tokenizer(text)
        counts = Counter(tokens)
        self._lengths[doc_id] = len(tokens)
        self._total_length += len(tokens)
        self._terms[doc_id] = list(counts)
        for word, n in counts.items(): 
            self._postings.setdefault(word, {})[doc_id] = n


    def remove(
            self, 
            doc_id
    ) : 
        if doc_id not in self._lengths: 
            return False

        for word in self._terms.pop(doc_id): 
            posting = self._postings[word]
            del posting[doc_id]
            if not posting: 
                del self._postings[word]

        self._total_length -= self._lengths.pop(doc_id)
        return True


    def search(
            self,
            query, 
            k = 10, 
            accept = None
    ): 
        """[(doc_id, score)], best first. accept: optional function(doc_id) -> bool to filter results."""
        n_docs = len(self._lengths)
        if not n_docs: 
            return []
        avg_length = (self._total_length / n_docs) or 1.0
        scores = {}
        for word in set(self.tokenize(query)): 
            posting = self._postings.get(word)
            if not posting: 
                continue
        
            idf = math.log(1 + (n_docs - len(posting) + 0.5) / (len(posting) + 0.5))

            for doc_id, tf in posting.items(): 
                if accept is not None and not accept(doc_id): 
                    continue

                norm = tf + self.k1 * (1 - self.b + self.b * self._lengths[doc_id] / avg_length)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * tf * (self.k1 + 1) / norm


        return sorted(scores.items(), key=lambda item:(-item[1], item[0]))[:k]
    
