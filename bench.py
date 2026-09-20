"""Run a reproducible retrieval benchmark for the ecommerce policy corpus."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from src import (
    FixedSizeChunker,
    GeminiEmbedder,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    SentenceChunker,
)
from src.chunking import ChunkingStrategyComparator
from src.models import Document
from src.store import EmbeddingStore

CORPUS_DIR = Path("data/marketplace-returns")
REQUIRED_FRONTMATTER_FIELDS = (
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
    "category",
    "language",
)

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "query": "Khi Shopee chấp nhận yêu cầu, Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau như thế nào?",
        "gold_doc_ids": ["shopee-request-processing"],
        "gold_answer": "Hoàn Tiền Ngay không yêu cầu người mua trả hàng; với Trả hàng & Hoàn tiền, người mua phải chọn phương thức trả hàng và gửi hàng về kho Shopee hoặc người bán trong vòng 6 ngày từ khi nhận thông báo.",
        "metadata_filter": {"audience": "both"},
    },
    {
        "id": "Q2",
        "query": "Shopee có hoàn phí vận chuyển ban đầu khi người mua chỉ trả lại một số sản phẩm trong đơn không?",
        "gold_doc_ids": ["shopee-return-shipping-fees"],
        "gold_answer": "Không. Phí vận chuyển ban đầu chỉ được hoàn khi yêu cầu áp dụng cho toàn bộ sản phẩm và toàn bộ giá trị đã thanh toán được hoàn; nếu chỉ trả một số sản phẩm thì phí này không được hoàn.",
        "metadata_filter": None,
    },
    {
        "id": "Q3",
        "query": "Người mua Shopee nên chuẩn bị những bằng chứng nào khi sản phẩm bị lỗi, hư hỏng hoặc khác mô tả?",
        "gold_doc_ids": ["shopee-return-evidence"],
        "gold_answer": "Người mua nên quay hoặc chụp toàn bộ kiện hàng, thông tin vận chuyển và niêm phong; video mở kiện nên liên tục và thể hiện rõ quá trình mở gói, tình trạng sản phẩm cùng lỗi, hư hỏng, thiếu hàng hoặc điểm khác mô tả.",
        "metadata_filter": {"audience": "buyer"},
    },
    {
        "id": "Q4",
        "query": "Nếu TikTok Shop đưa ra quyết định có lợi cho khách hàng trong tranh chấp hậu mãi, người bán phải thực hiện hành động khắc phục trong bao lâu?",
        "gold_doc_ids": ["tiktok-aftersales-disputes"],
        "gold_answer": "Người bán phải thực hiện biện pháp khắc phục trong vòng 48 giờ, chẳng hạn hoàn tiền hoặc thay sản phẩm, và chịu phí vận chuyển nếu có.",
        "metadata_filter": None,
    },
    {
        "id": "Q5",
        "query": "Sau khi nhân viên chăm sóc khách hàng TikTok Shop liên hệ, người bán có bao lâu và phải làm gì để gửi trả sản phẩm cho người mua?",
        "gold_doc_ids": ["tiktok-seller-to-customer-returns"],
        "gold_answer": "Người bán có 1 ngày làm việc để đóng gói an toàn, gắn nhãn vận chuyển và gửi qua đơn vị vận chuyển tiết kiệm có cung cấp mã theo dõi.",
        "metadata_filter": {"audience": "seller"},
    },
]


def parse_frontmatter(raw_text: str, source: Path) -> tuple[dict[str, str], str]:
    """Parse simple YAML-style frontmatter without adding a YAML dependency."""
    if not raw_text.startswith("---"):
        print(f"WARNING: {source}: frontmatter is missing", file=sys.stderr)
        return {}, raw_text

    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n)?", raw_text, re.DOTALL)
    if not match:
        print(
            f"WARNING: {source}: frontmatter closing delimiter is missing",
            file=sys.stderr,
        )
        return {}, raw_text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        metadata[key.strip()] = value

    missing = [
        field for field in REQUIRED_FRONTMATTER_FIELDS if not metadata.get(field)
    ]
    if missing:
        print(
            f"WARNING: {source}: missing required metadata: {', '.join(missing)}",
            file=sys.stderr,
        )
    return metadata, raw_text[match.end() :].strip()


def load_source_documents(corpus_dir: Path = CORPUS_DIR) -> list[Document]:
    """Load only source IDs declared in sources.csv, not every file in the folder."""
    source_index = corpus_dir / "sources.csv"
    if not source_index.exists():
        raise FileNotFoundError(f"Corpus index not found: {source_index}")

    documents: list[Document] = []
    seen_doc_ids: set[str] = set()
    with source_index.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            doc_id = (row.get("doc_id") or "").strip()
            if not doc_id:
                print(
                    "WARNING: sources.csv contains a row without doc_id",
                    file=sys.stderr,
                )
                continue
            if doc_id in seen_doc_ids:
                print(
                    f"WARNING: duplicate doc_id in sources.csv: {doc_id}",
                    file=sys.stderr,
                )
                continue
            seen_doc_ids.add(doc_id)

            # Resolve against the current ecommerce corpus instead of trusting
            # historical file_path values that may point at another dataset.
            path = corpus_dir / f"{doc_id}.md"
            if not path.exists():
                print(
                    f"WARNING: indexed source file is missing: {path}", file=sys.stderr
                )
                continue
            metadata, content = parse_frontmatter(
                path.read_text(encoding="utf-8"), path
            )
            metadata["doc_id"] = doc_id
            documents.append(Document(id=doc_id, content=content, metadata=metadata))
    return documents


def create_chunker(name: str):
    """Return a benchmark chunker and the parameters displayed in the report."""
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50), {
            "chunk_size": 500,
            "overlap": 50,
        }
    if name == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3), {
            "max_sentences_per_chunk": 3
        }
    return RecursiveChunker(chunk_size=500), {
        "chunk_size": 500,
        "separators": RecursiveChunker.DEFAULT_SEPARATORS,
    }


def create_embedder(name: str) -> Callable[[str], list[float]]:
    """Create only the requested backend; benchmark runs never silently downgrade."""
    if name == "mock":
        return MockEmbedder()
    load_dotenv(override=False)
    if name == "local":
        try:
            return LocalEmbedder()
        except (ImportError, ModuleNotFoundError) as exc:
            raise RuntimeError(
                "Local embeddings are unavailable. Install:\npython -m pip install -r requirements-local.txt"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Could not initialize local embeddings: {exc}") from exc
    if name == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for --embedding openai.")
        try:
            return OpenAIEmbedder()
        except Exception as exc:
            raise RuntimeError(
                f"Could not initialize OpenAI embeddings: {exc}"
            ) from exc
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is required for --embedding gemini."
        )
    try:
        return GeminiEmbedder()
    except Exception as exc:
        raise RuntimeError(f"Could not initialize Gemini embeddings: {exc}") from exc


def build_store(
    documents: list[Document], chunker: Any, embedder: Callable[[str], list[float]]
) -> tuple[EmbeddingStore, int]:
    """Chunk source documents outside the store, then add one record per chunk."""
    chunks: list[Document] = []
    for source_document in documents:
        for chunk_index, content in enumerate(chunker.chunk(source_document.content)):
            chunks.append(
                Document(
                    id=f"{source_document.id}#{chunk_index}",
                    content=content,
                    metadata={
                        **source_document.metadata,
                        "doc_id": source_document.id,
                        "chunk_index": chunk_index,
                    },
                )
            )
    store = EmbeddingStore(collection_name="ecommerce_benchmark", embedding_fn=embedder)
    store.add_documents(chunks)
    return store, len(chunks)


def gold_rank(results: list[dict[str, Any]], gold_doc_ids: list[str]) -> int | None:
    """Return the first one-based rank whose source document is a gold document."""
    gold_ids = set(gold_doc_ids)
    for index, result in enumerate(results, start=1):
        if result["metadata"].get("doc_id") in gold_ids:
            return index
    return None


def answer_keyword_match(
    gold_answer: str, results: list[dict[str, Any]]
) -> tuple[bool, list[str]]:
    """Provide a lightweight clue check without claiming to score answer quality."""
    tokens = re.findall(r"\w+", gold_answer.casefold(), flags=re.UNICODE)
    useful_tokens = sorted({token for token in tokens if len(token) >= 4})
    context = " ".join(result["content"] for result in results).casefold()
    matched = [token for token in useful_tokens if token in context]
    return bool(matched), matched


def preview(text: str, length: int = 300) -> str:
    """Make a single-line, bounded preview for a readable text report."""
    flat = " ".join(text.split())
    return flat if len(flat) <= length else f"{flat[:length - 3]}..."


def append_results(lines: list[str], results: list[dict[str, Any]]) -> None:
    """Append complete retrieval details for each returned top-k result."""
    if not results:
        lines.append("No results.")
        return
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        lines.extend(
            [
                f"TOP {rank}",
                f"rank: {rank}",
                f"score: {result['score']:.6f}",
                f"doc_id: {metadata.get('doc_id', '')}",
                f"title: {metadata.get('title', '')}",
                f"audience: {metadata.get('audience', '')}",
                f"category: {metadata.get('category', '')}",
                f"chunk_index: {metadata.get('chunk_index', '')}",
                f"content preview: {preview(result['content'])}",
                "",
            ]
        )


def compare_chunkers(documents: list[Document], lines: list[str]) -> None:
    """Report baseline chunk counts and average lengths for representative sources."""
    representative_ids = {
        "shopee-return-refund-policy",
        "shopee-return-evidence",
        "tiktok-aftersales-disputes",
    }
    comparator = ChunkingStrategyComparator()
    lines.extend(
        ["BASELINE CHUNKING COMPARISON", "document | strategy | count | avg_length"]
    )
    for document in documents:
        if document.id not in representative_ids:
            continue
        comparison = comparator.compare(document.content, chunk_size=500)
        for strategy, stats in comparison.items():
            lines.append(
                f"{document.id} | {strategy} | {stats['count']} | {stats['avg_length']:.2f}"
            )
    lines.append("")


def run_benchmark(args: argparse.Namespace) -> list[str]:
    """Run retrieval, metadata A/B checks, and the document-level summary."""
    documents = load_source_documents()
    if not documents:
        raise RuntimeError("No indexed ecommerce documents could be loaded.")
    chunker, chunker_parameters = create_chunker(args.chunker)
    embedder = create_embedder(args.embedding)
    store, chunk_count = build_store(documents, chunker, embedder)
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    lines = [
        "Ecommerce retrieval benchmark",
        f"timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"embedding backend: {args.embedding} ({backend_name})",
        f"chunker: {args.chunker}",
        f"parameters: {chunker_parameters}",
        f"number of source documents: {len(documents)}",
        f"number of chunks: {chunk_count}",
        f"top_k: {args.top_k}",
        "",
    ]
    if args.compare_chunkers:
        compare_chunkers(documents, lines)

    gold_at_1 = 0
    gold_at_3 = 0
    total_document_score = 0
    for specification in BENCHMARK_QUERIES:
        results = store.search_with_filter(
            query=specification["query"],
            top_k=args.top_k,
            metadata_filter=specification["metadata_filter"],
        )
        rank = gold_rank(results, specification["gold_doc_ids"])
        document_score = 2 if rank == 1 else 1 if rank in {2, 3} else 0
        total_document_score += document_score
        gold_at_1 += rank == 1
        gold_at_3 += rank is not None and rank <= 3
        clue_found, matched_keywords = answer_keyword_match(
            specification["gold_answer"], results
        )

        lines.extend(
            [
                f"QUERY {specification['id']}",
                f"query: {specification['query']}",
                f"Gold answer: {specification['gold_answer']}",
                f"Gold document: {', '.join(specification['gold_doc_ids'])}",
                f"Metadata filter: {specification['metadata_filter']}",
                "",
            ]
        )
        append_results(lines, results)
        lines.extend(
            [
                f"gold rank: {rank if rank is not None else 'not found'}",
                f"document_retrieval_score: {document_score}",
                f"gold answer keyword clue found: {clue_found}",
                f"matched keywords: {', '.join(matched_keywords) if matched_keywords else 'none'}",
                "",
            ]
        )

        if specification["metadata_filter"] is not None:
            unfiltered = store.search(specification["query"], top_k=args.top_k)
            filtered = results
            lines.extend(
                [
                    "A/B METADATA FILTER COMPARISON",
                    "Unfiltered top-3:",
                ]
            )
            append_results(lines, unfiltered)
            lines.append("Filtered top-3:")
            append_results(lines, filtered)
            lines.extend(
                [
                    f"Gold rank before: {gold_rank(unfiltered, specification['gold_doc_ids']) or 'not found'}",
                    f"Gold rank after: {gold_rank(filtered, specification['gold_doc_ids']) or 'not found'}",
                    "",
                ]
            )

    lines.extend(
        [
            "SUMMARY",
            f"Questions: {len(BENCHMARK_QUERIES)}",
            f"Gold@1: {gold_at_1}/{len(BENCHMARK_QUERIES)}",
            f"Gold@3: {gold_at_3}/{len(BENCHMARK_QUERIES)}",
            f"Document retrieval score: {total_document_score}/{len(BENCHMARK_QUERIES) * 2}",
            "Document retrieval score is a retrieval-only metric, not the final lab score.",
        ]
    )
    return lines


def parse_args() -> argparse.Namespace:
    """Build a concise command-line interface for repeatable benchmark runs."""
    parser = argparse.ArgumentParser(
        description="Benchmark ecommerce-policy document retrieval."
    )
    parser.add_argument(
        "--chunker", choices=("recursive", "fixed", "sentence"), default="recursive"
    )
    parser.add_argument(
        "--embedding", choices=("mock", "local", "openai", "gemini"), default="local"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of chunks to retrieve per query (default: 3).",
    )
    parser.add_argument("--output", type=Path, default=Path("ket_qua_benchmark.txt"))
    parser.add_argument(
        "--compare-chunkers",
        action="store_true",
        help="Include baseline chunking statistics for three representative documents.",
    )
    return parser.parse_args()


def main() -> int:
    """Write the requested benchmark output and echo it to the terminal."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    args = parse_args()
    if args.top_k <= 0:
        print("Error: --top-k must be a positive integer.", file=sys.stderr)
        return 2
    try:
        lines = run_benchmark(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report = "\n".join(lines) + "\n"
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Benchmark report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
