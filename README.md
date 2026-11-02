# RAG hỏi đáp tài liệu tiếng Việt (có trích dẫn nguồn)

Dự án học tập: tự xây pipeline RAG từ đầu (không dùng LlamaIndex/LangChain) để hỏi đáp trên tài liệu PDF tiếng Việt, **có trích dẫn nguồn (file, trang)** và **từ chối khi tài liệu không có thông tin**. Chạy hoàn toàn local, không cần API key.

> Tài liệu mẫu `docs/Tailieu.pdf` là quy chế của công ty hư cấu "NovaTech", do AI tạo ra để thử nghiệm. Mọi số liệu trong đó (kể cả mã số thuế) đều là giả.

## Pipeline

```
Indexing (chạy 1 lần)
  PDF -> load (pypdf) -> chunk theo "Điều" -> embedding (BAAI/bge-m3, 1024 chiều)
      -> vectors.npy + chunks.json   (vectors[i] ứng với chunks[i])

Querying (mỗi câu hỏi)
  câu hỏi -> embedding -> cosine similarity (NumPy) -> top-3 chunk
  -> Lớp từ chối 1: loại chunk có điểm < 0.55; không còn chunk nào thì từ chối ngay (không gọi LLM)
  -> prompt (ngữ cảnh đánh số [1], [2]...) -> LLM (Qwen2.5 3B qua Ollama, temperature 0)
  -> Lớp từ chối 2: LLM tự từ chối nếu ngữ cảnh không đủ thông tin
  -> tách câu trả lời và nhãn NGUỒN -> hiển thị file/trang
```

## Cấu trúc thư mục

| File | Vai trò |
|---|---|
| `load.py` | Đọc PDF, giữ metadata (file, trang) cho từng trang |
| `chunk.py` | Chunking: `chunk_pages` (cố định ký tự + overlap) và `chunk_by_article` (theo "Điều") |
| `embed.py` | Embedding các chunk, lưu `vectors.npy` và `chunks.json` |
| `retrieve.py` | Embed câu hỏi, cosine similarity, lấy top-k |
| `generate.py` | Prompt, gọi LLM, từ chối 2 lớp, tách nguồn trích dẫn |
| `eval.py` | Chạy bộ câu hỏi, chấm 3 chỉ số: từ chối, trả lời, trích dẫn |
| `inspect_chunk.py` | Xem nội dung đầy đủ của các chunk top-k (để chẩn đoán lỗi) |
| `eval_dev.json` | Bộ dev: 19 câu (13 có đáp án, 6 ngoài phạm vi) |
| `eval_test.json` | Bộ test: 12 câu (8 có đáp án, 4 ngoài phạm vi), soạn riêng, chỉ chạy sau khi đóng băng code |

## Cách chạy

Yêu cầu: Python 3.11+, [Ollama](https://ollama.com) đang chạy. Cần khoảng 5GB RAM trống (embedding model ~2GB, LLM ~2GB).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:3b

python embed.py        # tạo vectors.npy và chunks.json (lần đầu tự tải bge-m3 ~2GB)
python generate.py     # hỏi đáp trên terminal
python eval.py eval_dev.json
```

Trên Windows PowerShell, nếu dùng pipe (`| Tee-Object`), đặt trước: `$env:PYTHONUTF8 = "1"`.

## Kết quả đánh giá

Chấm bằng từ khoá (câu trả lời phải chứa đủ từ khoá, trích dẫn phải đủ các trang cần thiết). Đây là cách chấm thô, có thể chấm sai những câu trả lời đúng nhưng diễn đạt khác.

### Bộ dev (19 câu): dùng để chọn chunking, prompt, ngưỡng

| Phiên bản | Từ chối đúng | Trả lời đúng | Trích dẫn đúng |
|---|---|---|---|
| Chunk cố định 800 ký tự | 6/6 | 9/13 | 10/13 |
| Chunk theo "Điều" | 6/6 | 9/13 | 10/13 |
| + sửa regex tách nguồn, yêu cầu "chỉ tiếng Việt" | 6/6 | 10/13 | 10/13 |
| + định dạng `TRẢ LỜI:` / `NGUỒN:` (**bản cuối, v1.0**) | 6/6 | 9/13 | 11/13 |

Chênh 1 câu trên 13 câu là nhiễu, chưa đủ để kết luận phiên bản nào tốt hơn. Bản cuối được chọn vì sửa được lỗi câu trả lời rỗng (model chỉ in `NGUỒN: [1]`). Vì dev được dùng để chỉnh hệ thống nên số trên dev có xu hướng lạc quan.

### Bộ test: soạn riêng, chạy sau khi đóng băng code

Lần chạy đầu `eval_test.json` bị trùng một câu hỏi; đã sửa file (không đổi code) rồi chạy lại.

| Từ chối đúng | Trả lời đúng | Trích dẫn đúng |
|---|---|---|
| 4/4 | 6/8 | 6/8 |

Bộ test gồm 12 câu (8 có đáp án, 4 ngoài phạm vi). Ba trong tám câu có đáp án là cách hỏi khác của nội dung đã có trong dev, nên bộ này đo cả khả năng hiểu cách diễn đạt khác lẫn thông tin mới. Test cao hơn dev một chút không có nghĩa hệ thống tổng quát tốt: bộ nhỏ và có phần dễ hơn.

Lỗi trên test (2 câu, cả hai đều sai ở trả lời và trích dẫn):
- **Khóa riêng tư thuộc nhóm bảo mật nào?** Chunk đúng (Điều 7) đứng top-1 nhưng chỉ đạt 0.54, thấp hơn ngưỡng 0.55 nên bị lớp từ chối 1 chặn. Cùng kiểu lỗi với câu phép năm trên dev (đạt 0.553, suýt bị chặn).
- **Câu ghép WFH + phép năm:** bot trả lời đủ hai ý nhưng chỉ trích dẫn trang 1, thiếu trang 2. Ngoài ra câu bị chấm sai vì bot viết "24 tiếng" còn từ khoá là "24 giờ": nội dung đúng, lỗi do cách chấm. Kỳ vọng không được sửa sau khi đã thấy kết quả.

Bộ test do chính tác giả soạn, kích thước nhỏ, nên chỉ mang tính tham khảo, không phải benchmark chuẩn.

## Phân tích lỗi (dev, bản cuối)

- **Mã số thuế:** lỗi retrieval. Chunk chứa mã số thuế không lọt top-3. Embedding yếu với mã và số chính xác.
- **SLA P1:** model chèn từ của ngôn ngữ khác ("2 jam") dù prompt yêu cầu chỉ dùng tiếng Việt.
- **Tạm ứng và sa thải:** nội dung số đúng nhưng câu trả lời quá cụt ("3", "5"), thiếu đơn vị nên bị chấm sai. Ở câu sa thải, nhãn còn lẫn ký tự Cyrillic nên không được tách khỏi câu trả lời.
- **Câu hỏi ghép 2 trang:** trả lời đủ ý nhưng chỉ trích dẫn 1 trong 2 trang.

## Hạn chế đã biết

- **Ngưỡng 0.55 mong manh:** nhiều chunk đúng chỉ đạt 0.54-0.55. Điểm cosine không phải xác suất đúng, và nó dao động theo cách diễn đạt câu hỏi.
- **Trích dẫn phụ thuộc vào việc LLM tự ghi nhãn nguồn.** Model 3B có thể ghi thiếu, hoặc ghi nhầm nguồn dù trả lời đúng. Đây là lỗi nguy hiểm nhất vì người dùng dễ tin vào nguồn.
- **Model 3B nhỏ:** lẫn ngôn ngữ, đôi khi bỏ qua chỉ dẫn định dạng.
- **Bảng bị làm phẳng** khi `pypdf` trích text, model có thể chọn nhầm ô.
- `chunk_by_article` chỉ hợp với tài liệu có cấu trúc "Điều N:".
- Chỉ hỗ trợ PDF có text (không OCR), một file mỗi lần.
- Bộ đánh giá nhỏ, tự soạn, chấm bằng từ khoá.
- Kết quả có thể dao động giữa các lần chạy: theo quan sát, một câu test (WFH 30 phút) từng bị trích dẫn sai ở lần chạy trước nhưng đúng ở lần chạy sau dù code không đổi. Chưa rõ nguyên nhân.

## Hướng phát triển

1. Để code tự quyết định nguồn trích dẫn (đối chiếu câu trả lời với từng chunk) thay vì nhờ LLM.
2. Hybrid search (BM25 + embedding) để xử lý mã số, ngày tháng.
3. Reranker, hoặc đưa các chunk điểm 0.45-0.55 vào "vùng xám" cho LLM quyết định thay vì ngưỡng cứng.
4. Thử model lớn hơn hoặc LLM qua API; chuẩn hoá bảng biểu khi trích text.
5. Mở rộng bộ đánh giá, thêm chấm bằng LLM-as-judge.
6. Đóng gói FastAPI, giao diện Streamlit, vector DB (Chroma/Qdrant), Docker.
