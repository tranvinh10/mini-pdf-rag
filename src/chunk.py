from .load import load_pdf
import re

def chunk_by_article(pages, max_len=1200):
    chunks = []
    for p in pages:
        text = p["text"].strip()
        for part in re.split(r"(?=\bĐiều\s+\d+\s*:)", text):
            part = part.strip()
            for i in range(0, len(part), max_len):
                if part[i:i + max_len].strip():
                    chunks.append({"source": p["source"], "page": p["page"],
                                   "text": part[i:i + max_len]})
    return chunks

def chunk_pages(pages, chunk_size=1500, overlap=150):
    chunks = []
    for p in pages:
        # loại bỏ khoảng trắng ở đầu/cuối văn bản   
        text = p["text"].strip()
        start = 0 #con trỏ bắt đầu cắt ở vị trí đầu tiên (0) của trang (p)
        while start < len(text):
            end = start + chunk_size
            chunks.append({
                # cắt chuỗi và đóng gói chunk mới
                "source": p["source"],
                "page": p["page"],
                # nếu end=1100 mà text chỉ dài 900 thì py tự động lấy đến ký tự cuối (900) không gây lỗi
                "text": text[start:end],
            })
            # kiểm tra điểm cuối đi hết text chưa
            # nếu rồi break khỏi while và qua trang mới (vì đi hết rồi còn đâu)
            # chưa thì đặt con trỏ (start) của chunk mới rồi duyệt 800 ký tự tiếp coi hết nội dung chưa
            if end >= len(text):
                break
            start += chunk_size - overlap
    return chunks

if __name__ == "__main__":
    pages = load_pdf("docs/Tailieu.pdf")
    chunks = chunk_pages(pages)
    print(len(pages), "pages ->", len(chunks), "chunks")
    print(chunks[0]["text"][-200:])
    print("--- chunk 1 ---")
    print(chunks[1]["text"][:200])



