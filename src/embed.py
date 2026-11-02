
import numpy as np
from sentence_transformers import SentenceTransformer
from load import load_pdf
from chunk import chunk_by_article
import json

model = SentenceTransformer("BAAI/bge-m3")

# Vai trò: lỗi chuyển đổi
# biến văn bản -> ma trận số
def embed_texts(texts):
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
# đầu ra: mảng 2 chiều kích thước (N,1024) - N là số lượng texts


if __name__ == "__main__":
    pages = load_pdf("docs/Tailieu.pdf")
    chunks = chunk_by_article(pages)
    vectors = embed_texts([c["text"] for c in chunks])
    print(vectors.shape)
    np.save("data/vectors.npy", vectors)
    with open("data/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

