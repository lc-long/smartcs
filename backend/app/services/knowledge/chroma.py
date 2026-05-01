from __future__ import annotations

from typing import Optional

import chromadb
import structlog

from backend.app.core.config.settings import get_settings

logger = structlog.get_logger()

_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info("chroma_connected", path=settings.chroma_persist_dir)
    return _chroma_client


def get_or_create_collection(
    name: Optional[str] = None,
) -> chromadb.Collection:
    settings = get_settings()
    collection_name = name or settings.chroma_collection
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


class KnowledgeBase:
    """Chroma-based knowledge base for semantic search."""

    def __init__(self, collection_name: Optional[str] = None):
        self.collection = get_or_create_collection(collection_name)

    def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> None:
        if ids is None:
            import uuid

            ids = [str(uuid.uuid4()) for _ in documents]
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(
            "knowledge_documents_added",
            count=len(documents),
            collection=self.collection.name,
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
        documents = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0
            documents.append(
                {
                    "content": doc,
                    "metadata": metadata,
                    "score": 1.0 - distance,
                }
            )
        return documents

    def delete(self, ids: list[str]) -> None:
        self.collection.delete(ids=ids)

    def count(self) -> int:
        return self.collection.count()


_knowledge_base: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
