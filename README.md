# Mini PDF RAG – Hỏi đáp tài liệu tiếng Việt có trích dẫn nguồn

Dự án học tập xây dựng pipeline **Retrieval-Augmented Generation (RAG)** từ các thành phần nền tảng, không sử dụng LangChain hoặc LlamaIndex. Hệ thống cho phép hỏi đáp trên tài liệu PDF tiếng Việt, hiển thị nguồn theo **tên file và số trang**, đồng thời từ chối khi không tìm thấy thông tin phù hợp trong tài liệu.

Dự án chạy local, không yêu cầu API key.

> **Tài liệu mẫu:** `docs/Tailieu.pdf` là quy chế của công ty hư cấu NovaTech, được tạo để thử nghiệm. Mọi thông tin và số liệu trong tài liệu, bao gồm mã số thuế, đều là giả.

## 1. Công nghệ sử dụng

- **Python 3.11+**
- **pypdf:** trích xuất văn bản và số trang từ PDF.
- **BAAI/bge-m3:** tạo embedding 1024 chiều.
- **NumPy:** lưu vector và tính cosine similarity.
- **Ollama + Qwen2.5 3B:** sinh câu trả lời hoàn toàn local.

## 2. Pipeline hoạt động

### Indexing – thực hiện khi tạo hoặc cập nhật tài liệu

```text
PDF
  -> pypdf: đọc từng trang và giữ metadata (file, trang)
  -> Chunking: chia nội dung theo cấu trúc "Điều"
  -> BAAI/bge-m3: chuyển mỗi chunk thành vector 1024 chiều
  -> Lưu data/vectors.npy và data/chunks.json
```

Hai file được tạo có quan hệ theo chỉ số: `vectors[i]` là embedding của `chunks[i]`.

### Querying – thực hiện với mỗi câu hỏi

```text
Câu hỏi
  -> BGE-M3: tạo embedding cho câu hỏi
  -> NumPy: cosine similarity và lấy top-3 chunk
  -> Lớp từ chối 1: bỏ chunk có điểm < 0.55
       -> Không còn chunk phù hợp: từ chối ngay, không gọi LLM
  -> Tạo prompt với các đoạn ngữ cảnh đánh số [1], [2], ...
  -> Qwen2.5 3B qua Ollama (temperature = 0)
  -> Lớp từ chối 2: LLM từ chối nếu ngữ cảnh không đủ thông tin
  -> Tách câu trả lời và nhãn NGUỒN
  -> Hiển thị câu trả lời cùng file/trang được trích dẫn
```

## 3. Cấu trúc dự án

Chạy các lệnh Python từ **thư mục gốc của repository** (thư mục chứa `README.md`).

```text
mini-pdf-rag/
├── data/
│   ├── eval_dev.json          # 19 câu hỏi phát triển
│   ├── eval_test.json         # 12 câu hỏi kiểm thử
│   ├── chunks.json            # Tạo bởi src.embed
│   └── vectors.npy            # Tạo bởi src.embed
├── docs/
│   └── Tailieu.pdf            # PDF mẫu
├── results/
│   ├── dev_final.txt
│   ├── results_by_article.txt
│   └── test_final.txt
├── src/
│   ├── __init__.py
│   ├── load.py
│   ├── chunk.py
│   ├── embed.py
│   ├── retrieve.py
│   ├── generate.py
│   ├── eval.py
│   └── inspect_chunk.py
├── requirements.txt
└── README.md
```

| Module | Vai trò |
|---|---|
| `src/load.py` | Đọc PDF, lưu nội dung từng trang và metadata `source`, `page`. |
| `src/chunk.py` | Chia văn bản theo số ký tự có overlap hoặc theo cấu trúc `Điều`. |
| `src/embed.py` | Tạo embedding và lưu `data/vectors.npy`, `data/chunks.json`. |
| `src/retrieve.py` | Nhúng câu hỏi, tính cosine similarity và lấy top-k chunk. |
| `src/generate.py` | Tạo prompt, gọi Ollama, xử lý từ chối và nguồn trích dẫn. |
| `src/eval.py` | Chạy bộ câu hỏi và chấm từ chối, trả lời, trích dẫn. |
| `src/inspect_chunk.py` | In nội dung các chunk được truy xuất để chẩn đoán lỗi. |

## 4. Cài đặt và chạy

### Yêu cầu

- Python 3.11 trở lên.
- [Ollama](https://ollama.com/) đã được cài đặt và đang chạy.
- Khoảng 5 GB RAM trống là mức dự trù cho embedding model và LLM; mức sử dụng thực tế tùy môi trường.

### Bước 1 – Tạo môi trường Python

**Windows PowerShell:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 2 – Tải LLM

```bash
ollama pull qwen2.5:3b
```

Đảm bảo Ollama đang chạy trước khi sử dụng chức năng hỏi đáp hoặc đánh giá. Trên máy cài Ollama dạng service/desktop, ứng dụng thường tự quản lý tiến trình; nếu môi trường yêu cầu, có thể chạy `ollama serve` trong một terminal riêng.

### Bước 3 – Tạo chỉ mục embedding

Chạy từ thư mục gốc repository:

```bash
python -m src.embed
```

Lần đầu chạy, Sentence Transformers sẽ tải model `BAAI/bge-m3` (khoảng 2 GB, tùy phiên bản/cache). Sau khi hoàn tất, chương trình tạo:

- `data/vectors.npy`: ma trận embedding.
- `data/chunks.json`: nội dung chunk và metadata tương ứng.

Không cần chạy lại bước này mỗi lần đặt câu hỏi. Hãy chạy lại khi thay đổi PDF hoặc cách chunking.

### Bước 4 – Hỏi đáp trên terminal

```bash
python -m src.generate
```

Nhập câu hỏi tại dấu nhắc `Hỏi`. Nhấn Enter trên dòng trống để thoát.

### Bước 5 – Chạy đánh giá

Chạy bộ dev:

```bash
python -m src.eval data/eval_dev.json
```

Chạy bộ test (chỉ sau khi đã chốt code và cấu hình):

```bash
python -m src.eval data/eval_test.json
```

Chương trình in kết quả từng câu hỏi và tổng hợp ba chỉ số: từ chối đúng, trả lời đúng và trích dẫn đúng trang.

### Công cụ kiểm tra retrieval

Để xem nội dung các chunk top-3 cho một câu hỏi:

```bash
python -m src.inspect_chunk "Câu hỏi cần kiểm tra"
```

### Lưu log khi chạy trên Windows PowerShell

Nếu terminal hiển thị tiếng Việt bị lỗi khi chuyển hướng output, đặt UTF-8 trước:

```powershell
$env:PYTHONUTF8 = "1"
python -m src.eval data/eval_dev.json | Tee-Object -FilePath results/dev_final.txt
```

**Lưu ý:** luôn chạy lệnh từ thư mục gốc repository. Các module trong `src/` được chạy theo dạng package bằng `python -m src.<module>`; không chạy bằng cách chuyển vào thư mục `src` rồi gọi trực tiếp file Python.

## 5. Đánh giá

Bộ đánh giá hiện dùng kiểm tra từ khóa: câu trả lời phải chứa đủ các từ khóa khai báo trong JSON và trích dẫn phải bao gồm tất cả các trang kỳ vọng. Đây là cách chấm đơn giản; có thể đánh dấu sai câu trả lời đúng nếu cách diễn đạt khác từ khóa.

### Bộ dev – 19 câu

Bộ dev được dùng trong quá trình điều chỉnh chunking, prompt và ngưỡng retrieval.

| Phiên bản | Từ chối đúng | Trả lời đúng | Trích dẫn đúng |
|---|---:|---:|---:|
| Chunk cố định 800 ký tự | 6/6 | 9/13 | 10/13 |
| Chunk theo "Điều" | 6/6 | 9/13 | 10/13 |
| Sửa regex tách nguồn, yêu cầu chỉ tiếng Việt | 6/6 | 10/13 | 10/13 |
| Định dạng `TRẢ LỜI:` / `NGUỒN:` (bản cuối v1.0) | 6/6 | 9/13 | 11/13 |

Chênh lệch một câu trên 13 câu chưa đủ để kết luận phiên bản nào tốt hơn. Bản cuối được chọn vì khắc phục lỗi câu trả lời rỗng khi model chỉ in nhãn nguồn. Do bộ dev được dùng để điều chỉnh hệ thống, kết quả trên dev có xu hướng lạc quan.

### Bộ test – 12 câu (8 có đáp án, 4 ngoài phạm vi)

Bộ test được soạn riêng và chỉ chạy sau khi đóng băng code. Lần chạy đầu bị trùng một câu hỏi và thiếu câu, nên file `eval_test.json` đã được sửa cho đủ 12 câu rồi chạy lại. Code không thay đổi giữa hai lần. Hai lần chạy sau khi sửa file cho cùng kết quả.

| Từ chối đúng | Trả lời đúng | Trích dẫn đúng |
|---:|---:|---:|
| 4/4 | 6/8 | 6/8 |

Log chạy: `results/test_final.txt`.

Hai câu sai:

- **Câu ghép (WFH và phép năm):** bot trả lời đủ hai ý nhưng viết "24 tiếng" (theo cách hỏi), trong khi từ khóa chấm là "24 giờ", nên bị chấm sai ở chỉ số trả lời. Đây là lỗi do cách chấm. Trích dẫn sai thật: chỉ cite trang 1, thiếu trang 2.
- **Khóa riêng tư thuộc nhóm bảo mật nào:** chunk đúng (Điều 7) đứng top-1 nhưng chỉ đạt 0.54, thấp hơn ngưỡng 0.55 nên bị từ chối ở lớp 1. Đây là lỗi do ngưỡng cứng.

Bộ test do tác giả tự soạn, chỉ có 12 câu, nên mỗi câu chiếm hơn 8% và kết quả chỉ mang tính tham khảo. Trong 8 câu có đáp án, 3 câu diễn đạt lại nội dung đã có ở dev (đi muộn, mật khẩu, SLA P1), 5 câu còn lại hỏi nội dung khác.

## 6. Phân tích lỗi và hạn chế đã biết

- **Retrieval với mã số và định danh:** embedding có thể không đưa chunk chứa mã số thuế vào top-3.
- **Ngưỡng 0.55 khá mong manh:** chunk đúng có thể đạt 0.54–0.55 và bị lớp từ chối đầu tiên loại bỏ. Cosine similarity không phải xác suất câu trả lời đúng.
- **Trích dẫn do LLM tự ghi nhãn:** model có thể ghi thiếu hoặc nhầm nguồn dù nội dung trả lời đúng. Đây là điểm cần ưu tiên cải thiện.
- **LLM 3B có giới hạn:** đôi khi lẫn ngôn ngữ, bỏ qua định dạng hoặc trả lời quá cụt, thiếu đơn vị.
- **Bảng trong PDF:** văn bản trích xuất bằng pypdf có thể làm phẳng cấu trúc bảng, dẫn đến ghép nhầm hàng/cột.
- **Chunking theo Điều:** `chunk_by_article` phù hợp hơn với tài liệu có cấu trúc tiêu đề dạng `Điều N:`; không phải bộ chia chunk tổng quát cho mọi PDF.
- **Định dạng PDF:** hiện chỉ hỗ trợ PDF có lớp văn bản; chưa có OCR cho PDF scan.
- **Phạm vi indexing:** luồng hiện tại được xây quanh một PDF mẫu mỗi lần chạy.
- **Đánh giá:** dữ liệu nhỏ, do tác giả tự soạn và chấm bằng từ khóa; chưa phải benchmark chuẩn.
- **Độ ổn định:** kết quả sinh và trích dẫn có thể dao động giữa các lần chạy dù code không đổi.

## 7. Hướng phát triển

1. Tự xác định nguồn trích dẫn bằng cách đối chiếu câu trả lời với các chunk, thay vì phụ thuộc hoàn toàn vào nhãn nguồn do LLM sinh.
2. Kết hợp BM25 và embedding (hybrid search) để cải thiện truy vấn mã số, ngày tháng và định danh chính xác.
3. Thử reranker hoặc vùng xám cho các chunk có điểm gần ngưỡng thay vì từ chối cứng.
4. Thử model lớn hơn và cải thiện xử lý bảng biểu khi trích xuất PDF.
5. Mở rộng bộ đánh giá, bổ sung đánh giá thủ công hoặc LLM-as-judge có kiểm soát.
6. Đóng gói thành API (FastAPI), giao diện (Streamlit), bổ sung vector database (Chroma/Qdrant) và Docker.
