"""시안 테마에서 물체 부분만 글자로 뽑아 웹 배경용 web/bg.json을 만든다.

  python web/make_bg.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import CHARS, Renderer  # noqa: E402

# (테마, 시각) - 형체가 완성된 순간
PICKS = [("saturn", 12.6), ("saturn", 8.0), ("saturn", 3.0),
         ("saturn", 11.0)]
LIGHT = 0.28        # 이보다 어두운 칸(배경 글자비, 흐린 별)은 버린다


def grab(slug, t):
    r = Renderer(ROOT / "themes" / f"{slug}.py")
    g = r.grid
    g.ch[:] = 0
    g.col[:] = 0
    r.theme.draw(g, t)
    lit = (g.col.max(-1) > LIGHT) & (g.ch > 0)
    rows = np.nonzero(lit.sum(1) > 2)[0]
    cols = np.nonzero(lit.sum(0) > 1)[0]
    r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    lines = []
    for r_ in range(r0, r1):
        lines.append("".join(CHARS[g.ch[r_, c]] if lit[r_, c] else " "
                             for c in range(c0, c1)).rstrip())
    return {"slug": slug, "text": "\n".join(lines)}


out = [grab(s, t) for s, t in PICKS]
(ROOT / "web" / "bg.json").write_text(json.dumps(out, ensure_ascii=False))
for o in out:
    print(o["slug"], len(o["text"].split("\n")), "줄")
