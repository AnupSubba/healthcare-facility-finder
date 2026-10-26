"""Build the glossary index (data/chroma/) from the cards in knowledge/. Commit the result.

uv run python scripts/ingest_glossary.py
"""

import shutil
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from facility_finder import config  # noqa: E402


def read_card(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    _, header, body = text.split("---", 2)
    meta = dict(line.split(":", 1) for line in header.strip().splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    content = f"# {meta['title']}\nTerms: {meta.get('term', '')}\n\n{body.strip()}"
    return Document(page_content=content, metadata={"url": meta["source"], "title": meta["title"], "file": path.name})


def main() -> None:
    cards = [read_card(p) for p in sorted((ROOT / "knowledge").glob("*.md"))]
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
    Chroma.from_documents(
        cards,
        FastEmbedEmbeddings(model_name=config.EMBED_MODEL),
        persist_directory=str(config.CHROMA_DIR),
        collection_name=config.COLLECTION,
    )
    print(f"{len(cards)} glossary cards indexed in {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
