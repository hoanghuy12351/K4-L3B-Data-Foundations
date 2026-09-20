from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """Kho vector cho văn bản, có thể dùng ChromaDB hoặc bộ nhớ trong."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._client = None
        self._next_index = 0

        try:
            import chromadb

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=collection_name
            )
            self._use_chroma = True
        except Exception:
            # ChromaDB là tùy chọn; bộ nhớ trong luôn sẵn sàng để dự phòng.
            self._use_chroma = False
            self._collection = None
            self._client = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuẩn hóa một tài liệu thành bản ghi có mã, nội dung và vector."""
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}-{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Tính điểm cho các bản ghi và trả về kết quả tốt nhất trước."""
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Nhúng nội dung và thêm từng tài liệu vào kho."""
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        # Giữ bản ghi chuẩn hóa để tìm kiếm và lọc nhất quán giữa các backend.
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                )
            except Exception:
                # Nếu backend ngoài gặp lỗi, dữ liệu vẫn dùng được từ bộ nhớ trong.
                self._use_chroma = False
                self._collection = None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Tìm các tài liệu có tích vô hướng lớn nhất với truy vấn."""
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Trả về tổng số đoạn đang được lưu."""
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Lọc theo siêu dữ liệu trước, sau đó xếp hạng theo độ tương tự."""
        if not metadata_filter:
            return self.search(query, top_k)

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == expected_value
                for key, expected_value in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """Xóa mọi đoạn thuộc tài liệu và báo có tìm thấy dữ liệu để xóa hay không."""
        original_size = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        removed = len(self._store) < original_size

        if removed and self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                self._use_chroma = False
                self._collection = None

        return removed
