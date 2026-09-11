import hashlib
import json
from pathlib import Path

import pytest

from app.extraction import ExtractedPage, ExtractionResult
from app.legal_ingestion import LegalSourceIngestionError, ingest_sources, load_approved_sources


def _write_corpus(tmp_path: Path, *, local_path: str = "data/rag/sources/source.pdf") -> tuple[Path, Path]:
    pdf_path = tmp_path / "data" / "rag" / "sources" / "source.pdf"
    pdf_path.parent.mkdir(parents=True)
    content = b"%PDF-1.7\nlegal source"
    pdf_path.write_bytes(content)
    source = {
        "source_id": "official-source", "title": "Official source", "url": "https://example.test/source.pdf",
        "publisher": "Authority", "source_type": "binding_law", "jurisdiction": "Saudi Arabia",
        "language": "ar", "case_categories": ["contract"], "download": True,
    }
    manifest = [{**source, "local_path": local_path, "sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}]
    registry_path = tmp_path / "rag_sources.json"
    manifest_path = tmp_path / "download_manifest.json"
    registry_path.write_text(json.dumps([source]), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return registry_path, manifest_path


def test_load_approved_sources_validates_manifest_and_resolves_windows_path(tmp_path):
    registry_path, manifest_path = _write_corpus(tmp_path, local_path="data\\rag\\sources\\source.pdf")

    sources = load_approved_sources(registry_path, manifest_path, tmp_path)

    assert sources[0]["source_id"] == "official-source"
    assert sources[0]["path"] == tmp_path / "data" / "rag" / "sources" / "source.pdf"


def test_load_approved_sources_rejects_hash_mismatch(tmp_path):
    registry_path, manifest_path = _write_corpus(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[0]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(LegalSourceIngestionError, match="hash"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_ingestion_skips_unchanged_source(tmp_path, monkeypatch):
    registry_path, manifest_path = _write_corpus(tmp_path)
    from app import legal_ingestion

    source = load_approved_sources(registry_path, manifest_path, tmp_path)[0]
    monkeypatch.setattr(legal_ingestion.repositories, "get_legal_source_sha256", lambda _: source["sha256"])
    monkeypatch.setattr(legal_ingestion.repositories, "replace_legal_source", lambda *_: pytest.fail("should not replace"))

    assert ingest_sources(registry_path, manifest_path, tmp_path) == [
        {"source_id": "official-source", "status": "skipped", "chunk_count": 0}
    ]


def test_ingestion_replaces_changed_source_with_page_provenance(tmp_path, monkeypatch):
    registry_path, manifest_path = _write_corpus(tmp_path)
    from app import legal_ingestion

    stored = {}
    monkeypatch.setattr(legal_ingestion.repositories, "get_legal_source_sha256", lambda _: "old-hash")
    monkeypatch.setattr(legal_ingestion, "extract_document", lambda *_: ExtractionResult(
        pages=[ExtractedPage(3, "Approved legal evidence " * 60, "en", "text_layer", "usable")], status="ready", review_reasons=[]
    ))
    monkeypatch.setattr(legal_ingestion.repositories, "replace_legal_source", lambda source, pages, chunks: stored.update(source=source, pages=pages, chunks=chunks))

    result = ingest_sources(registry_path, manifest_path, tmp_path, embedder=lambda _: [0.1, 0.2])

    assert result[0]["status"] == "indexed"
    assert stored["pages"][0]["page_number"] == 3
    assert stored["chunks"][0]["page_number"] == 3
    assert stored["chunks"][0]["embedding"] == [0.1, 0.2]


def test_load_approved_sources_rejects_source_missing_from_manifest(tmp_path):
    registry_path, manifest_path = _write_corpus(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[0]["source_id"] = "some-other-source"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(LegalSourceIngestionError, match="missing from the manifest"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_load_approved_sources_rejects_missing_registry_metadata(tmp_path):
    registry_path, manifest_path = _write_corpus(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    del registry[0]["jurisdiction"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(LegalSourceIngestionError, match="missing required registry metadata"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_load_approved_sources_rejects_non_pdf_content(tmp_path):
    registry_path, manifest_path = _write_corpus(
        tmp_path,
        local_path="data/rag/sources/source.pdf",
    )
    content = b"this is not a pdf"
    (tmp_path / "data" / "rag" / "sources" / "source.pdf").write_bytes(content)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[0]["sha256"] = hashlib.sha256(content).hexdigest()
    manifest[0]["size_bytes"] = len(content)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(LegalSourceIngestionError, match="not the recorded PDF"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_load_approved_sources_rejects_missing_pdf_file(tmp_path):
    registry_path, manifest_path = _write_corpus(
        tmp_path,
        local_path="data/rag/sources/does-not-exist.pdf",
    )

    with pytest.raises(LegalSourceIngestionError, match="Downloaded PDF is missing"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_load_approved_sources_rejects_invalid_case_categories(tmp_path):
    registry_path, manifest_path = _write_corpus(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry[0]["case_categories"] = "contract"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(LegalSourceIngestionError, match="invalid case_categories"):
        load_approved_sources(registry_path, manifest_path, tmp_path)


def test_ingest_sources_rejects_source_without_usable_text(tmp_path, monkeypatch):
    registry_path, manifest_path = _write_corpus(tmp_path)
    from app import legal_ingestion

    monkeypatch.setattr(legal_ingestion.repositories, "get_legal_source_sha256", lambda _: None)
    monkeypatch.setattr(legal_ingestion, "extract_document", lambda *_: ExtractionResult(
        pages=[ExtractedPage(1, "  \n  ", "unknown", "text_layer", "poor")], status="needs_review", review_reasons=[]
    ))

    with pytest.raises(LegalSourceIngestionError, match="no usable text"):
        ingest_sources(registry_path, manifest_path, tmp_path, embedder=lambda _: [0.1, 0.2])
