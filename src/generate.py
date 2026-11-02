import re
import time
import ollama
from src.retrieve import retrieve

MODEL = "qwen2.5:3b"
THRESHOLD = 0.55
DEBUG = False
REFUSE = "Tôi không tìm thấy thông tin này trong tài liệu."

def build_prompt(question, contexts):
    blocks = []
    for i, c in enumerate(contexts, start=1):
        blocks.append(f'[{i}] ({c["source"]}, trang {c["page"]})\n{c["text"]}')
    context_text = "\n\n".join(blocks)
    return f"""Bạn là trợ lý hỏi đáp tài liệu. Chỉ trả lời dựa trên phần NGỮ CẢNH bên dưới.
Nếu ngữ cảnh không chứa thông tin để trả lời, hãy trả lời đúng một câu: "{REFUSE}" và không ghi nguồn.
Không dùng kiến thức bên ngoài. Trả lời bằng tiếng Việt, ngắn gọn.
Chỉ viết bằng tiếng Việt, không dùng ngôn ngữ khác.
Khi có câu trả lời, viết đúng 2 dòng:
TRẢ LỜI: <câu trả lời ngắn gọn>
NGUỒN: [số đoạn đã dùng], ví dụ NGUỒN: [1] hoặc NGUỒN: [1, 2]

NGỮ CẢNH:
{context_text}

CÂU HỎI: {question}"""

def parse_sources(text, n):
    m = re.search(r"NGUỒN:\s*\[?([\d,\s]+)\]?", text, re.IGNORECASE)
    ids = []
    if m:
        ids = [int(x) for x in re.findall(r"\d+", m.group(1)) if 1 <= int(x) <= n]
    clean = re.sub(r"\n?NGUỒN:[^\n]*", "", text, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^\s*TRẢ LỜI:\s*", "", clean, flags=re.IGNORECASE)
    return clean, ids

def answer(question, k=3):
    results = retrieve(question, k)
    top_score = results[0]["score"]
    contexts = [r for r in results if r["score"] >= THRESHOLD]
    if not contexts:
        return REFUSE, [], top_score
    resp = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": build_prompt(question, contexts)}],
        options={"temperature": 0, "num_ctx": 2048},
    )
    raw = resp["message"]["content"].strip()
    if DEBUG:
        d_pre = (resp["prompt_eval_duration"] / 1e9) or 1e-9
        d_dec = (resp["eval_duration"] / 1e9) or 1e-9
        print(f'prefill: {resp["prompt_eval_count"] / d_pre:.0f} token/s | '
              f'decode: {resp["eval_count"] / d_dec:.1f} token/s')
        print("RAW:", repr(raw), "| prompt tokens:", resp["prompt_eval_count"])
    if REFUSE in raw:
        return REFUSE, [], top_score
    text, ids = parse_sources(raw, len(contexts))
    if not text:
        return REFUSE, [], top_score
    cited = [contexts[i - 1] for i in ids] or contexts[:1]
    return text, cited, top_score

if __name__ == "__main__":
    while True:
        q = input("Hỏi (Enter để thoát): ")
        if not q:
            break
        t0 = time.perf_counter()
        text, cited, top = answer(q)
        print(f"[top score: {top:.3f} | {time.perf_counter() - t0:.1f}s]")
        print(text)
        for c in cited:
            print(f'  - {c["source"]}, trang {c["page"]}: "{c["text"][:80]}..."')
        print()