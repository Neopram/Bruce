# Indice vectorial cognitivo
import math
import re
from collections import Counter, defaultdict


class CognitiveIndex:
    """Vector cognitive index using TF-IDF keyword matching for document search."""

    def __init__(self):
        self._documents = []
        self._doc_vectors = []
        self._vocabulary = {}
        self._idf = {}
        self._built = False

    def _tokenize(self, text):
        """Tokenize text into lowercase words."""
        return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())

    def _compute_tf(self, tokens):
        """Compute term frequency for a list of tokens."""
        counts = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {term: count / total for term, count in counts.items()}

    def _compute_idf(self):
        """Compute inverse document frequency across all documents."""
        num_docs = len(self._documents)
        if num_docs == 0:
            return
        doc_freq = defaultdict(int)
        for doc in self._documents:
            tokens = set(self._tokenize(doc.get("text", "")))
            for token in tokens:
                doc_freq[token] += 1
        self._idf = {
            term: math.log((num_docs + 1) / (df + 1)) + 1
            for term, df in doc_freq.items()
        }
        vocab_list = sorted(self._idf.keys())
        self._vocabulary = {term: idx for idx, term in enumerate(vocab_list)}

    def _vectorize(self, text):
        """Convert text to a TF-IDF vector."""
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)
        vector = {}
        for term, freq in tf.items():
            if term in self._idf:
                idx = self._vocabulary.get(term)
                if idx is not None:
                    vector[idx] = freq * self._idf[term]
        return vector

    def _cosine_similarity(self, vec_a, vec_b):
        """Compute cosine similarity between two sparse vectors."""
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
        mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def build_index(self, documents):
        """Build the search index from a list of document dicts with 'id' and 'text' keys."""
        self._documents = list(documents)
        self._compute_idf()
        self._doc_vectors = [self._vectorize(doc.get("text", "")) for doc in self._documents]
        self._built = True
        return {"status": "built", "num_documents": len(self._documents), "vocab_size": len(self._vocabulary)}

    def search(self, query, top_k=5):
        """Find the most relevant documents for a query."""
        if not self._built or not self._documents:
            return []
        query_vec = self._vectorize(query)
        scores = []
        for i, doc_vec in enumerate(self._doc_vectors):
            sim = self._cosine_similarity(query_vec, doc_vec)
            if sim > 0:
                scores.append((sim, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, idx in scores[:top_k]:
            doc = self._documents[idx]
            results.append({"id": doc.get("id", idx), "score": round(sim, 4), "text": doc.get("text", "")[:200]})
        return results

    def add_document(self, doc):
        """Add a single document to the index and rebuild."""
        self._documents.append(doc)
        self._compute_idf()
        self._doc_vectors = [self._vectorize(d.get("text", "")) for d in self._documents]
        self._built = True
        return {"status": "added", "num_documents": len(self._documents)}

    def get_stats(self):
        """Return index statistics."""
        return {
            "num_documents": len(self._documents),
            "vocab_size": len(self._vocabulary),
            "is_built": self._built,
            "avg_doc_length": (
                sum(len(self._tokenize(d.get("text", ""))) for d in self._documents) / len(self._documents)
                if self._documents else 0
            ),
        }
