# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G-08
**Thành viên:** Võ Huy Hoàng, Lê Trọng Khánh, [chưa có thông tin thành viên 3]
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

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy trình Shopee xử lý yêu cầu trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 20/09/2026 / không nêu phiên bản | 8.692 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 2 | Chuẩn bị bằng chứng khi yêu cầu trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/79467 | 20/09/2026 / không nêu phiên bản | 3.864 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 3 | Chính sách trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 20/09/2026 / hiệu lực 11/03/2026 | 20.129 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 4 | Phương thức gửi hàng hoàn trả và phí hoàn trả Shopee | https://help.shopee.vn/portal/4/article/189477 | 20/09/2026 / không nêu phiên bản | 6.368 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 5 | Nâng cấp tranh chấp hậu mãi trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=101756645132049 | 20/09/2026 / 18/06/2025 | 7.744 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 6 | Trả hàng do đổi ý trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=6988871880738576 | 20/09/2026 / 21/08/2026 | 9.758 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 7 | Chính sách trả hàng và hoàn tiền TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=1766935302801169 | 20/09/2026 / 21/08/2026 | 20.891 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |
| 8 | Người bán gửi trả sản phẩm cho người mua trên TikTok Shop | https://seller-vn.tiktok.com/university/essay?knowledge_id=4041059496167184 | 20/09/2026 / 20/08/2026 | 5.918 | `doc_id`, `audience`, `category`, `language`, nguồn và phiên bản |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | Chuỗi | `shopee-return-evidence` | Định danh tài liệu gốc và hỗ trợ xóa toàn bộ chunk của tài liệu. |
| `title` | Chuỗi | `Chuẩn bị bằng chứng...` | Giải thích nội dung kết quả truy xuất cho người đọc. |
| `source_url` | URL | `https://help.shopee.vn/...` | Truy vết và kiểm chứng câu trả lời với nguồn gốc. |
| `retrieved_at` | Ngày | `2026-09-20` | Kiểm tra thời điểm dữ liệu được thu thập. |
| `document_version` | Chuỗi/ngày | `2025-06-18` hoặc `not-stated` | Theo dõi phiên bản hoặc ngày hiệu lực của chính sách. |
| `audience` | Chuỗi | `buyer`, `seller`, `both` | Lọc chính sách dành cho đúng người mua hoặc người bán. |
| `category` | Chuỗi | `return-evidence` | Thu hẹp kết quả theo loại chính sách hoặc nghiệp vụ. |
| `language` | Chuỗi | `vi` | Xác định ngôn ngữ tài liệu và mô hình embedding phù hợp. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-return-evidence` | FixedSizeChunker (`fixed_size`) | 8 | 477,38 | Khá; có overlap nhưng có thể cắt giữa câu. |
| `shopee-return-evidence` | SentenceChunker (`by_sentences`) | 12 | 286,08 | Tốt; giữ nguyên ranh giới câu. |
| `shopee-return-evidence` | RecursiveChunker (`recursive`) | 9 | 385,44 | Tốt; ưu tiên ranh giới đoạn/câu. |
| `shopee-return-refund-policy` | FixedSizeChunker (`fixed_size`) | 44 | 494,68 | Khá; ổn định về kích thước nhưng có thể tách điều khoản. |
| `shopee-return-refund-policy` | SentenceChunker (`by_sentences`) | 48 | 405,79 | Tốt; giữ câu đầy đủ nhưng đôi khi mất liên kết với tiêu đề. |
| `shopee-return-refund-policy` | RecursiveChunker (`recursive`) | 71 | 276,28 | Tốt; chunk mạch lạc hơn nhưng số lượng lớn. |
| `tiktok-aftersales-disputes` | FixedSizeChunker (`fixed_size`) | 17 | 474,94 | Khá; kích thước đồng đều. |
| `tiktok-aftersales-disputes` | SentenceChunker (`by_sentences`) | 14 | 516,36 | Tốt với văn xuôi; một số chunk vượt 500 ký tự. |
| `tiktok-aftersales-disputes` | RecursiveChunker (`recursive`) | 17 | 427,88 | Tốt; giữ được ranh giới tự nhiên tương đối. |

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

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Võ Huy Hoàng | `FixedSizeChunker(500, overlap=50)` | 10/10 | Cấu hình đơn giản, số lượng chunk dễ kiểm soát; overlap giúp giữ thông tin gần ranh giới; cả 5 tài liệu đúng đều đứng top-1. | Có thể cắt giữa câu hoặc giữa điều khoản, làm giảm tính mạch lạc của chunk. |
| Lê Trọng Khánh | `SentenceChunker(max_sentences_per_chunk=5)` | 9/10 | Giữ câu nguyên vẹn, dễ đọc và giảm cắt ngang điều khoản; cả 5 tài liệu đúng đều xuất hiện trong top-3. | Có thể tách sai chữ viết tắt, tạo chunk dài với danh sách thiếu dấu câu và làm mất liên kết với tiêu đề. |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

Theo kết quả hiện có của hai thành viên, `FixedSizeChunker` của Võ Huy Hoàng tốt nhất về điểm truy xuất với 10/10 và đưa đúng tài liệu lên top-1 ở cả 5 câu, trong khi `SentenceChunker` đạt 9/10 do Q1 chỉ đứng top-2. Tuy vậy, `SentenceChunker` tạo các đoạn dễ đọc hơn; kết luận cuối cùng cần bổ sung kết quả của thành viên 3 dùng chiến lược theo heading(tiêu đề/mục) trước khi khẳng định chiến lược tốt nhất cho toàn nhóm.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Khi Shopee chấp nhận yêu cầu, Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau như thế nào? | Hoàn Tiền Ngay không yêu cầu người mua trả hàng; với Trả hàng & Hoàn tiền, người mua phải chọn phương thức trả hàng và gửi hàng về kho Shopee hoặc người bán trong vòng 6 ngày từ khi nhận thông báo. | `shopee-request-processing` |
| 2 | Shopee có hoàn phí vận chuyển ban đầu khi người mua chỉ trả lại một số sản phẩm trong đơn không? | Không. Phí ban đầu chỉ được hoàn khi yêu cầu áp dụng cho toàn bộ sản phẩm và toàn bộ giá trị đã thanh toán được hoàn. | `shopee-return-shipping-fees` |
| 3 | Người mua Shopee nên chuẩn bị những bằng chứng nào khi sản phẩm bị lỗi, hư hỏng hoặc khác mô tả? | Quay/chụp toàn bộ kiện hàng, thông tin vận chuyển và niêm phong; video mở kiện phải liên tục, thể hiện quá trình mở gói, tình trạng và lỗi của sản phẩm. | `shopee-return-evidence` |
| 4 | Nếu TikTok Shop quyết định có lợi cho khách hàng trong tranh chấp hậu mãi, người bán phải khắc phục trong bao lâu? | Trong vòng 48 giờ; có thể hoàn tiền hoặc thay sản phẩm và chịu phí vận chuyển nếu có. | `tiktok-aftersales-disputes` |
| 5 | Sau khi nhân viên chăm sóc khách hàng TikTok Shop liên hệ, người bán có bao lâu và phải làm gì để gửi trả sản phẩm? | Có 1 ngày làm việc để đóng gói an toàn, gắn nhãn và gửi qua đơn vị vận chuyển tiết kiệm có mã theo dõi. | `tiktok-seller-to-customer-returns` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Phân biệt hai phương án hoàn tiền Shopee | FixedSize | Có | FixedSize: top-1; Sentence: top-2. |
| 2 | Hoàn phí vận chuyển khi trả một phần đơn hàng | FixedSize và Sentence | Có | Cả hai đều đưa đúng tài liệu lên top-1. |
| 3 | Bằng chứng cho sản phẩm lỗi/khác mô tả | FixedSize và Sentence | Có | Cả hai đều đưa đúng tài liệu lên top-1. |
| 4 | Thời hạn khắc phục tranh chấp TikTok Shop | FixedSize và Sentence | Có | Cả hai đều đưa đúng tài liệu lên top-1. |
| 5 | Thời hạn và cách người bán gửi trả sản phẩm | FixedSize và Sentence | Có | Cả hai đều đưa đúng tài liệu lên top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có, rõ nhất ở Q3 trong benchmark FixedSize: bộ lọc `audience=buyer` đưa tài liệu chuẩn từ top-2 lên top-1 bằng cách loại các tài liệu không dành riêng cho người mua. Ở Q1 và Q5, tài liệu đúng vốn đã ở top-1 nên bộ lọc không đổi thứ hạng, nhưng vẫn giảm tập ứng viên sai đối tượng; benchmark Sentence cũng không ghi nhận thay đổi thứ hạng ở các câu có lọc.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- `FixedSizeChunker` đạt 10/10 dù có nguy cơ cắt giữa câu, cho thấy embedding(vectơ nhúng) đa ngữ và overlap(độ chồng lặp) có thể bù một phần hạn chế về ranh giới đoạn.
- `SentenceChunker` giữ nội dung dễ đọc hơn nhưng tạo 100 chunk và Q1 chỉ đứng top-2; chunk mạch lạc không tự động bảo đảm thứ hạng truy xuất cao hơn.
- Metadata filtering(lọc siêu dữ liệu) hữu ích khi corpus có nội dung gần giống nhau cho người mua và người bán; ở Q3, bộ lọc đã cải thiện hạng tài liệu chuẩn từ 2 lên 1 trong benchmark FixedSize.

**Bài học rút ra khi so sánh trong nhóm:**

Trên cùng 8 tài liệu và 5 câu hỏi, hai chiến lược đều đạt Gold@3 = 5/5 nhưng khác Gold@1: FixedSize đạt 5/5 còn Sentence đạt 4/5. Kết quả cho thấy cần đánh giá đồng thời độ chính xác truy xuất và tính mạch lạc của chunk; số lượng chunk nhiều hơn hoặc câu nguyên vẹn hơn không nhất thiết tạo kết quả xếp hạng tốt hơn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

Nhóm sẽ làm sạch phần menu, nội dung lặp và lời dẫn không liên quan trước khi chunk, đồng thời thử chiến lược theo heading(tiêu đề/mục) để gắn tiêu đề điều khoản vào từng đoạn. Nhóm cũng sẽ chuẩn hóa metadata, tách rõ tài liệu `buyer` và `seller`, rồi chạy A/B test(so sánh hai cấu hình) có và không có bộ lọc trên toàn bộ 5 câu hỏi.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
