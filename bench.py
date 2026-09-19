from __future__ import annotations

import os
import sys
from pathlib import Path

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


def parse_markdown_with_frontmatter(content: str) -> tuple[dict, str]:
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1].strip()
            body = parts[2].strip()
            for line in raw_meta.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.split("#")[0].strip().strip("\"'")
                    metadata[key] = val
    return metadata, body


BENCHMARK_QUERIES_UNIV = [
    {
        "id": 1,
        "query": "Thời hạn mượn sách thư viện tối đa bao nhiêu ngày và được gia hạn mấy lần?",
        "filter": {"audience": "student"},
        "gold_doc": "library-services",
        "gold_answer": "Thời hạn mượn sách tiêu chuẩn cho sinh viên là 14 ngày, được gia hạn trực tuyến tối đa 2 lần (mỗi lần thêm 7 ngày).",
    },
    {
        "id": 2,
        "query": "Sinh viên được đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong một học kỳ chính?",
        "filter": None,
        "gold_doc": "course-registration",
        "gold_answer": "Trong học kỳ chính, sinh viên phải đăng ký tối thiểu 12 tín chỉ và tối đa 22 tín chỉ.",
    },
    {
        "id": 3,
        "query": "Hạn chót nộp học phí của học kỳ là khi nào và mức phạt nộp muộn là bao nhiêu?",
        "filter": None,
        "gold_doc": "tuition-payment",
        "gold_answer": "Hạn chót nộp học phí là 17h00 thứ Sáu của tuần thứ 4 tính từ ngày khai giảng; phạt nộp trễ 0.05% trên tổng số tiền chậm nộp mỗi ngày.",
    },
    {
        "id": 4,
        "query": "Tiêu chuẩn để sinh viên đạt học bổng khuyến khích học tập loại Xuất sắc là gì?",
        "filter": None,
        "gold_doc": "scholarship-policy",
        "gold_answer": "Sinh viên cần đạt điểm trung bình học kỳ (GPA) từ 3.80 trở lên và điểm rèn luyện từ 90 điểm trở lên.",
    },
    {
        "id": 5,
        "query": "Thời hạn nộp đơn phúc khảo bài thi kết thúc học phần là bao lâu và lệ phí bao nhiêu?",
        "filter": None,
        "gold_doc": "exam-regrade",
        "gold_answer": "Thời hạn nộp đơn là trong vòng 07 ngày làm việc kể từ ngày công bố điểm; lệ phí là 100.000 VNĐ/bài thi.",
    },
]


def run_benchmark(corpus_path: str = "data/university", output_path: str = "ket_qua_benchmark.txt") -> None:
    data_dir = Path(corpus_path)
    if not data_dir.exists():
        data_dir = Path("data/university")

    md_files = sorted(list(data_dir.glob("*.md")))
    print(f"=== BẮT ĐẦU BENCHMARK TRUY XUẤT (L3A: Dịch vụ & Quy định Đại học) ===")
    print(f"Thư mục corpus: {data_dir}")
    print(f"Chiến lược cá nhân của Giang: FixedSizeChunker (350, 50) + Metadata Filtering")
    print(f"Tìm thấy {len(md_files)} tài liệu:")

    chunker = FixedSizeChunker(chunk_size=350, overlap=50)
    all_chunks: list[Document] = []

    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")
        meta, body = parse_markdown_with_frontmatter(content)
        doc_id = meta.get("doc_id", file_path.stem)

        chunks = chunker.chunk(body)
        print(f"  - {file_path.name}: {len(chunks)} chunks (audience={meta.get('audience', 'all')})")

        for idx, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{idx}",
                content=chunk_text,
                metadata={
                    **meta,
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "source": str(file_path),
                },
            )
            all_chunks.append(chunk_doc)

    print(f"\nTổng số chunks tạo ra: {len(all_chunks)}")

    store = EmbeddingStore("university_benchmark_store", embedding_fn=_mock_embed)
    store.add_documents(all_chunks)
    print(f"Đã nạp {store.get_collection_size()} chunks vào EmbeddingStore")

    def mock_llm(prompt: str) -> str:
        lines = [line for line in prompt.splitlines() if line.startswith("[1]")]
        top_snippet = lines[0] if lines else "Nội dung trích xuất"
        return f"Dựa trên tài liệu quy định trích dẫn ({top_snippet[:90]}...)."

    agent = KnowledgeBaseAgent(store, llm_fn=mock_llm)

    output_lines = []
    output_lines.append("=== KẾT QUẢ BENCHMARK TRUY XUẤT (K4-L3A) ===")
    output_lines.append(f"Sinh viên: Nguyễn Xuân Trường Giang - MSSV: 2A202602446")
    output_lines.append(f"Chủ đề: Dịch vụ & Quy định Đại học (Corpus: {data_dir.name})")
    output_lines.append(f"Chiến lược: FixedSizeChunker (chunk_size=350, overlap=50) + Metadata Filter")
    output_lines.append(f"Tổng số tài liệu: {len(md_files)} | Tổng số chunks: {len(all_chunks)}\n")

    top3_success_count = 0

    for item in BENCHMARK_QUERIES_UNIV:
        qid = item["id"]
        q = item["query"]
        meta_filter = item["filter"]
        gold_doc = item["gold_doc"]
        gold_ans = item["gold_answer"]

        output_lines.append("=" * 70)
        output_lines.append(f"Câu hỏi {qid}: {q}")
        output_lines.append(f"Bộ lọc metadata: {meta_filter}")
        output_lines.append(f"Đáp án chuẩn (Gold Answer): {gold_ans}")
        output_lines.append(f"Tài liệu chuẩn (Gold Doc): {gold_doc}")

        results = store.search_with_filter(q, top_k=3, metadata_filter=meta_filter)
        output_lines.append(f"\nTop-3 Chunks truy xuất được:")

        found_in_top3 = False
        for rank, res in enumerate(results, 1):
            res_doc_id = res["metadata"].get("doc_id", "")
            res_score = res["score"]
            preview = res["content"][:100].replace("\n", " ")
            is_gold = (res_doc_id == gold_doc)
            if is_gold:
                found_in_top3 = True
            mark = "(*) [GOLD MATCH]" if is_gold else ""
            output_lines.append(f"  {rank}. [Score: {res_score:.3f}] id={res['id']} | doc_id={res_doc_id} {mark}")
            output_lines.append(f"     Nội dung: {preview}...")

        if found_in_top3:
            top3_success_count += 1
            output_lines.append(f"-> ĐÁNH GIÁ: THÀNH CÔNG (Tài liệu chuẩn nằm trong Top-3)")
        else:
            output_lines.append(f"-> ĐÁNH GIÁ: THẤT BẠI (Tài liệu chuẩn không nằm trong Top-3)")

        agent_ans = agent.answer(q, top_k=3)
        output_lines.append(f"Câu trả lời của Agent: {agent_ans}\n")

    output_lines.append("=" * 70)
    output_lines.append(f"TỔNG KẾT: {top3_success_count}/5 câu hỏi có chunk liên quan trong Top-3")

    full_output = "\n".join(output_lines)
    Path(output_path).write_text(full_output, encoding="utf-8")
    print(f"\nĐã ghi kết quả benchmark ra file: {output_path}")
    print(f"Tổng kết: {top3_success_count}/5 câu hỏi đạt chuẩn Top-3")


if __name__ == "__main__":
    corpus = sys.argv[1] if len(sys.argv) > 1 else "data/university"
    run_benchmark(corpus_path=corpus)
