"""Download explicitly approved official RAG sources and preserve provenance."""

import argparse
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "rag_sources.json"
DEFAULT_OUTPUT = ROOT.parent / "data" / "rag" / "sources"


def download_sources(output_dir: Path, manifest_path: Path = MANIFEST_PATH) -> list[dict[str, object]]:
    sources = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for source in sources:
        if not source.get("download"):
            continue
        source_id = source["source_id"]
        target = output_dir / f"{source_id}.pdf"
        if target.exists():
            content = target.read_bytes()
        else:
            request = Request(source["url"], headers={"User-Agent": "Mawthooq-RAG-Downloader/0.1"})
            with urlopen(request, timeout=30) as response:
                content = response.read()
            target.write_bytes(content)
        if not content.startswith(b"%PDF"):
            raise ValueError(f"{source_id} did not return a PDF")
        results.append({
            **source,
            "local_path": str(target.relative_to(ROOT.parent)),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        })
    (output_dir / "download_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    downloaded = download_sources(args.output)
    print(f"Downloaded {len(downloaded)} source(s) to {args.output}")
    for source in downloaded:
        print(f"- {source['source_id']}: {source['size_bytes']} bytes")
