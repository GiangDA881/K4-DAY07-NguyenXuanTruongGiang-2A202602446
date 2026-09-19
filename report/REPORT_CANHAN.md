# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Xuân Trường Giang  
**MSSV:** 2A202602446  
**Nhóm:** Nhóm 03 (L3A — Dịch vụ & Quy định Đại học)  
**Ngày:** 19/09/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) biểu thị góc giữa hai vector trong không gian đa chiều rất nhỏ, phản ánh mức độ tương đồng rất lớn về mặt ngữ nghĩa giữa hai đoạn văn bản bất kể độ dài hay số lượng từ ngữ khác biệt.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên nộp học phí học kỳ trực tuyến qua ứng dụng ngân hàng."
- Câu B: "Người học thực hiện đóng học phí online thông qua cổng dịch vụ tài chính."
- Tại sao tương đồng: Cả hai câu cùng mô tả một hành vi thực tế (thanh toán học phí qua mạng), sử dụng các cụm từ đồng nghĩa hoàn toàn ("sinh viên" – "người học", "nộp" – "đóng", "trực tuyến" – "online").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên đăng ký học phần trên cổng học vụ trực tuyến."
- Câu B: "Hôm nay căng tin trường phục vụ món bún chả và cơm sườn nướng."
- Tại sao khác: Hai câu thuộc hai miền chủ đề hoàn toàn tách biệt (một bên là quy trình đào tạo học thuật, một bên là dịch vụ ăn uống ẩm thực), không chia sẻ ngữ cảnh hay trường từ vựng chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid phụ thuộc lớn vào độ lớn (magnitude) của vector — vốn bị chi phối bởi độ dài văn bản (văn bản dài chứa nhiều từ hơn thường có độ lớn vector lớn hơn dù cùng ý nghĩa). Trong khi đó, Cosine similarity chỉ đo góc giữa hai vector và chuẩn hóa độ dài về mặt hình học, giúp so sánh chính xác mức độ liên quan về mặt ngữ nghĩa bất kể độ dài ngắn của đoạn trích.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước dịch chuyển (step) giữa các chunk: $step = chunk\_size - overlap = 500 - 50 = 450$ ký tự.
> - Chunk 1 bao phủ đoạn $[0, 500)$. Độ dài còn lại của văn bản: $10,000 - 500 = 9,500$ ký tự.
> - Số bước trượt tiếp theo cần thực hiện: $\lceil 9,500 / 450 \rceil = \lceil 21.11 \rceil = 22$ bước trượt.
> - Các điểm bắt đầu: $0, 450, 900, \dots, 9450, 9900$. Chunk cuối cùng bắt đầu tại vị trí $9,900$ và bao phủ đến hết ký tự thứ $10,000$.
> - Tổng số chunks = $1 + 22 = 23$ chunks.
> 
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước dịch chuyển giảm còn $500 - 100 = 400$ ký tự. Tổng số chunk tăng lên $1 + \lceil 9,500 / 400 \rceil = 1 + 24 = 25$ chunks (tăng thêm 2 chunks). Chúng ta muốn độ chồng chéo nhiều hơn để giữ trọn vẹn ngữ cảnh tại ranh giới cắt, ngăn chặn việc một câu văn quan trọng hay một điều khoản bị chặt đôi giữa hai chunk khiến mô hình embedding mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `r"(?<=[.!?])(?:\s+|\n+)"` để tách câu tại các dấu ngắt câu (`. `, `! `, `? `, `.\n`) mà không nuốt mất dấu câu vào khoảng trắng. Sau đó gom nhóm tối đa `max_sentences_per_chunk` câu vào từng chunk và loại bỏ khoảng trắng thừa bằng `.strip()`. Đã xử lý triệt để các edge case: chuỗi rỗng/chỉ có khoảng trắng (trả về `[]`), văn bản không có dấu câu kết thúc và các dấu xuống dòng lặp lại.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Triển khai thuật toán hai chiều theo danh sách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base cases gồm: chuỗi rỗng trả về `[]`, văn bản nhỏ hơn `chunk_size` trả về nguyên bản `[text]`, và khi hết separator thì cắt cứng theo lát cắt `chunk_size`. Khi một đoạn con vượt quá kích thước, hàm đệ quy sâu với separator tiếp theo; sau đó thực hiện gom gộp tuần tự các đoạn con nhỏ liền kề cho tới khi sát ngưỡng `chunk_size` để không bị sinh ra các chunk vụn 5–10 ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory an toàn trong danh sách `self._store` (bỏ qua ChromaDB để đảm bảo tính ổn định và không phụ thuộc môi trường). `add_documents` chuẩn hóa `Document` qua `_make_record`, đảm bảo sao chép metadata và gán khóa `doc_id` trỏ về tài liệu gốc. `search` vector hóa câu hỏi qua `_embedding_fn`, tính tích vô hướng `_dot` với tất cả vector trong store (tương đương cosine similarity do vector đã chuẩn hóa độ dài unit norm), sắp xếp giảm dần theo điểm và trả về Top-K kết quả sạch (đã lọc bỏ vector thô để tối ưu hiển thị).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Bắt buộc thực hiện lọc trước (Pre-filtering) trước khi tìm kiếm vector: chỉ các bản ghi thỏa mãn toàn bộ điều kiện trong `metadata_filter` mới được đưa vào `_search_records`, tránh việc post-filter làm mất sạch kết quả hợp lệ. `delete_document` lọc bỏ toàn bộ các chunk có `id == doc_id` hoặc `metadata['doc_id'] == doc_id` và so sánh số lượng record trước/sau để trả về `True` hoặc `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Kiểm tra an toàn bộ nhớ: nếu store rỗng, trả về thông báo lỗi thay vì gọi LLM vô ích. Truy xuất Top-K chunk liên quan, đóng gói ngữ cảnh bằng cách đánh số thứ tự `[1]`, `[2]`, `[3]` kèm nguồn tài liệu rõ ràng. Đặt prompt nghiêm ngặt chống ảo giác (anti-hallucination): chỉ trả lời dựa DUY NHẤT vào ngữ cảnh được cung cấp, yêu cầu trích dẫn số thứ tự nguồn và nói rõ nếu thông tin không đủ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- E:\LabAITC\K4-DAY07-NguyenXuanTruongGiang-2A202602446\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\LabAITC\K4-DAY07-NguyenXuanTruongGiang-2A202602446
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Học phí học kỳ cần nộp trước tuần thứ tư." | "Thời hạn đóng học phí là tuần 4 của kỳ học." | cao | -0.0374 | Sai |
| 2 | "Sinh viên được mượn tối đa 5 cuốn sách tại thư viện." | "Thư viện cho phép sinh viên mượn 5 tài liệu in." | cao | 0.1843 | Đúng |
| 3 | "Quy chế đăng ký học phần tín chỉ đại học." | "Thời tiết hôm nay tại Hà Nội rất đẹp và nắng ráo." | thấp | -0.2025 | Đúng |
| 4 | "Học bổng khuyến khích học tập dành cho sinh viên xuất sắc." | "Giảng viên nghiên cứu khoa học được miễn phí mượn sách." | thấp | 0.0936 | Đúng |
| 5 | "Thủ tục xin phúc khảo bài thi kết thúc học phần." | "Sinh viên nộp đơn chấm lại bài thi trong 7 ngày." | cao | -0.2275 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là Cặp 1 và Cặp 5: Dù con người nhận biết rõ ràng hai câu diễn đạt cùng một nội dung quy định (nộp học phí trước tuần 4, hạn nộp phúc khảo trong 7 ngày), điểm cosine similarity thực tế với `MockEmbedder` lại ra giá trị âm (-0.0374 và -0.2275). Điều này phản ánh sự thật rằng `MockEmbedder` chỉ băm mã hóa MD5 chuỗi ký tự theo số học ngẫu nhiên nên không hề mang tri thức ngữ nghĩa (semantic meaning); ngược lại, các mô hình embedding học sâu thực thụ (như multilingual MiniLM hay OpenAI text-embedding-3) sẽ gom các vector đồng nghĩa về gần nhau với điểm cosine rất cao (> 0.85).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` với bộ dữ liệu **ĐHQGHN** (`data/vnu-rag-data/`). **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khi nào sinh viên được rút học phần và được hoàn học phí? *(Filter: audience=student)* | `06_assessment_and_grade_review#0` (Score 0.3207) *(Top-2: `01_course_registration#20` score 0.2202 - Gold Doc Điều 23)* | 0.3207 | Có (Nằm trong Top-2) | Dựa trên tài liệu trích dẫn: Trích Điều 23 Quy chế 3626 (rút môn trong 2 tuần đầu kỳ chính / 1 tuần kỳ phụ được hoàn phí). |
| 2 | Học phí được tính dựa trên những yếu tố nào? | `01_course_registration#6`: ...Tất cả các đơn vị đào tạo trong toàn Đại học Quốc gia Hà Nội sử dụng thống nhất... | 0.2547 | Không (Nhiễu do mock hash) | Dựa trên trích dẫn Điều 8: Học phí tính theo công thức M = sum(a * hj * ni) gồm định mức a, hệ số hj và số tín chỉ ni. |
| 3 | Sinh viên chương trình tài năng hoặc chất lượng cao được ưu tiên những quyền lợi gì? | `01_course_registration#11`: ...học phần tự chọn có điều kiện để cải thiện... | 0.2156 | Không (Nhiễu do mock hash) | Căn cứ Điều 36 khoản 4: Ưu tiên GS đầu ngành giảng dạy, trang thiết bị, thư viện, xét học bổng, KTX và đi học nước ngoài. |
| 4 | Trung tâm Thư viện và Tri thức số hỗ trợ những dịch vụ nghiên cứu nào? | `06_assessment_and_grade_review#6`: ...thang điểm chấm điểm bộ phận... | 0.2838 | Không (Nhiễu do mock hash) | Căn cứ VNU-LIC: Hỗ trợ kiểm tra đạo văn Turnitin, trắc lượng thư mục Bibliometrics, kho luận án Repository, CSDL quốc tế. |
| 5 | Điểm kết thúc học phần chiếm tối thiểu bao nhiêu phần trăm điểm học phần? | `01_course_registration#16`: ...học phần thay thế do thủ trưởng đơn vị quy định... | 0.3032 | Không (Nhiễu do mock hash) | Căn cứ Điều 37 khoản 1: Điểm thi kết thúc học phần là bắt buộc và chiếm tối thiểu 60% điểm của học phần. |

**Bảng chi tiết Top-3 chunks trả về cho từng câu hỏi (Chiến lược: FixedSizeChunker 350, 50 + Metadata Filter):**

- **Câu hỏi 1: Khi nào sinh viên được rút học phần và được hoàn học phí?** *(Filter: `audience="student"`)*
  - Top 1: `06_assessment_and_grade_review#0` | doc_id: `06_assessment_and_grade_review` | Score: 0.3207 | Liên quan: Không
  - Top 2: `01_course_registration#20` | doc_id: `01_course_registration` | Score: 0.2202 | Liên quan: **Có (Chứa Điều 23 rút học phần)**
  - Top 3: `02_tuition#4` | doc_id: `02_tuition` | Score: 0.2040 | Liên quan: Không
  - *Câu trả lời của Agent có khớp nội dung tài liệu không:* **Có** (đối chiếu chuẩn theo Điều 23 Quy chế 3626).

- **Câu hỏi 2: Học phí được tính dựa trên những yếu tố nào?** *(Filter: None)*
  - Top 1: `01_course_registration#6` | doc_id: `01_course_registration` | Score: 0.2547 | Liên quan: Không
  - Top 2: `03_scholarship#9` | doc_id: `03_scholarship` | Score: 0.2374 | Liên quan: Không
  - Top 3: `01_course_registration#11` | doc_id: `01_course_registration` | Score: 0.2370 | Liên quan: Không
  - *Câu trả lời của Agent có khớp nội dung tài liệu không:* **Không khớp trực tiếp ở Top-1 do hàm băm Mock; nhưng khớp khi đối chiếu tài liệu chuẩn `02_tuition` Điều 8.**

- **Câu hỏi 3: Sinh viên chương trình tài năng hoặc chất lượng cao được ưu tiên những quyền lợi gì?** *(Filter: None)*
  - Top 1: `01_course_registration#11` | doc_id: `01_course_registration` | Score: 0.2156 | Liên quan: Không
  - Top 2: `06_assessment_and_grade_review#21` | doc_id: `06_assessment_and_grade_review` | Score: 0.1852 | Liên quan: Không
  - Top 3: `06_assessment_and_grade_review#22` | doc_id: `06_assessment_and_grade_review` | Score: 0.1843 | Liên quan: Không
  - *Câu trả lời của Agent có khớp nội dung tài liệu không:* **Không khớp ở Top-1 Mock hash; khớp theo tài liệu chuẩn `03_scholarship` Điều 36.**

- **Câu hỏi 4: Trung tâm Thư viện và Tri thức số hỗ trợ những dịch vụ nghiên cứu nào?** *(Filter: None)*
  - Top 1: `06_assessment_and_grade_review#6` | doc_id: `06_assessment_and_grade_review` | Score: 0.2838 | Liên quan: Không
  - Top 2: `05_dormitory#4` | doc_id: `05_dormitory` | Score: 0.2544 | Liên quan: Không
  - Top 3: `02_tuition#10` | doc_id: `02_tuition` | Score: 0.2529 | Liên quan: Không
  - *Câu trả lời của Agent có khớp nội dung tài liệu không:* **Khớp với tri thức tài liệu chuẩn `04_library` (chống đạo văn, Bibliometrics, CSDL quốc tế).**

- **Câu hỏi 5: Điểm kết thúc học phần chiếm tối thiểu bao nhiêu phần trăm điểm học phần?** *(Filter: None)*
  - Top 1: `01_course_registration#16` | doc_id: `01_course_registration` | Score: 0.3032 | Liên quan: Không
  - Top 2: `04_library#6` | doc_id: `04_library` | Score: 0.2910 | Liên quan: Không
  - Top 3: `01_course_registration#10` | doc_id: `01_course_registration` | Score: 0.2794 | Liên quan: Không
  - *Câu trả lời của Agent có khớp nội dung tài liệu không:* **Khớp với tri thức tài liệu chuẩn Điều 37 khoản 1 (tối thiểu 60%).**

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 trên môi trường MockEmbedder offline (với dense embedding thực sự như SentenceTransformer MiniLM/OpenAI, tỷ lệ đạt 5/5 trong Top-1).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Khi áp dụng chiến lược `FixedSizeChunker` với `overlap=50`, việc duy trì độ chồng chéo giúp hạn chế đáng kể hiện tượng mất thông tin ở các câu nằm sát biên cắt so với khi không có overlap. Tuy nhiên, so với chiến lược `SentenceChunker` hay `RecursiveChunker` của các thành viên khác trong nhóm, `FixedSizeChunker` có điểm yếu cố hữu là dễ cắt ngang lưng câu văn hoặc ranh giới mục logic, làm suy giảm tính toàn vẹn ngữ nghĩa của chunk. Đặc biệt, việc kết hợp **Pre-filtering với metadata** (`audience="student"`) chứng minh là bắt buộc để cô lập tập ứng viên phù hợp với sinh viên trước khi thực hiện tính toán độ tương đồng.


---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

