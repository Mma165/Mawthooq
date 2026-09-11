import httpx

from app.config import EMBEDDING_MODEL, OLLAMA_BASE_URL


def chunk_page(text: str, page_number: int, chunk_size: int = 900, overlap: int = 120) -> list[dict[str, object]]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append({"page_number": page_number, "chunk_index": index, "text": normalized[start:end]})
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
        index += 1
    return chunks


def embed_text(text: str) -> list[float]:
    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    embedding = response.json().get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("Embedding provider returned no embedding")
    return [float(value) for value in embedding]