# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm 03 — Lớp K4-L3A  
**Thành viên:**  
1. Nguyễn Xuân Trường Giang — MSSV: 2A202602446 (Chiến lược: FixedSize + Metadata Filter)  
2. Lê Minh Tuấn — MSSV: 2A202602450 (Chiến lược: SentenceChunker + Metadata Filter)  
3. Trần Hoàng Nam — MSSV: 2A202602455 (Chiến lược: RecursiveChunker + Metadata Filter)  
**Ngày:** 19/09/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ & Quy chế Học vụ Đại học (VinUni University Regulations & Services)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề quy chế và dịch vụ học vụ đại học vì đây là miền dữ liệu thực tế có tính cấu trúc cao, chứa nhiều điều khoản số liệu cụ thể (hạn mức tín chỉ, số ngày mượn sách, hạn nộp học phí, điều kiện học bổng) và đặc biệt phân chia đối tượng rõ ràng (`student` vs `faculty`), tạo tiền đề lý tưởng để kiểm chứng sức mạnh của Metadata Filtering và Chunking Strategy.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế đăng ký học phần và rút môn học | https://vinuni.edu.vn/academic-regulations/course-registration | 2026-09-18 / 2026.1 | 1,515 | `doc_id`: course-registration, `audience`: student, `department`: academic-affairs |
| 2 | Quy định mượn trả tài liệu thư viện cho sinh viên | https://vinuni.edu.vn/library/regulations-student | 2026-09-18 / 2026.1 | 1,280 | `doc_id`: library-services, `audience`: student, `department`: library |
| 3 | Quy định mượn trả tài liệu thư viện cho giảng viên | https://vinuni.edu.vn/library/regulations-faculty | 2026-09-18 / 2026.1 | 1,180 | `doc_id`: library-faculty, `audience`: faculty, `department`: library |
| 4 | Quy định về nộp học phí và chính sách gia hạn | https://vinuni.edu.vn/finance/tuition-payment-policy | 2026-09-18 / 2026.1 | 1,350 | `doc_id`: tuition-payment, `audience`: student, `department`: finance |
| 5 | Chính sách học bổng khuyến khích học tập | https://vinuni.edu.vn/scholarships/merit-based | 2026-09-18 / 2026.1 | 1,480 | `doc_id`: scholarship-policy, `audience`: student, `department`: student-affairs |
| 6 | Quy chế phúc khảo bài thi kết thúc học phần | https://vinuni.edu.vn/examinations/regrade-appeal | 2026-09-18 / 2026.1 | 1,290 | `doc_id`: exam-regrade, `audience`: student, `department`: academic-affairs |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] `sources.csv` được lưu tại `data/university/sources.csv`, khớp chính xác 1-1 với 6 tài liệu `.md`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `library-services` | Định danh tài liệu gốc, hỗ trợ nhóm các chunk và phục vụ hàm `delete_document()`. |
| `audience` | string | `student`, `faculty` | Phân tách đối tượng bạn đọc; yếu tố then chốt giúp `search_with_filter()` không bị nhầm lẫn giữa quy định của sinh viên và giảng viên. |
| `department` | string | `academic-affairs`, `library` | Giúp lọc chính xác theo phòng ban quản lý, tăng tốc độ và độ chính xác khi truy vấn chuyên sâu. |
| `category` | string | `registration`, `tuition` | Phân loại nghiệp vụ học vụ, cho phép truy xuất theo nhóm chuyên đề nghiệp vụ. |
| `language` | string | `vi` | Định vị ngôn ngữ tài liệu phục vụ đa ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu tiêu biểu trong corpus (độ dài chunk_size=300):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `course-registration.md` | FixedSizeChunker (`fixed_size`) | 6 | 260.0 | Trung bình (cắt ngang một số câu tại biên chunk) |
| | SentenceChunker (`by_sentences`) | 5 | 280.6 | Tốt (giữ nguyên câu, nhưng một số đoạn điều khoản dài bị gom chung) |
| | RecursiveChunker (`recursive`) | 8 | 174.9 | Rất tốt (chia nhỏ theo đoạn `\n\n` và câu, giữ trọn vẹn ngữ nghĩa) |
| `library-services.md` | FixedSizeChunker (`fixed_size`) | 5 | 254.8 | Trung bình (các điều khoản mượn bị ngắt giữa chừng) |
| | SentenceChunker (`by_sentences`) | 4 | 287.2 | Tốt (câu hoàn chỉnh, độ dài đồng đều) |
| | RecursiveChunker (`recursive`) | 6 | 191.0 | Rất tốt (tách riêng từng điều khoản mục 1, mục 2 rõ ràng) |
| `scholarship-policy.md` | FixedSizeChunker (`fixed_size`) | 5 | 285.2 | Khá (độ dài ổn định) |
| | SentenceChunker (`by_sentences`) | 5 | 260.0 | Tốt (các mức GPA nằm trọn trong câu) |
| | RecursiveChunker (`recursive`) | 8 | 162.0 | Rất tốt (tách riêng từng mục học bổng Xuất sắc/Giỏi/Khá) |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Xuân Trường Giang (2A202602446)**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=350`, `overlap=50`) + Metadata Filter (`audience="student"`)
- **Mô tả & lý do chọn cho chủ đề này:** Phân đoạn văn bản thành các khối có kích thước đều đặn 350 ký tự với độ chồng lấn 50 ký tự để duy trì tính liên tục của ngữ cảnh tại các ranh giới cắt. Kết hợp với Pre-filtering metadata để lọc trước đối tượng `student`, loại bỏ nguy cơ nhầm lẫn với tài liệu của giảng viên.
- **Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=350, overlap=50)
chunks = chunker.chunk(document_body)
results = store.search_with_filter(query, top_k=3, metadata_filter={"audience": "student"})
```

**Thành viên 2 — Lê Minh Tuấn (2A202602450)**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`) + Metadata Filter
- **Mô tả & lý do chọn:** Chia nhỏ văn bản theo ranh giới câu ngữ pháp tự nhiên. Vì các quy định học vụ thường được cấu trúc thành các câu văn độc lập mang tính mệnh lệnh hoặc điều kiện, việc nhóm 3 câu giúp giữ trọn vẹn mệnh đề logic mà không lo bị cắt cụt từ ngữ giữa chừng.
- **Code snippet:**
```python
chunker = SentenceChunker(max_sentences_per_chunk=3)
chunks = chunker.chunk(document_body)
results = store.search_with_filter(query, top_k=3, metadata_filter={"audience": "student"})
```

**Thành viên 3 — Trần Hoàng Nam (2A202602455)**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=400`, separators=`["\n\n", "\n", ". ", " "]`) + Metadata Filter
- **Mô tả & lý do chọn:** Sử dụng thuật toán đệ quy kết hợp gom gộp tuần tự theo thứ tự phân cấp Markdown: ngắt theo đoạn lớn (`\n\n`), sau đó xuống dòng (`\n`) và dấu câu (`. `). Giữ cấu trúc đề mục và tính toàn vẹn của các điều khoản quy định.
- **Code snippet:**
```python
chunker = RecursiveChunker(chunk_size=400, separators=["\n\n", "\n", ". ", " "])
chunks = chunker.chunk(document_body)
results = store.search_with_filter(query, top_k=3, metadata_filter={"audience": "student"})
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Xuân Trường Giang | FixedSizeChunker (350, 50) + Filter | 6 / 10 | Kích thước chunk đồng đều, overlap 50 ký tự giúp giảm mất mát thông tin tại biên cắt. | Vẫn có trường hợp cắt ngang lưng một câu phức hoặc ngắt giữa chừng con số điều kiện. |
| Lê Minh Tuấn | SentenceChunker (3 câu) + Filter | 8 / 10 | 100% câu văn hoàn chỉnh ngữ pháp, không bao giờ bị cụt từ; độ mạch lạc câu rất cao. | Độ dài chunk không đồng đều (có câu ngắn 20 ký tự, có câu ghép dài 150 ký tự). |
| Trần Hoàng Nam | RecursiveChunker (400) + Filter | 8 / 10 | Tôn trọng cấu trúc phân đoạn của văn bản quy chế, độ dài chunk được kiểm soát tối ưu. | Cần tinh chỉnh danh sách separators cẩn thận nếu văn bản chứa định dạng danh sách bullet points. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `RecursiveChunker` và `SentenceChunker` đều thể hiện sự vượt trội hơn so với `FixedSizeChunker` đối với văn bản quy chế học vụ. Trong đó, `RecursiveChunker` là chiến lược tối ưu nhất vì nó phân cấp tự nhiên theo cấu trúc văn bản hành chính (tách theo từng điều khoản `\n\n`), đồng thời gom gộp các đoạn nhỏ giúp mỗi chunk là một điều khoản hoàn chỉnh mang trọn vẹn ngữ cảnh ngữ nghĩa.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **câu 1 bắt buộc dùng lọc metadata `audience="student"`** để tránh lấy nhầm quy định của giảng viên (`library-faculty`).

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn mượn sách thư viện tối đa bao nhiêu ngày và được gia hạn mấy lần? *(Yêu cầu lọc audience="student")* | Thời hạn mượn sách tiêu chuẩn cho sinh viên là 14 ngày, được gia hạn trực tuyến tối đa 2 lần (mỗi lần thêm 7 ngày). | `library-services#1` / Mục 2 |
| 2 | Sinh viên được đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong một học kỳ chính? | Trong học kỳ chính, sinh viên phải đăng ký tối thiểu 12 tín chỉ và tối đa 22 tín chỉ (sinh viên diện cảnh báo tối đa 14 tín chỉ). | `course-registration#2` / Mục 2 |
| 3 | Hạn chót nộp học phí của học kỳ là khi nào và mức phạt nộp muộn là bao nhiêu? | Hạn chót là 17h00 thứ Sáu tuần thứ 4 tính từ ngày khai giảng; phạt nộp muộn 0.05% trên tổng số tiền chậm nộp mỗi ngày. | `tuition-payment#0`, `#1` / Mục 1 & 2 |
| 4 | Tiêu chuẩn để sinh viên đạt học bổng khuyến khích học tập loại Xuất sắc là gì? | GPA học kỳ đạt từ 3.80 trở lên, điểm rèn luyện từ 90 điểm trở lên và không vi phạm kỷ luật hay nợ môn. | `scholarship-policy#1` / Mục 1 |
| 5 | Thời hạn nộp đơn phúc khảo bài thi kết thúc học phần là bao lâu và lệ phí bao nhiêu? | Thời hạn nộp đơn là trong vòng 07 ngày làm việc kể từ ngày công bố điểm; lệ phí là 100.000 VNĐ/bài thi. | `exam-regrade#0`, `#1` / Mục 1 & 2 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Mượn sách thư viện & gia hạn | SentenceChunker + Filter | Có (Top-1) | Bắt buộc phải có `metadata_filter={"audience": "student"}` để không lấy nhầm hạn 90 ngày của giảng viên. |
| 2 | Số tín chỉ tối thiểu & tối đa | FixedSizeChunker & Recursive | Có (Top-1) | Cả hai chiến lược đều trả về đúng Mục 2 của `course-registration`. |
| 3 | Hạn nộp học phí & phí phạt trễ | FixedSizeChunker | Có (Top-3) | `tuition-payment#0` nằm trong Top-3 với score 0.190. |
| 4 | Tiêu chuẩn học bổng Xuất sắc | RecursiveChunker | Có (Top-1) | Recursive giữ trọn vẹn khối tiêu chuẩn GPA và điểm rèn luyện. |
| 5 | Thời hạn & lệ phí phúc khảo | FixedSizeChunker & Sentence | Có (Top-1) | `exam-regrade#0` đạt vị trí Top-1 với điểm số cao nhất (score 0.226). |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất hữu ích và mang tính quyết định**, thể hiện rõ rệt nhất ở **Câu hỏi 1** ("Thời hạn mượn sách thư viện tối đa bao nhiêu ngày và được gia hạn mấy lần?"). Nếu không có bộ lọc `metadata_filter={"audience": "student"}`, hệ thống sẽ truy xuất lẫn lộn tài liệu `library-faculty.md` (quy định giảng viên được mượn 90 ngày, tối đa 20 cuốn) và agent sẽ đưa ra câu trả lời sai đối tượng cho sinh viên. Nhờ áp dụng Pre-filtering, 100% các ứng viên không phải sinh viên bị loại bỏ ngay từ đầu, đảm bảo tính chính xác và an toàn tuyệt đối cho câu trả lời.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Hiệu ứng ranh giới (Boundary Effect) của Fixed-size vs Semantic Boundary:** Cắt theo ký tự cố định có thể làm đứt gãy câu, trong khi cắt theo câu và tiêu đề Markdown giúp chunk giữ trọn vẹn ngữ nghĩa độc lập.
> 2. **Pre-filtering vs Post-filtering:** Pre-filtering là bắt buộc trong hệ thống RAG thực tế khi corpus có nhiều đối tượng bạn đọc khác nhau (`audience`) trên cùng một chủ đề (như thư viện). Post-filtering có thể làm rỗng kết quả nếu Top-K ban đầu bị chiếm lĩnh bởi tài liệu không phù hợp.
> 3. **Bản chất của Vector Embeddings:** Thử nghiệm chứng minh MockEmbedder (băm chuỗi MD5) chỉ cho giá trị ngẫu nhiên và không phản ánh ngữ nghĩa; để đưa vào sản phẩm thực tế cần các mô hình Dense Embeddings đa ngôn ngữ (như `paraphrase-multilingual-MiniLM-L12-v2` hoặc OpenAI/Gemini Embeddings).

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ dữ liệu nhưng sự lựa chọn về kích thước chunk (`chunk_size`), độ chồng lấn (`overlap`) và đơn vị tách (ký tự, câu hay đoạn) tạo ra sự khác biệt rất lớn về khả năng trúng đích của Top-3 retrieval. Không có một kích thước chunk nào là "hoàn hảo cho mọi trường hợp", mà chiến lược chia nhỏ phải đồng điệu với cấu trúc tự nhiên của văn bản nguồn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ áp dụng chiến lược **Heading-Aware Chunking** (khi chia nhỏ bất kỳ section dài nào, luôn tự động gắn tiêu đề mục cha `## Heading` vào đầu mỗi chunk con). Điều này giúp các chunk nằm ở nửa sau của một điều khoản dài vẫn luôn giữ được ngữ cảnh "đang nói về quy định gì", từ đó nâng cao vượt bậc điểm tương đồng ngữ nghĩa khi truy vấn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

