"""Explicit ingestion of approved, downloaded legal-source PDFs."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Callable

from app import repositories
from app.extraction import PDF_MIME, extract_document
from app.rag import chunk_page, embed_text


class LegalSourceIngestionError(ValueError):
    """Raised when the approved corpus or its provenance is invalid."""


def load_approved_sources(
    registry_path: Path, manifest_path: Path, repo_root: Path | None = None
) -> list[dict[str, object]]:
    """Join explicitly downloadable registry entries to their verified downloads."""
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LegalSourceIngestionError("Could not read the source registry or download manifest.") from error
    if not isinstance(registry, list) or not isinstance(manifest, list):
        raise LegalSourceIngestionError("The source registry and download manifest must be JSON lists.")

    manifest_by_id = {
        item.get("source_id"): item for item in manifest if isinstance(item, dict) and item.get("source_id")
    }
    root = repo_root or registry_path.parent.parent
    approved = []
    for source in registry:
        if not isinstance(source, dict) or not source.get("download"):
            continue
        source_id = source.get("source_id")
        required = ("source_id", "title", "url", "publisher", "source_type", "jurisdiction", "language", "case_categories")
        if not source_id or any(not source.get(field) for field in required):
            raise LegalSourceIngestionError("A downloadable source is missing required registry metadata.")
        if not isinstance(source["case_categories"], list):
            raise LegalSourceIngestionError(f"{source_id} has invalid case_categories metadata.")
        downloaded = manifest_by_id.get(source_id)
        if downloaded is None:
            raise LegalSourceIngestionError(f"{source_id} is approved for download but missing from the manifest.")
        if not downloaded.get("local_path") or not downloaded.get("sha256") or not downloaded.get("size_bytes"):
            raise LegalSourceIngestionError(f"{source_id} has incomplete download provenance.")
        relative_path = Path(str(downloaded["local_path"]).replace("\\", "/"))
        path = relative_path if relative_path.is_absolute() else root / relative_path
        if not path.is_file():
            raise LegalSourceIngestionError(f"Downloaded PDF is missing for {source_id}: {path}")
        content = path.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != downloaded["sha256"]:
            raise LegalSourceIngestionError(f"Downloaded PDF hash does not match the manifest for {source_id}.")
        if len(content) != downloaded["size_bytes"] or not content.startswith(b"%PDF-"):
            raise LegalSourceIngestionError(f"Downloaded file is not the recorded PDF for {source_id}.")
        approved.append({**source, **downloaded, "path": path, "sha256": actual_hash})
    return approved


def ingest_sources(
    registry_path: Path,
    manifest_path: Path,
    repo_root: Path | None = None,
    embedder: Callable[[str], list[float]] = embed_text,
) -> list[dict[str, object]]:
    """Index changed approved sources and skip records matching their manifest hash."""
    results = []
    for source in load_approved_sources(registry_path, manifest_path, repo_root):
        source_id = str(source["source_id"])
        if repositories.get_legal_source_sha256(source_id) == source["sha256"]:
            results.append({"source_id": source_id, "status": "skipped", "chunk_count": 0})
            continue
        extraction = extract_document(Path(source["path"]), PDF_MIME)
        pages = [
            {
                "page_number": page.page_number,
                "text": page.text,
                "language": page.language,
                "extraction_method": page.extraction_method,
                "quality": page.quality,
            }
            for page in extraction.pages
        ]
        chunks = []
        for page in pages:
            for chunk in chunk_page(str(page["text"]), int(page["page_number"])):
                chunk["embedding"] = embedder(str(chunk["text"]))
                chunks.append(chunk)
        if not chunks:
            raise LegalSourceIngestionError(f"{source_id} has no usable text to index.")
        repositories.replace_legal_source(source, pages, chunks)
        results.append({"source_id": source_id, "status": "indexed", "chunk_count": len(chunks)})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("/project/ai/rag_sources.json"))
    parser.add_argument("--manifest", type=Path, default=Path("/project/data/rag/sources/download_manifest.json"))
    parser.add_argument("--repo-root", type=Path, default=Path("/project"))
    args = parser.parse_args()
    results = ingest_sources(args.registry, args.manifest, args.repo_root)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
