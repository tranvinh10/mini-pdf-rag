import json
import re
import sys
import time
from generate import answer, REFUSE
from src.retrieve import retrieve

def norm(s):
    return re.sub(r"\b0(\d)\b", r"\1", s.lower())   # "04 ngày" -> "4 ngày"

path = sys.argv[1] if len(sys.argv) > 1 else "eval_set.json"
with open(path, encoding="utf-8") as f:
    items = json.load(f)

n_ref = n_ref_ok = n_ans = n_ans_ok = n_cite_ok = 0
total_time = 0

for it in items:
    t0 = time.perf_counter()
    text, cited, top = answer(it["q"])
    total_time += time.perf_counter() - t0
    refused = (text == REFUSE)
    cite_ok = True

    if it["type"] == "refuse":
        n_ref += 1
        ok = refused
        n_ref_ok += ok
        cite = "-"
    else:
        n_ans += 1
        ok = (not refused) and all(norm(k) in norm(text) for k in it["all_of"])
        pages = {c["page"] for c in cited}
        cite_ok = set(it["pages"]).issubset(pages)
        n_ans_ok += ok
        n_cite_ok += cite_ok
        cite = "OK" if cite_ok else f"SAI (bot cite {sorted(pages)})"

    print(f'{"OK " if ok else "SAI"} | top={top:.2f} | cite: {cite} | {it["q"]}')
    if not ok or not cite_ok:
        print("    BOT:", text.replace("\n", " ")[:250])
        for r in retrieve(it["q"], 3):
            print(f'    chunk: {r["score"]:.2f} | trang {r["page"]} | {r["text"][:70]!r}')

print("---")
print(f"Từ chối đúng: {n_ref_ok}/{n_ref}")
print(f"Trả lời đúng: {n_ans_ok}/{n_ans}")
print(f"Trích dẫn đúng trang: {n_cite_ok}/{n_ans}")
print(f"Thời gian TB: {total_time / len(items):.1f}s/câu")