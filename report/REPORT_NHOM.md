# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G-08
**Thành viên:** Võ Huy Hoàng, Lê Trọng Khánh, Bùi Quang Vinh
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách trả hàng, hoàn tiền và xử lý tranh chấp trên Shopee và TikTok Shop.

**Tại sao nhóm chọn chủ đề này?**

Đây là nhóm chính sách có nhiều điều kiện, thời hạn và trách nhiệm khác nhau theo nền tảng, đối tượng người mua/người bán nên phù hợp để kiểm tra retrieval(truy xuất) theo ngữ nghĩa và metadata(siêu dữ liệu). Các câu trả lời cũng có thể đối chiếu trực tiếp với nguồn công khai, giúp đánh giá rõ khả năng giữ ngữ cảnh của từng chiến lược chunking(chia đoạn).

### Danh sách tài liệu (Data Inventory)

| #   | Tên tài liệu                                                 | Nguồn (Source URL)                                                          | Ngày lấy / Phiên bản             | Số ký tự | Metadata đã gán                                                  |
| --- | ------------------------------------------------------------ | --------------------------------------------------------------------------- | -------------------------------- | -------- | ---------------------------------------------------------------- |
| 1   | Quy trình Shopee xử lý yêu cầu trả hàng và hoàn tiền         | https://help.shopee.vn/portal/4/article/190242                              | 20/09/2026 / không nêu phiên bản | 8.692    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 2   | Chuẩn bị bằng chứng khi yêu cầu trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/79467                               | 20/09/2026 / không nêu phiên bản | 3.864    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 3   | Chính sách trả hàng và hoàn tiền Shopee                      | https://help.shopee.vn/portal/4/article/77251                               | 20/09/2026 / hiệu lực 11/03/2026 | 20.129   | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 4   | Phương thức gửi hàng hoàn trả và phí hoàn trả Shopee         | https://help.shopee.vn/portal/4/article/189477                              | 20/09/2026 / không nêu phiên bản | 6.368    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 5   | Nâng cấp tranh chấp hậu mãi trên TikTok Shop                 | https://seller-vn.tiktok.com/university/essay?knowledge_id=101756645132049  | 20/09/2026 / 18/06/2025          | 7.744    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 6   | Trả hàng do đổi ý trên TikTok Shop                           | https://seller-vn.tiktok.com/university/essay?knowledge_id=6988871880738576 | 20/09/2026 / 21/08/2026          | 9.758    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 7   | Chính sách trả hàng và hoàn tiền TikTok Shop                 | https://seller-vn.tiktok.com/university/essay?knowledge_id=1766935302801169 | 20/09/2026 / 21/08/2026          | 20.891   | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 8   | Người bán gửi trả sản phẩm cho người mua trên TikTok Shop    | https://seller-vn.tiktok.com/university/essay?knowledge_id=4041059496167184 | 20/09/2026 / 20/08/2026          | 5.918    | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu       | Ví dụ giá trị                  | Tại sao hữu ích cho truy xuất (retrieval)?                       |
| ------------------ | ---------- | ------------------------------ | ---------------------------------------------------------------- |
| `doc_id`           | Chuỗi      | `shopee-return-evidence`       | Định danh tài liệu gốc và hỗ trợ xóa toàn bộ chunk của tài liệu. |
| `title`            | Chuỗi      | `Chuẩn bị bằng chứng...`       | Giải thích nội dung kết quả truy xuất cho người đọc.             |
| `source_url`       | URL        | `https://help.shopee.vn/...`   | Truy vết và kiểm chứng câu trả lời với nguồn gốc.                |
| `retrieved_at`     | Ngày       | `2026-09-20`                   | Kiểm tra thời điểm dữ liệu được thu thập.                        |
| `document_version` | Chuỗi/ngày | `2025-06-18` hoặc `not-stated` | Theo dõi phiên bản hoặc ngày hiệu lực của chính sách.            |
| `audience`         | Chuỗi      | `buyer`, `seller`, `both`      | Lọc chính sách dành cho đúng người mua hoặc người bán.           |
| `category`         | Chuỗi      | `return-evidence`              | Thu hẹp kết quả theo loại chính sách hoặc nghiệp vụ.             |
| `language`         | Chuỗi      | `vi`                           | Xác định ngôn ngữ tài liệu và mô hình embedding phù hợp.         |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                      | Chiến lược (Strategy)            | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                    |
| ----------------------------- | -------------------------------- | -------------- | ----------------- | ----------------------------------------------------------- |
| `shopee-return-evidence`      | FixedSizeChunker (`fixed_size`)  | 8              | 477,38            | Khá; có overlap nhưng có thể cắt giữa câu.                  |
| `shopee-return-evidence`      | SentenceChunker (`by_sentences`) | 12             | 286,08            | Tốt; giữ nguyên ranh giới câu.                              |
| `shopee-return-evidence`      | RecursiveChunker (`recursive`)   | 9              | 385,44            | Tốt; ưu tiên ranh giới đoạn/câu.                            |
| `shopee-return-refund-policy` | FixedSizeChunker (`fixed_size`)  | 44             | 494,68            | Khá; ổn định về kích thước nhưng có thể tách điều khoản.    |
| `shopee-return-refund-policy` | SentenceChunker (`by_sentences`) | 48             | 405,79            | Tốt; giữ câu đầy đủ nhưng đôi khi mất liên kết với tiêu đề. |
| `shopee-return-refund-policy` | RecursiveChunker (`recursive`)   | 71             | 276,28            | Tốt; chunk mạch lạc hơn nhưng số lượng lớn.                 |
| `tiktok-aftersales-disputes`  | FixedSizeChunker (`fixed_size`)  | 17             | 474,94            | Khá; kích thước đồng đều.                                   |
| `tiktok-aftersales-disputes`  | SentenceChunker (`by_sentences`) | 14             | 516,36            | Tốt với văn xuôi; một số chunk vượt 500 ký tự.              |
| `tiktok-aftersales-disputes`  | RecursiveChunker (`recursive`)   | 17             | 427,88            | Tốt; giữ được ranh giới tự nhiên tương đối.                 |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Võ Huy Hoàng**

- **Loại chiến lược:** `FixedSizeChunker` (chia đoạn theo kích thước cố định), với `chunk_size=500` và `overlap=50`.
- **Mô tả & lý do chọn cho chủ đề này:** Tôi chọn kích thước cố định để kiểm soát lượng văn bản đầu vào của mỗi embedding(vectơ nhúng) và giữ cách xử lý nhất quán giữa 8 tài liệu chính sách Shopee, TikTok Shop. Phần chồng lặp 50 ký tự giúp hạn chế mất thông tin tại ranh giới chunk(đoạn văn bản), nhưng chiến lược vẫn có thể cắt giữa câu hoặc giữa một điều khoản.
- **Cấu hình đánh giá:** `top_k=3`, Gemini `gemini-embedding-001`; tổng cộng 22 chunk.
- **Kết quả:** `Gold@1 = 5/5`, `Gold@3 = 5/5`, điểm truy xuất tài liệu `10/10`. Cả 5 câu hỏi đều truy xuất đúng tài liệu ở vị trí top-1.
- **Code snippet:** Không có mã tùy chỉnh; sử dụng lớp có sẵn như sau:

```python
chunker = FixedSizeChunker(chunk_size=500, overlap=50)
```

**Thành viên 2 — Lê Trọng Khánh**

- **Loại chiến lược:** `SentenceChunker` (chia đoạn theo câu), với `max_sentences_per_chunk=5`.
- **Mô tả & lý do chọn:** Chiến lược tách tại khoảng trắng sau dấu `.`, `!`, `?`, giữ lại dấu câu và gom tối đa 5 câu trong mỗi chunk(đoạn văn bản). Cách này giữ câu nguyên vẹn khi đọc điều khoản và yêu cầu bằng chứng, đồng thời giảm tình trạng cắt ngang câu so với `FixedSizeChunker` (chia đoạn theo kích thước cố định).
- **Cấu hình đánh giá:** `top_k=3`, Gemini `gemini-embedding-001`; 8 tài liệu tạo thành 100 chunk.
- **Kết quả:** `Gold@1 = 4/5`, `Gold@3 = 5/5`, điểm truy xuất tài liệu `9/10`. Câu Q1 truy xuất đúng tài liệu ở top-2; bốn câu còn lại truy xuất đúng tài liệu ở top-1.
- **Hạn chế:** Chữ viết tắt có thể gây tách sai; danh sách không có dấu kết thúc câu có thể tạo chunk dài; tiêu đề không tự được gắn lại vào mọi chunk.
- **Code snippet:** Không có mã tùy chỉnh; sử dụng lớp có sẵn như sau:

```python
chunker = SentenceChunker(max_sentences_per_chunk=5)
```

**Thành viên 3 — Bùi Quang Vinh**

- **Loại chiến lược:** `HeadingRecursiveChunker` (chia theo heading/section), với `chunk_size=500`.
- **Mô tả & lý do chọn:** Chiến lược nhận diện Markdown heading và section đánh số, giữ heading đi cùng nội dung của section. Nếu section dài hơn 500 ký tự thì phần body được chia tiếp bằng `RecursiveChunker`, sau đó heading được prepend vào từng child chunk. Cách này phù hợp với tài liệu chính sách vì điều kiện, thời hạn, ngoại lệ và trách nhiệm thường nằm dưới các tiêu đề/mục cụ thể; giữ heading giúp chunk có thêm ngữ cảnh và dễ truy vết về điều khoản gốc.
- **Cấu hình đánh giá hiện có:** `top_k=3`, local embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; 8 tài liệu tạo thành **232 chunk**.
- **Kết quả document retrieval:** `Gold@1 = 4/5`, `Gold@3 = 4/5`, điểm truy xuất tài liệu `8/10`. Q1, Q3, Q4, Q5 lấy đúng gold document ở top-1; Q2 không lấy được gold document trong top-3.
- **Kết quả evidence retrieval:** `Evidence@1 = 1/5`, `Evidence@3 = 3/5`, `Evidence score = 4/10`. Q4 có đầy đủ evidence ở top-1; Q3 và Q5 có đầy đủ evidence ở top-3.
- **Hạn chế:** Số chunk tăng nhiều do các section nhỏ và heading được giữ lại; các điều khoản gần nghĩa vẫn có thể cạnh tranh thứ hạng. Kết quả hiện dùng local embedding nên chưa thể so trực tiếp về điểm số với hai thành viên đang dùng Gemini nếu chưa chạy lại cùng backend.
- **Code snippet:**

```python
chunker = HeadingRecursiveChunker(chunk_size=500)
```

### So Sánh Giữa Các Thành Viên

| Thành viên     | Chiến lược (Strategy)                        | Điểm truy xuất (/10) | Điểm mạnh                                                                                                                         | Điểm yếu                                                                                                 |
| -------------- | -------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Võ Huy Hoàng   | `FixedSizeChunker(500, overlap=50)`          | 10/10                | Cấu hình đơn giản, số lượng chunk dễ kiểm soát; overlap giúp giữ thông tin gần ranh giới; cả 5 tài liệu đúng đều đứng top-1.      | Có thể cắt giữa câu hoặc giữa điều khoản, làm giảm tính mạch lạc của chunk.                              |
| Lê Trọng Khánh | `SentenceChunker(max_sentences_per_chunk=5)` | 9/10                 | Giữ câu nguyên vẹn, dễ đọc và giảm cắt ngang điều khoản; cả 5 tài liệu đúng đều xuất hiện trong top-3.                            | Có thể tách sai chữ viết tắt, tạo chunk dài với danh sách thiếu dấu câu và làm mất liên kết với tiêu đề. |
| Bùi Quang Vinh | `HeadingRecursiveChunker(chunk_size=500)`    | 8/10 document        | Giữ heading/section cùng nội dung; trong benchmark local, evidence tốt hơn Fixed/Sentence/Recursive; agent trả lời đúng Q3 và Q5. | 232 chunk; Q2 không có gold document trong top-3; Q1 thiếu full evidence; Q4 agent chỉ trả lời một phần. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

Các output hiện tại cho thấy mỗi chiến lược có ưu thế khác nhau. FixedSize đạt document retrieval `10/10` và Sentence đạt `9/10` trên Gemini, trong khi Heading đạt document retrieval `8/10` nhưng có evidence score `4/10` trên local embedding và giữ cấu trúc điều khoản rõ hơn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                                                                     | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                                       | Chunk nào chứa thông tin?           |
| --- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| 1   | Khi Shopee chấp nhận yêu cầu, Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau như thế nào?                         | Hoàn Tiền Ngay không yêu cầu người mua trả hàng; với Trả hàng & Hoàn tiền, người mua phải chọn phương thức trả hàng và gửi hàng về kho Shopee hoặc người bán trong vòng 6 ngày từ khi nhận thông báo. | `shopee-request-processing`         |
| 2   | Shopee có hoàn phí vận chuyển ban đầu khi người mua chỉ trả lại một số sản phẩm trong đơn không?                    | Không. Phí ban đầu chỉ được hoàn khi yêu cầu áp dụng cho toàn bộ sản phẩm và toàn bộ giá trị đã thanh toán được hoàn.                                                                                 | `shopee-return-shipping-fees`       |
| 3   | Người mua Shopee nên chuẩn bị những bằng chứng nào khi sản phẩm bị lỗi, hư hỏng hoặc khác mô tả?                    | Quay/chụp toàn bộ kiện hàng, thông tin vận chuyển và niêm phong; video mở kiện phải liên tục, thể hiện quá trình mở gói, tình trạng và lỗi của sản phẩm.                                              | `shopee-return-evidence`            |
| 4   | Nếu TikTok Shop quyết định có lợi cho khách hàng trong tranh chấp hậu mãi, người bán phải khắc phục trong bao lâu?  | Trong vòng 48 giờ; có thể hoàn tiền hoặc thay sản phẩm và chịu phí vận chuyển nếu có.                                                                                                                 | `tiktok-aftersales-disputes`        |
| 5   | Sau khi nhân viên chăm sóc khách hàng TikTok Shop liên hệ, người bán có bao lâu và phải làm gì để gửi trả sản phẩm? | Có 1 ngày làm việc để đóng gói an toàn, gắn nhãn và gửi qua đơn vị vận chuyển tiết kiệm có mã theo dõi.                                                                                               | `tiktok-seller-to-customer-returns` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| #   | Câu hỏi                                       | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú                                 |
| --- | --------------------------------------------- | ------------------------------- | ------------------------------- | --------------------------------------- |
| 1   | Phân biệt hai phương án hoàn tiền Shopee      | FixedSize                       | Có                              | FixedSize: top-1; Sentence: top-2.      |
| 2   | Hoàn phí vận chuyển khi trả một phần đơn hàng | FixedSize và Sentence           | Có                              | Cả hai đều đưa đúng tài liệu lên top-1. |
| 3   | Bằng chứng cho sản phẩm lỗi/khác mô tả        | FixedSize và Sentence           | Có                              | Cả hai đều đưa đúng tài liệu lên top-1. |
| 4   | Thời hạn khắc phục tranh chấp TikTok Shop     | FixedSize và Sentence           | Có                              | Cả hai đều đưa đúng tài liệu lên top-1. |
| 5   | Thời hạn và cách người bán gửi trả sản phẩm   | FixedSize và Sentence           | Có                              | Cả hai đều đưa đúng tài liệu lên top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có. Trong các benchmark hiện có, metadata giúp giới hạn candidate theo `platform` hoặc `audience`, đặc biệt khi corpus có nhiều chính sách gần nghĩa dành cho buyer/seller. Ở benchmark FixedSize, Q3 với `audience=buyer` cải thiện hạng tài liệu chuẩn từ top-2 lên top-1. Với Heading, Q1/Q2 lọc theo `platform=shopee`, Q4 theo `platform=tiktok_shop`, Q3 theo `audience=buyer` và Q5 theo `audience=seller`; tuy nhiên Q2 vẫn thất bại trong top-3, cho thấy metadata filter không thay thế được chất lượng chunking và embedding.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- `FixedSizeChunker` đạt document retrieval 10/10 trong run Gemini dù có nguy cơ cắt giữa câu; overlap có thể giúp giữ một phần thông tin tại ranh giới.
- `SentenceChunker` giữ câu nguyên vẹn và dễ đọc hơn, nhưng tạo nhiều chunk hơn FixedSize và có một câu gold document chỉ đứng top-2.
- `HeadingRecursiveChunker` giữ cấu trúc điều khoản và cho evidence score `4/10` trong benchmark local, cao hơn Fixed `0/10`, Sentence `0/10` và Recursive `1/10` khi cùng dùng local embedding; agent đạt `2 correct / 1 partial / 2 incorrect`, tương ứng **6/10 theo rubric**; đổi lại số chunk tăng lên 232 và Q2 bị miss.
- Metadata filtering hữu ích để giảm candidate sai platform/audience, nhưng không bảo đảm gold evidence xuất hiện nếu chunk hoặc embedding chưa phù hợp.

**Bài học rút ra khi so sánh trong nhóm:**

Kết quả cho thấy “đúng tài liệu”, “đúng evidence” và “agent trả lời đúng” là ba mức đánh giá khác nhau. Q4 có full evidence ở top-1 nhưng agent vẫn chỉ trả lời một phần; ngược lại Q3 và Q5 có evidence ở rank 3 nhưng agent vẫn trả lời đúng. Heading cho thấy lợi ích của việc giữ section context, tuy nhiên retrieval tốt chưa đảm bảo generation đầy đủ. Nhóm vẫn cần chuẩn hóa cùng embedding nếu muốn so sánh tuyệt đối giữa ba thành viên.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

Nhóm sẽ tiếp tục làm sạch menu/navigation artifacts trước khi chunk, chuẩn hóa metadata `platform`, `audience`, `category`, sau đó chạy tất cả strategy trên cùng embedding. Với Heading, nhóm sẽ thử gộp các section quá ngắn, điều chỉnh quy tắc nhận diện heading và thử overlap nhỏ cho phần body để giảm tình trạng evidence bị tách sang nhiều chunk. Sau đó nhóm sẽ chạy agent benchmark để kiểm tra câu trả lời cuối thay vì chỉ đánh giá document/evidence retrieval.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá |
| ---------------------------------------- | ---------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10          |
| Thiết kế chiến lược (Strategy Design)    | 15 / 15          |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10          |
| Thuyết trình (Demo)                      | 5 / 5            |
| **Tổng phần nhóm**                       | **40 / 40**      |
