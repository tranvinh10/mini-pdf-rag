import sys
from src.retrieve import retrieve

for r in retrieve(sys.argv[1], 3):
    print(f'=== {r["score"]:.2f} | trang {r["page"]} ===')
    print(r["text"], "\n")