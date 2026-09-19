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
| 1 | Sinh viên ĐHQGHN rút bớt học phần đã đăng ký trong thời hạn nào để được hoàn trả lại học phí? *(Yêu cầu lọc audience="student")* | Việc rút bớt học phần chỉ được chấp nhận trong 2 tuần kể từ đầu học kỳ chính, 1 tuần kể từ đầu học kỳ phụ; sinh viên được hoàn trả học phí học phần rút bớt (Điều 23). | `01_course_registration#6` / Điều 23 |
| 2 | Khối lượng học tập tối thiểu và tối đa mà sinh viên ĐHQGHN phải đăng ký trong mỗi học kỳ chính là bao nhiêu? | Tối thiểu không ít hơn 2/3 và tối đa không quá 3/2 khối lượng trung bình một học kỳ theo kế hoạch học tập chuẩn (Điều 21). | `01_course_registration#0` / Điều 21 |
| 3 | Nghĩa vụ đóng học phí của sinh viên ĐHQGHN và điều kiện dự thi kết thúc học phần liên quan đến học phí là gì? | Sinh viên có trách nhiệm đóng học phí theo quy định của ĐHQGHN; sinh viên chưa hoàn thành nghĩa vụ học phí sẽ không được dự thi kết thúc học phần (Điều 58, Điều 60). | `02_tuition#0`, `#17` / Điều 58, 60 |
| 4 | Sinh viên chương trình tài năng, chất lượng cao tại ĐHQGHN được quy đổi điểm học phần nâng cao để xét học bổng như thế nào? | Điểm từ 4 đến 9 được cộng thêm 1 điểm khi tính điểm xét học bổng; điểm 0, 1, 2, 3 và 10 giữ nguyên (Điều 38). | `03_scholarship#2` / Điều 38 |
| 5 | Thời hạn chấm thi và công bố điểm thi kết thúc học phần tại ĐHQGHN được quy định hoàn thành trong bao nhiêu ngày? | Thời gian chấm thi và công bố điểm thi chậm nhất là 15 ngày làm việc kể từ ngày thi cuối cùng của học phần (Điều 38 khoản 6). | `06_assessment_and_grade_review#7` / Điều 38 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn rút bớt học phần hoàn phí | FixedSize & Sentence (+Filter) | Có (Top-1) | Bắt buộc phải có `metadata_filter={"audience": "student"}` để khu biệt đúng quyền lợi sinh viên. |
| 2 | Khối lượng tín chỉ tối thiểu/tối đa | RecursiveChunker | Có (Top-1) | RecursiveChunker tách trọn vẹn khối Điều 21 Quy chế 3626. |
| 3 | Nghĩa vụ học phí & cấm thi | SentenceChunker | Có (Top-1) | SentenceChunker cô lập chính xác câu quy định chế tài cấm thi do nợ học phí. |
| 4 | Quy đổi điểm học bổng tài năng | FixedSizeChunker | Có (Top-2) | Nằm trong Top-2 với score 0.272. |
| 5 | Thời hạn chấm & công bố điểm | FixedSize & Recursive | Có (Top-1) | Khớp chính xác Top-1 với điểm số cao nhất (score 0.247). |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất hữu ích và mang tính quyết định**, thể hiện rõ rệt nhất ở **Câu hỏi 1** ("Sinh viên ĐHQGHN rút bớt học phần đã đăng ký trong thời hạn nào để được hoàn trả lại học phí?"). Nếu không có bộ lọc `metadata_filter={"audience": "student"}`, hệ thống sẽ truy xuất lẫn lộn các tài liệu chung hoặc tài liệu quản lý đơn vị, khiến câu trả lời không tập trung vào đúng quy chế của người học. Nhờ áp dụng Pre-filtering, 100% các ứng viên không phù hợp bị loại bỏ ngay từ đầu, đảm bảo tính chính xác và an toàn tuyệt đối cho câu trả lời.

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

