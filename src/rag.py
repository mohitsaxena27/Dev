"""
Hybrid RAG retriever for code_analysis.md

pip install langchain-ollama langchain-chroma langchain-text-splitters rank-bm25
ollama pull nomic-embed-text   (on the same Ollama server as your LLM)
"""
import hashlib
import os
import re
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from rank_bm25 import BM25Okapi

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DB_DIR = Path("chroma_db")
HASH_FILE = DB_DIR / "source.hash"


def tokenize(text: str) -> list[str]:
    """Split camelCase / snake_case / paths so identifiers match in BM25."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return re.findall(r"[a-z0-9]+", text.lower())


def load_chunks(path: str) -> list[Document]:
    text = Path(path).read_text(encoding="utf-8")

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=False,
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150
    )

    chunks = []
    for section in header_splitter.split_text(text):
        trail = " > ".join(
            section.metadata[h] for h in ("h1", "h2", "h3") if h in section.metadata
        )
        match = re.search(r"`([^`]+)`", section.metadata.get("h2", ""))
        file_path = match.group(1) if match else ""

        for piece in size_splitter.split_text(section.page_content):
            # contextual header: every chunk knows which file/section it came from
            chunks.append(
                Document(
                    page_content=f"[{trail}]\n{piece}",
                    metadata={"file": file_path, "section": trail},
                )
            )
    return chunks


def build_store(chunks: list[Document], source_path: str) -> Chroma:
    """Persisted vector store; re-embeds only when code_analysis.md changes."""
    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=BASE_URL)
    digest = hashlib.sha256(Path(source_path).read_bytes()).hexdigest()

    up_to_date = HASH_FILE.exists() and HASH_FILE.read_text() == digest
    if not up_to_date:
        shutil.rmtree(DB_DIR, ignore_errors=True)
        store = Chroma.from_documents(
            chunks,
            embeddings,
            collection_name="analysis",
            persist_directory=str(DB_DIR),
        )
        HASH_FILE.write_text(digest)
        return store

    return Chroma(
        collection_name="analysis",
        embedding_function=embeddings,
        persist_directory=str(DB_DIR),
    )


class Retriever:
    def __init__(self, source_path: str = "code_analysis.md"):
        self.chunks = load_chunks(source_path)
        self.store = build_store(self.chunks, source_path)
        self.bm25 = BM25Okapi([tokenize(c.page_content) for c in self.chunks])

    def search(self, query: str, k: int = 6) -> list[Document]:
        # 1) semantic candidates
        vector_hits = self.store.similarity_search(query, k=20)

        # 2) keyword candidates (great for file names / function names)
        scores = self.bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:20]
        bm25_hits = [self.chunks[i] for i in top if scores[i] > 0]

        # 3) reciprocal rank fusion
        fused: dict[str, float] = {}
        docs: dict[str, Document] = {}
        for hits in (vector_hits, bm25_hits):
            for rank, doc in enumerate(hits):
                key = doc.page_content
                docs[key] = doc
                fused[key] = fused.get(key, 0) + 1 / (60 + rank)

        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [docs[key] for key in best]

    def context_for(self, query: str, k: int = 6) -> str:
        parts = []
        for doc in self.search(query, k):
            parts.append(f"### Source: {doc.metadata['section']}\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)