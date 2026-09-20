# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Võ Huy Hoàng
**Nhóm:** G-08
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm được tổng hợp riêng trong `REPORT_NHOM.md`.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Cosine similarity(độ tương tự cosine)

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding(vectơ nhúng) có hướng gần nhau. Trong bài toán văn bản, điều này thường cho thấy hai đoạn có nội dung hoặc ý nghĩa tương đồng, kể cả khi cách diễn đạt không hoàn toàn giống nhau.

**Ví dụ có độ tương tự cao:**

- Câu A: Người mua có thể yêu cầu trả hàng.
- Câu B: Khách hàng được phép gửi yêu cầu hoàn trả sản phẩm.
- Lý do: Hai câu cùng nói về quyền yêu cầu trả lại sản phẩm của người mua.

**Ví dụ có độ tương tự thấp:**

- Câu A: Shopee xử lý yêu cầu hoàn tiền.
- Câu B: Hôm nay thời tiết có nhiều mây.
- Lý do: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance(khoảng cách Euclid) cho text embedding(vectơ nhúng văn bản)?**

Cosine similarity tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ lớn của vector. Điều này phù hợp với text embedding vì hướng thường thể hiện nội dung ngữ nghĩa, trong khi độ dài hoặc độ lớn của vector không phải lúc nào cũng phản ánh mức độ liên quan.

### Bài toán chunking(chia nhỏ văn bản)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

```text
step = 500 - 50 = 450
số chunk = ceil((10.000 - 50) / 450)
          = ceil(9.950 / 450)
          = 23
```

**Đáp án:** 23 chunk.

**Nếu `overlap` tăng lên 100:**

```text
step = 500 - 100 = 400
số chunk = ceil((10.000 - 100) / 400)
          = ceil(9.900 / 400)
          = 25
```

Số chunk tăng từ 23 lên 25 vì bước nhảy nhỏ hơn. Overlap(độ chồng lặp) lớn hơn giúp giữ ngữ cảnh nằm ở ranh giới hai chunk, nhưng làm tăng số vector cần lưu và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chunking(chia nhỏ)

**`SentenceChunker.chunk`:**

Tôi dùng regex(biểu thức chính quy) `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tách tại khoảng trắng hoặc xuống dòng ngay sau dấu chấm, chấm than hay chấm hỏi, nhờ đó dấu câu vẫn nằm trong câu. Sau khi loại bỏ chuỗi rỗng và khoảng trắng thừa, các câu được gom theo `max_sentences_per_chunk`; văn bản rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán thử lần lượt các dấu phân cách `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là chuỗi rỗng. Base case(trường hợp cơ sở) xảy ra khi đoạn đã không vượt `chunk_size`; nếu hết dấu phân cách mà đoạn vẫn quá dài, thuật toán cắt cứng theo số ký tự. Các phần nhỏ được ghép vào buffer(vùng đệm) cho đến khi việc ghép tiếp làm vượt giới hạn.

### Lớp `EmbeddingStore`

**`add_documents` và `search`:**

Mỗi `Document` được chuẩn hóa thành bản ghi gồm mã, nội dung, metadata(siêu dữ liệu) và embedding(vectơ nhúng). Store(kho lưu trữ) ưu tiên ChromaDB nếu khả dụng và luôn giữ bản sao trong bộ nhớ; khi tìm kiếm, truy vấn được nhúng rồi tính dot product(tích vô hướng) với từng bản ghi, sắp xếp giảm dần và lấy `top_k`.

**`search_with_filter` và `delete_document`:**

`search_with_filter` lọc bản ghi theo tất cả cặp khóa–giá trị trong metadata trước khi tính điểm, tránh để tài liệu sai đối tượng chiếm vị trí top-k. `delete_document` loại mọi bản ghi có `metadata["doc_id"]` trùng mã cần xóa và trả về `True` khi thực sự có dữ liệu bị xóa.

### Tác tử `KnowledgeBaseAgent`

**`answer`:**

Agent(tác tử) lấy top-k chunk liên quan từ store, đánh số từng phần ngữ cảnh và ghép chúng vào prompt(chỉ dẫn đầu vào). Prompt yêu cầu mô hình chỉ trả lời dựa trên ngữ cảnh và phải nói rõ khi dữ liệu không đủ; sau đó `llm_fn` được gọi để sinh câu trả lời.

### Chiến lược truy xuất cá nhân

Tôi chọn `FixedSizeChunker(chunk_size=500, overlap=50)`. Kích thước cố định giúp kiểm soát lượng văn bản trong mỗi embedding, còn 50 ký tự chồng lặp giúp giảm nguy cơ mất thông tin tại ranh giới chunk. Hạn chế của chiến lược là có thể cắt giữa câu hoặc giữa một điều khoản chính sách.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh đã chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Kết quả:

```text
============================= test session starts =============================
collected 42 items
tests/test_solution.py ..........................................       [100%]
============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua:** 42 / 42.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm thực tế dưới đây được tính bằng `MockEmbedder` và `compute_similarity`. Mock embedding(vectơ nhúng giả lập) tạo vector từ hàm băm, không biểu diễn ngữ nghĩa; bảng này dùng để kiểm tra pipeline(quy trình xử lý), không đại diện cho chất lượng của mô hình embedding thật.

| Cặp | Câu A                                        | Câu B                                               | Dự đoán | Điểm thực tế | Đúng? |
| --- | -------------------------------------------- | --------------------------------------------------- | ------- | -----------: | ----- |
| 1   | Người mua có thể yêu cầu trả hàng.           | Khách hàng được phép gửi yêu cầu hoàn trả sản phẩm. | Cao     |    -0.041304 | Không |
| 2   | Shopee xử lý yêu cầu hoàn tiền.              | Hôm nay thời tiết có nhiều mây.                     | Thấp    |    -0.080914 | Có    |
| 3   | Người bán phải phản hồi trong hai ngày.      | Người bán có thời hạn 48 giờ để trả lời.            | Cao     |     0.086203 | Không |
| 4   | Sản phẩm bị lỗi cần có video làm bằng chứng. | Người mua nên quay video khi sản phẩm bị hư hỏng.   | Cao     |     0.177154 | Không |
| 5   | TikTok Shop hỗ trợ trả hàng.                 | Shopee có chính sách hoàn trả sản phẩm.             | Cao     |    -0.072141 | Không |

**Phản ngẫm:**

Cặp 1 gây bất ngờ nhất vì hai câu gần như diễn đạt cùng một ý nhưng điểm lại âm. Kết quả cho thấy `MockEmbedder` chỉ phù hợp để kiểm tra cấu trúc chương trình; muốn đánh giá quan hệ ngữ nghĩa tiếng Việt cần dùng multilingual embedding(mô hình nhúng đa ngữ) như `paraphrase-multilingual-MiniLM-L12-v2`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Cấu hình

- Corpus(tập tài liệu): 8 tài liệu chính sách Shopee và TikTok Shop.
- Chunker(bộ chia đoạn): `FixedSizeChunker`.
- `chunk_size=500`, `overlap=50`.
- Tổng số chunk: 22.
- `top_k=3`.
- Embedding backend(bộ máy tạo vectơ nhúng): Gemini `gemini-embedding-001`.

| #   | Câu hỏi                                                                                                   | Top-1 chunk truy xuất được                                            |    Score | Có liên quan không?                 | Câu trả lời dựa trên ngữ cảnh top-3                                                                       |
| --- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------: | ----------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 1   | Khi Shopee chấp nhận yêu cầu, Hoàn Tiền Ngay và Trả hàng & Hoàn tiền khác nhau như thế nào?               | `shopee-request-processing#0`: mô tả hai phương án xử lý                    | 0.828695 | Có, đúng ở top-1 | Hoàn Tiền Ngay không cần trả hàng; Trả hàng & Hoàn tiền yêu cầu gửi hàng trong 6 ngày từ thông báo.       |
| 2   | Shopee có hoàn phí vận chuyển ban đầu khi chỉ trả một số sản phẩm không?                                  | `shopee-return-shipping-fees#1`: quy định hoàn phí vận chuyển ban đầu       | 0.843720 | Có, đúng ở top-1 | Không; phí ban đầu chỉ được hoàn khi trả toàn bộ sản phẩm và được hoàn toàn bộ giá trị.                   |
| 3   | Người mua Shopee nên chuẩn bị bằng chứng nào khi sản phẩm lỗi, hư hỏng hoặc khác mô tả?                   | `shopee-return-evidence#1`: ảnh, video và tình trạng sản phẩm               | 0.873956 | Có, đúng ở top-1 | Cần ảnh hoặc video rõ ràng về kiện hàng, niêm phong, quá trình mở kiện và tình trạng lỗi hoặc khác mô tả. |
| 4   | Nếu TikTok Shop quyết định có lợi cho khách hàng, người bán phải khắc phục trong bao lâu?                 | `tiktok-aftersales-disputes#0`: quy trình giải quyết tranh chấp hậu mãi     | 0.839265 | Có, đúng ở top-1 | Người bán phải khắc phục trong 48 giờ, chẳng hạn hoàn tiền hoặc thay sản phẩm.                            |
| 5   | Sau khi chăm sóc khách hàng TikTok Shop liên hệ, người bán có bao lâu và phải làm gì để gửi trả sản phẩm? | `tiktok-seller-to-customer-returns#0`: quy trình người bán gửi trả sản phẩm | 0.862890 | Có, đúng ở top-1 | Người bán có 1 ngày làm việc để đóng gói, gắn nhãn và gửi bằng dịch vụ tiết kiệm có mã theo dõi.          |

**Số câu có tài liệu đúng trong top-3:** 5 / 5.

**Gold@1:** 5 / 5.  
**Gold@3:** 5 / 5.  
**Điểm truy xuất tài liệu:** 10 / 10.

### Phân tích lỗi

Cả năm câu đều truy xuất đúng tài liệu ở top-1 khi dùng Gemini embedding(vectơ nhúng Gemini). Kết quả tốt cho thấy mô hình đa ngữ nhận diện đúng quan hệ ngữ nghĩa tiếng Việt dù `FixedSizeChunker` có thể cắt tại ranh giới câu. Metadata filtering(lọc siêu dữ liệu) tiếp tục giới hạn kết quả vào đúng nền tảng hoặc đối tượng; tuy nhiên cần so sánh với kết quả không lọc để tránh kết luận rằng mọi bộ lọc đều cải thiện thứ hạng.

### Bài học từ thành viên khác hoặc demo nhóm

Phần này cần bổ sung sau khi có kết quả của các thành viên dùng chiến lược khác. Nội dung cần so sánh `FixedSizeChunker` với `SentenceChunker`, `RecursiveChunker` hoặc chiến lược tùy chỉnh trên đúng năm câu hỏi ở trên.

---

## Tự đánh giá

| Tiêu chí              | Điểm tự đánh giá |
| --------------------- | ---------------: |
| Khởi động             |            5 / 5 |
| Hướng tiếp cận        |          10 / 10 |
| Hoàn thiện code       |          30 / 30 |
| Dự đoán độ tương tự   |            5 / 5 |
| Kết quả truy xuất     |          10 / 10 |
| **Tổng phần cá nhân** |      **60 / 60** |
