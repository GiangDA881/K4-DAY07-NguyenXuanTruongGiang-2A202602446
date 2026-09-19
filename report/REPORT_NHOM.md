# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Cocacola  
**Chủ đề:** Dịch vụ và quy định dành cho sinh viên tại Đại học Quốc gia Hà Nội (ĐHQGHN)  
**Ngày:** 2026-09-19  
**Thành viên:**

1. Nguyễn Nhân Sâm — MSSV 2A202602672 — SentenceChunker + metadata filter
2. Nguyễn Xuân Trường Giang — MSSV 2A202602446 — FixedSizeChunker + metadata filter
3. Đào Đức Hải — MSSV 2A202602752 — RecursiveChunker + metadata filter
4. Phan Trọng Hoàn — MSSV 2A202602954 — HeadingChunker + metadata filter

### Phân công điều phối

Các vai R1–R3 là trách nhiệm điều phối cộng thêm; cả bốn thành viên vẫn tự code chiến lược riêng và tự chạy cùng 5 benchmark queries trên corpus nhóm.

| Vai | Người phụ trách | Trách nhiệm | Minh chứng trong repo |
|---|---|---|---|
| **R1 · Data** | Nguyễn Xuân Trường Giang | Chốt chủ đề, kiểm tra 6 tài liệu, metadata, URL nguồn và manifest | `data/vnu-rag-data/*.md`, `sources.csv`, mục 1 |
| **R2 · Benchmark** | Nguyễn Nhân Sâm | Chốt 5 query, viết gold answer, đối chiếu từng gold answer với tài liệu thật | Mục 3 và kết quả benchmark của 4 thành viên |
| **R3 · Strategy** | Phan Trọng Hoàn | Bảo đảm chiến lược không trùng, phụ trách HeadingChunker, chạy baseline chung | Mục 2, bảng so sánh, kết quả HeadingChunker |
| **Hỗ trợ kiểm thử và phân tích** | Đào Đức Hải | Chạy RecursiveChunker, kiểm tra top-3, ghi failure case và hỗ trợ demo | Mục 2, failure analysis |

> **Nộp 1 bản / nhóm.** Báo cáo cá nhân của từng thành viên nộp riêng trong `REPORT_CANHAN.md`. Corpus nhóm nằm trong `data/vnu-rag-data/` và có manifest tại `data/vnu-rag-data/sources.csv`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề và lý do chọn

Nhóm xây dựng knowledge base về các dịch vụ và quy định mà sinh viên ĐHQGHN thường cần tra cứu: đăng ký học phần, học phí, học bổng, thư viện, ký túc xá và kiểm tra/phúc khảo. Đây là chủ đề phù hợp với yêu cầu K4-L3A vì các câu trả lời phải dựa trên quy định công khai, có thể truy vết, đồng thời có những trường hợp dữ liệu không đủ để hệ thống phải nói rõ giới hạn thay vì suy đoán.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn | Ngày lấy / phiên bản | Số ký tự nội dung | Metadata |
|---|---|---|---|---:|---|
| 1 | Đăng ký và rút học phần | [Nguồn quy chế ĐHQGHN](https://fos.ussh.vnu.edu.vn/vi/laws/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-5/) | 2026-09-19 / 2022-10-21 | 2.4k | `student`, `academic_affairs`, `course_registration`, `vi` |
| 2 | Nguyên tắc học phí | [Nguồn quy chế ĐHQGHN](https://fos.ussh.vnu.edu.vn/vi/laws/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-5/) | 2026-09-19 / 2022-10-21 | 2.2k | `student`, `finance`, `tuition`, `vi` |
| 3 | Học bổng và quyền lợi | [Nguồn quy chế ĐHQGHN](https://fos.ussh.vnu.edu.vn/vi/laws/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-5/) | 2026-09-19 / 2022-10-21 | 1.8k | `student`, `student_affairs`, `scholarship`, `vi` |
| 4 | Dịch vụ thư viện và tri thức số | [VNU-LIC](https://lic.vnu.edu.vn/) | 2026-09-19 / not-stated | 1.6k | `all`, `library`, `library`, `vi` |
| 5 | Dịch vụ nội trú và ký túc xá | [Trung tâm Hỗ trợ Sinh viên ĐHQGHN](https://css.vnu.edu.vn/) | 2026-09-19 / not-stated | 1.5k | `student`, `student_affairs`, `dormitory`, `vi` |
| 6 | Kiểm tra, thi và xem xét kết quả điểm | [Nguồn quy chế ĐHQGHN](https://fos.ussh.vnu.edu.vn/vi/laws/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-5/) | 2026-09-19 / 2022-10-21 | 2.5k | `student`, `academic_affairs`, `grade_appeal`, `vi` |

Các file trong corpus là **regulation/service summaries có dẫn nguồn**, không phải bản sao toàn văn. Những giới hạn được ghi ngay trong tài liệu, chẳng hạn không có mức học phí cụ thể, giá phòng hoặc thời hạn phúc khảo thống nhất. Nhóm không đưa dữ liệu cá nhân, thông tin đăng nhập hay tài liệu nội bộ vào repo.

### Cấu trúc metadata

| Trường | Kiểu | Ví dụ | Giá trị cho retrieval |
|---|---|---|---|
| `doc_id` | string | `02_tuition` | Định danh và truy vết tài liệu |
| `source_url` | string | URL chính thức | Kiểm chứng nguồn |
| `retrieved_at` | date | `2026-09-19` | Theo dõi thời điểm thu thập |
| `document_version` | string | `2022-10-21` / `not-stated` | Phân biệt phiên bản/quy định |
| `audience` | enum | `student`, `all` | Lọc đúng đối tượng hỏi |
| `department` | string | `finance`, `library` | Thu hẹp phạm vi nghiệp vụ |
| `category` | string | `tuition`, `dormitory` | Phân loại chủ đề |
| `language` | string | `vi` | Lọc theo ngôn ngữ |

**Checklist quản trị dữ liệu:**
- [x] 6 tài liệu có nguồn công khai và có URL truy vết.
- [x] Không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc nội dung nội bộ.
- [x] Mỗi file có `source_url`, `retrieved_at`, `document_version`, `audience` và metadata bổ sung.
- [x] Corpus chính thức là `data/vnu-rag-data/`; manifest là `data/vnu-rag-data/sources.csv`.

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu sau khi bỏ YAML front matter, với `chunk_size=200`. `SentenceChunker` được cấu hình theo mặc định tối đa 3 câu/chunk.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| 01_course_registration.md | FixedSizeChunker (`fixed_size`) | 11 | 189.3 | Một phần; kích thước đều nhưng có thể cắt giữa câu/điều khoản. |
| 01_course_registration.md | SentenceChunker (`by_sentences`) | 6 | 345.0 | Tốt; giữ nguyên ranh giới câu nhưng chunk thường dài hơn 200 ký tự. |
| 01_course_registration.md | RecursiveChunker (`recursive`) | 14 | 146.9 | Tốt; ưu tiên ranh giới đoạn/câu nhưng tạo nhiều chunk nhỏ hơn. |
| 04_library.md | FixedSizeChunker (`fixed_size`) | 8 | 186.0 | Một phần; kích thước đều nhưng có thể tách rời danh sách dịch vụ. |
| 04_library.md | SentenceChunker (`by_sentences`) | 6 | 246.7 | Tốt; giữ câu và ý dịch vụ tương đối trọn vẹn. |
| 04_library.md | RecursiveChunker (`recursive`) | 10 | 147.2 | Tốt; giữ ranh giới đoạn tốt hơn FixedSize nhưng nhiều chunk hơn. |
| 06_assessment_and_grade_review.md | FixedSizeChunker (`fixed_size`) | 11 | 192.6 | Một phần; có nguy cơ tách điều kiện và mốc thời gian. |
| 06_assessment_and_grade_review.md | SentenceChunker (`by_sentences`) | 6 | 351.0 | Tốt; phù hợp văn bản quy định có câu đầy đủ nhưng chunk khá dài. |
| 06_assessment_and_grade_review.md | RecursiveChunker (`recursive`) | 15 | 139.7 | Tốt; giữ các đoạn nhỏ theo ranh giới tự nhiên, nhưng số chunk cao. |

**Nhận xét baseline:** FixedSize có độ dài ổn định và số chunk vừa phải nhưng dễ cắt mất ngữ cảnh. SentenceChunker giữ ranh giới câu tốt nhất trong baseline nhưng độ dài trung bình vượt `chunk_size=200`. RecursiveChunker giữ cấu trúc đoạn/câu tốt và linh hoạt hơn, đổi lại tạo nhiều chunk nhất. Kết quả này là cơ sở để so sánh với `HeadingChunker`, chiến lược của thành viên R3.

### Phân tích chiến lược trên cùng corpus

| Thành viên | Chiến lược | Tổng chunk | Độ dài trung bình | Nhận xét |
|---|---|---:|---:|---|
| Nguyễn Nhân Sâm | SentenceChunker | **40** | **261.4** | Giữ ranh giới câu, Gemini đúng chủ đề trong top-3 cả 5 query |
| Nguyễn Xuân Trường Giang | FixedSize, size 350, overlap 50 | 97 | 339.8 | Dễ kiểm soát kích thước nhưng có thể cắt giữa câu/điều |
| Đào Đức Hải | Recursive, size 350 | 43 | 246.1 | Giữ ranh giới đoạn/câu tốt hơn, ít chunk vụn |
| Phan Trọng Hoàn | HeadingChunker, max 500 | 35 | 313.5 | Giữ heading và ngữ cảnh điều khoản tốt nhất |

### Chiến lược của từng thành viên

**Nguyễn Nhân Sâm — SentenceChunker**

SentenceChunker tách theo dấu kết thúc câu và gom các câu thành nhóm tối đa 3 câu. Trên corpus team, chiến lược tạo 40 chunks: lần lượt 8, 7, 5, 7, 5 và 8 chunks; độ dài trung bình theo tài liệu lần lượt là 257.9, 270.4, 308.6, 210.9, 297.4 và 262.4 ký tự (trung bình toàn corpus khoảng 261.4 ký tự). Kết quả Gemini trên 5 query chính: Q1 top-2 có `01_course_registration` (0.9048), Q2 top-1 `02_tuition` (0.7665), Q3 top-1 `03_scholarship` (0.8186), Q4 top-1 `04_library` (0.7627), Q5 top-1 `06_assessment_and_grade_review` (0.8805). Như vậy cả 5 câu đều có chunk đúng trong top-3; Q1 cần đọc top-2 vì tài liệu học phí đứng top-1 do câu hỏi có cụm “hoàn học phí”.

**Nguyễn Xuân Trường Giang — FixedSize + metadata filter**

Dùng `chunk_size=350`, `overlap=50`, tạo tổng cộng 97 chunks. Ưu điểm là kích thước gần đồng đều và dễ dự đoán chi phí embedding. Nhược điểm là ranh giới ký tự có thể cắt giữa câu hoặc giữa điều khoản. Metadata filter giúp giảm phạm vi tìm kiếm; Query 1 có tài liệu đúng trong top-2 nhưng 4 query còn lại bị nhiễu.

**Đào Đức Hải — RecursiveChunker + metadata filter**

Dùng separators `['\n\n', '\n', '. ', ' ', '']` và `chunk_size=350`, tạo 43 chunks. Thuật toán ưu tiên tách theo đoạn, dòng và câu trước khi fallback xuống khoảng trắng/ký tự, nên bảo toàn ngữ cảnh hơn FixedSize. Kết quả đạt 3/5 câu có tài liệu liên quan trong top-3; Query 4 đúng top-1 và Query 5 có chunk đúng trong top-3.

**Phan Trọng Hoàn — HeadingChunker + metadata filter**

Tách văn bản theo heading Markdown, giữ heading trong mỗi chunk con; section vượt 500 ký tự được tách tiếp bằng RecursiveChunker. Chiến lược tạo 35 chunks, độ dài trung bình 313.5 ký tự và giữ được ngữ cảnh của từng điều khoản. Đây là chiến lược phù hợp nhất với corpus quy định vì heading thường biểu diễn cấu trúc nghiệp vụ trực tiếp.

### So sánh kết quả retrieval

| Thành viên | Chiến lược | Kết quả top-3 | Điểm mạnh | Điểm yếu |
|---|---|---:|---|---|
| Nguyễn Nhân Sâm | SentenceChunker | **5/5** | Ranh giới câu tự nhiên; 40 chunk, Gemini truy xuất đúng chủ đề | Q1 bị tài liệu học phí chen lên top-1 vì có cụm “hoàn học phí”; đúng tài liệu ở top-2 |
| Nguyễn Xuân Trường Giang | FixedSize + filter | 1/5 | Đơn giản, kích thước đồng đều | 97 chunk vụn; dễ cắt hỏng điều khoản |
| Đào Đức Hải | Recursive + filter | 3/5 | 43 chunk mạch lạc, tốt hơn FixedSize | MockEmbedder làm score nhiễu |
| Phan Trọng Hoàn | Heading + filter + Gemini | **5/5** | 35 chunk, giữ heading/ngữ cảnh, đúng top-1 cả 5 | Section heading quá chung có thể tạo nhiều kết quả cùng tài liệu |

**Chiến lược tốt nhất:** HeadingChunker của Phan Trọng Hoàn và SentenceChunker của Nguyễn Nhân Sâm cùng có 5/5 câu chứa tài liệu liên quan trong top-3; HeadingChunker có ưu thế hơn về vị trí top-1 (5/5), còn SentenceChunker có Q1 ở top-2 do từ khóa “hoàn học phí” kéo tài liệu học phí lên trước. Vì vậy nhóm chọn HeadingChunker làm chiến lược chính cho corpus quy định, SentenceChunker làm phương án đơn giản dễ tái tạo, và RecursiveChunker làm fallback khi tài liệu không có heading rõ. Kết luận này chỉ áp dụng cho corpus và bộ query hiện tại; cần chạy lại khi nguồn hoặc benchmark thay đổi.

### Failure analysis

- **FixedSize:** Query 2, 3, 4, 5 thường trả về sai top-1 vì cắt cứng theo ký tự làm mất ranh giới điều khoản; 97 chunks cũng làm tăng nhiễu.
- **Recursive:** giảm số chunk và giữ ngữ cảnh tốt hơn, nhưng với MockEmbedder dựa trên MD5, vector không biểu diễn ngữ nghĩa nên Query 2, 3, 5 vẫn nhiễu.
- **Heading:** vẫn có thể trả nhiều chunk cùng tài liệu nếu heading chung, nhưng trên bộ query này cả 5 câu đều có chunk đúng ở top-1.
- **Metadata filter:** chỉ giới hạn tập tài liệu theo metadata, không thay thế embedding tốt. Filter cần dùng đúng giá trị đã khai báo (`student` hoặc `all`); không dùng giá trị chưa tồn tại như `undergraduate_student`.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### 5 benchmark queries và gold answers

| # | Câu hỏi | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Khi nào sinh viên được rút học phần và được hoàn học phí? | Được rút theo thủ tục của đơn vị đào tạo; rút trong **2 tuần đầu học kỳ chính** hoặc **1 tuần đầu học kỳ phụ** thì được xóa đăng ký và hoàn học phí. Rút sau hạn không được hoàn và có thể nhận F nếu không hoàn thành. | `01_course_registration`, mục “Rút bớt học phần”; đối chiếu `02_tuition` |
| 2 | Học phí được tính dựa trên những yếu tố nào? | Dựa trên định mức học phí một tín chỉ, số tín chỉ học phần và hệ số tương ứng với học lần đầu, học lại, học cải thiện hoặc học tự chọn tự do. | `02_tuition`, mục “Nghĩa vụ học phí” |
| 3 | Sinh viên chương trình tài năng hoặc chất lượng cao được ưu tiên những quyền lợi gì? | Được ưu tiên xét học bổng khuyến khích phát triển và học bổng tổ chức/cá nhân; nếu ở xa được ưu tiên bố trí KTX; có thể được ưu tiên dùng tài liệu, thiết bị, thư viện, Internet và tham gia chương trình học tập/hợp tác quốc tế. | `03_scholarship` |
| 4 | Trung tâm Thư viện và Tri thức số hỗ trợ những dịch vụ nghiên cứu nào? | Hỗ trợ tra cứu theo chủ đề, DSpace-CRIS, DOIT, EndNote/Mendeley/Zotero, trắc lượng thư mục, số hóa tài liệu, quản lý/lưu trữ/chia sẻ dữ liệu nghiên cứu và hoạt động học thuật. | `04_library` |
| 5 | Điểm kết thúc học phần chiếm tối thiểu bao nhiêu phần trăm điểm học phần? | Điểm đánh giá kết thúc học phần là bắt buộc và chiếm **không dưới 60%** tổng điểm học phần. | `06_assessment_and_grade_review`, mục “Thành phần điểm” |

### Tổng hợp kết quả của từng thành viên

| Thành viên | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng top-3 |
|---|---|---|---|---|---|---:|
| Nguyễn Nhân Sâm — SentenceChunker | Q1: Top-2, 0.9048 | Q2: Top-1, 0.7665 | Q3: Top-1, 0.8186 | Q4: Top-1, 0.7627 | Q5: Top-1, 0.8805 | **5/5** |
| Nguyễn Xuân Trường Giang — FixedSize | Top-2, đúng | Sai top-3 | Sai top-3 | Sai top-3 | Sai top-3 | **1/5** |
| Đào Đức Hải — Recursive | Top-2, đúng | Sai top-3 | Sai top-3 | Top-1, đúng | Top-3, đúng | **3/5** |
| Phan Trọng Hoàn — Heading + Gemini | Top-1, 0.9181 | Top-1, 0.7716 | Top-1, 0.8666 | Top-1, 0.8338 | Top-1, 0.8489 | **5/5** |

### Metadata filtering

Metadata filter có ích nhất khi câu hỏi được giới hạn theo đối tượng, đặc biệt là `audience=student`. Nó loại các tài liệu không phù hợp trước khi xếp hạng, nhưng không thể sửa lỗi do chunking kém hoặc embedding không có tính ngữ nghĩa. Kết quả của Giang và Hải cho thấy filter hỗ trợ Q1, nhưng kết quả tốt nhất vẫn cần kết hợp metadata với chunk có ranh giới ngữ nghĩa và embedding phù hợp. Trong thí nghiệm của Hoàn, filter được áp dụng trước similarity search và cả 5 câu đều có chunk đúng ở top-1.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Kịch bản demo đề xuất

1. Giới thiệu corpus 6 tài liệu, metadata schema và một giới hạn dữ liệu.
2. Chạy cùng 5 queries với FixedSize, Recursive và HeadingChunker.
3. So sánh số chunk: 97 → 43 → 35 và chỉ ra ví dụ ranh giới điều khoản.
4. Demo metadata filter `audience=student`.
5. Trình bày vì sao HeadingChunker đạt 5/5, nhưng không khẳng định chiến lược luôn tốt cho mọi corpus.

### Insights chính

- Chunk ít hơn không tự động tốt hơn; quan trọng là chunk có giữ trọn điều khoản trả lời hay không.
- Chunking theo heading phù hợp với văn bản quy chế vì heading mang thông tin cấu trúc và giảm việc cắt giữa câu.
- Metadata filter cải thiện phạm vi tìm kiếm nhưng không thay thế embedding có tính ngữ nghĩa. MockEmbedder hữu ích cho unit test nhưng không nên dùng để kết luận chất lượng semantic retrieval cuối cùng.

### Bài học và hướng cải thiện

Nếu làm lại, nhóm sẽ dùng HeadingChunker làm chiến lược chính, RecursiveChunker làm fallback, đồng thời chuẩn hóa metadata và chạy benchmark bằng cùng một embedding backend. Nhóm cũng sẽ bổ sung tài liệu chính thức chi tiết hơn cho mức học phí, quy trình KTX và phúc khảo để các câu trả lời không phải dừng ở “dữ liệu chưa đủ”.

### Phân công demo

- Nguyễn Nhân Sâm: giới thiệu bài toán, SentenceChunker và pipeline RAG.
- Nguyễn Xuân Trường Giang: FixedSize, overlap và failure case.
- Đào Đức Hải: RecursiveChunker và so sánh số lượng chunk.
- Phan Trọng Hoàn: HeadingChunker, Gemini benchmark và kết luận.

---

## Tự đánh giá (Phần nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 15 / 15 |
| Chất lượng truy xuất | 10 / 10 |
| Thuyết trình | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

> Trước khi nộp: mỗi thành viên cần copy bản `REPORT_NHOM.md` và `data/vnu-rag-data/` vào fork cá nhân; R1 kiểm tra manifest, R2 kiểm tra 5 query/gold answer, R3 kiểm tra các chiến lược không trùng. Điểm tự đánh giá là đề xuất của nhóm, giảng viên quyết định điểm cuối cùng.
