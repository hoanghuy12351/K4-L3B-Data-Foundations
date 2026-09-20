from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Chia văn bản thành các đoạn có kích thước cố định và có thể chồng lấn."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size phải lớn hơn 0")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap phải nằm trong khoảng từ 0 đến chunk_size - 1")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Trả về các đoạn văn bản có độ dài không vượt quá ``chunk_size``."""
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            current_chunk = text[start : start + self.chunk_size]
            chunks.append(current_chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Chia văn bản theo ranh giới câu và gom một số câu vào mỗi đoạn."""

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        """Chia tại dấu chấm, chấm than hoặc chấm hỏi đứng trước khoảng trắng."""
        if not text or not text.strip():
            return []

        sentences = re.split(r"(?<=[.!?])(?:[ \t]+|\r?\n+)", text.strip())
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            sentence_group = sentences[start : start + self.max_sentences_per_chunk]
            chunks.append(" ".join(sentence_group))
        return chunks


class RecursiveChunker:
    """Chia đệ quy bằng cách thử các dấu phân cách theo thứ tự ưu tiên."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self, separators: list[str] | None = None, chunk_size: int = 500
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size phải lớn hơn 0")

        self.separators = (
            list(self.DEFAULT_SEPARATORS) if separators is None else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        """Trả về danh sách đoạn; văn bản rỗng tạo ra danh sách rỗng."""
        if not text or not text.strip():
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        """Chia tiếp các đoạn quá dài bằng dấu phân cách ưu tiên kế tiếp."""
        if len(current_text) <= self.chunk_size:
            cleaned_text = current_text.strip()
            return [cleaned_text] if cleaned_text else []

        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Chuỗi rỗng là phương án cuối: cắt cứng theo số ký tự.
        if separator == "":
            return self._split(current_text, [])

        # Nếu dấu hiện tại không xuất hiện, thử dấu ưu tiên tiếp theo.
        if separator not in current_text:
            return self._split(current_text, next_separators)

        raw_parts = current_text.split(separator)
        parts = [
            part + separator if index < len(raw_parts) - 1 else part
            for index, part in enumerate(raw_parts)
            if part
        ]

        chunks: list[str] = []
        buffer = ""

        for part in parts:
            if len(part) > self.chunk_size:
                if buffer.strip():
                    chunks.append(buffer.strip())
                    buffer = ""
                chunks.extend(self._split(part, next_separators))
                continue

            if not buffer or len(buffer) + len(part) <= self.chunk_size:
                buffer += part
            else:
                chunks.append(buffer.strip())
                buffer = part

        if buffer.strip():
            chunks.append(buffer.strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    """Tính tích vô hướng của hai vector."""
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Tính độ tương tự cosine; trả về 0 nếu một vector có độ dài bằng 0."""
    dot_product = _dot(vec_a, vec_b)
    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Chạy ba chiến lược chia nhỏ và tổng hợp số liệu để so sánh."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        """Trả về số đoạn, độ dài trung bình và nội dung của từng chiến lược."""
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for strategy_name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[strategy_name] = {
                "count": count,
                "avg_length": (
                    sum(len(current_chunk) for current_chunk in chunks) / count
                    if count
                    else 0.0
                ),
                "chunks": chunks,
            }

        return comparison
