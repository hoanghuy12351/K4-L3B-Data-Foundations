from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Tác tử trả lời câu hỏi dựa trên tri thức được truy xuất từ kho vector."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """Truy xuất ngữ cảnh, tạo câu lệnh và gọi mô hình ngôn ngữ."""
        search_results = self.store.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[Ngữ cảnh {index}]\n{result['content']}"
            for index, result in enumerate(search_results, start=1)
        )
        if not context:
            context = "Không tìm thấy ngữ cảnh phù hợp trong kho tri thức."

        prompt = (
            "Hãy trả lời câu hỏi chỉ dựa trên ngữ cảnh được cung cấp. "
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ điều đó.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
