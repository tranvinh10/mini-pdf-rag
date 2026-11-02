import json
import numpy as np
from .embed import embed_texts
import os

SUFFIX = os.environ.get("RAG_INDEX", "")
vectors = np.load(f"data/vectors{SUFFIX}.npy")
with open(f"data/chunks{SUFFIX}.json", encoding="utf-8") as f:
    chunks = json.load(f)
assert len(vectors) == len(chunks), "vectors và chunks lệch nhau, hãy chạy lại embed.py"
print(f"[index: {len(chunks)} chunks]")

def retrieve(question, k=3):
    q = embed_texts([question])[0]
    scores = vectors @ q
    top = np.argsort(scores)[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in top]

if __name__ == "__main__":
    for r in retrieve("Công ty có thưởng Tết không?"):
        print(f'{r["score"]:.3f} | {r["source"]} trang {r["page"]}')
        print(r["text"][:200], "\n")