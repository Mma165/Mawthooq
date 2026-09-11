from app.rag import chunk_page


def test_chunk_page_preserves_page_and_content():
    chunks = chunk_page("Arabic legal evidence " * 100, page_number=7, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(chunk["page_number"] == 7 for chunk in chunks)
    assert all(chunk["text"] for chunk in chunks)
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_empty_page_produces_no_chunks():
    assert chunk_page("  \n\t", page_number=1) == []