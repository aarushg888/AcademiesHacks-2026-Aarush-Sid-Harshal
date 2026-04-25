import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INVESTORS = ["buffett", "munger", "dalio", "lynch"]

# In-memory store: {investor: [chunks]}
_store: dict[str, list[str]] = {}


def _load(investor: str) -> list[str]:
    if investor in _store:
        return _store[investor]
    path = os.path.join(DATA_DIR, f"{investor}.txt")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [c.strip() for c in text.strip().split("\n\n") if c.strip()]
    _store[investor] = chunks
    return chunks


def ingest_investor(investor: str, text: str) -> int:
    chunks = [c.strip() for c in text.strip().split("\n\n") if c.strip()]
    _store[investor] = chunks
    return len(chunks)


def retrieve(investor: str, query: str, n: int = 8) -> list[str]:
    """Keyword-overlap retrieval — best effort without embeddings."""
    chunks = _load(investor)
    if not chunks:
        return []
    query_words = set(query.lower().split())

    def score(chunk: str) -> int:
        chunk_words = set(chunk.lower().split())
        return len(query_words & chunk_words)

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked[:n]


def is_ingested(investor: str) -> bool:
    return len(_load(investor)) > 0


def get_dna_chunks(investor: str) -> list[str]:
    return _load(investor)