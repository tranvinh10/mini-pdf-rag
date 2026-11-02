from pypdf import PdfReader

def load_pdf(path):
    reader = PdfReader(path) # PdfReader(path) mở file pdf theo path
    pages = []
# Danh sách này đóng vai trò như một thùng chứa 
# để gom tất cả dữ liệu (dạng dictionary) của từng trang sau khi trích xuất.
    for i, page in enumerate(reader.pages, start=1): # .pages là thuộc tính của đối tượng reader
        text = page.extract_text() or "" # Rút toàn bộ chữ thành chuỗi string
        pages.append({"source": path, "page": i, "text": text})
        # Đóng gói thông tin trang thành một dictionary và thêm vào danh sách pages
        # "source" và "page" được gọi là metadata
    return pages

if __name__ == "__main__":
    pages = load_pdf("docs/Tailieu.pdf")
    print(len(pages), "pages")
    print(pages[0]["text"][:300])
