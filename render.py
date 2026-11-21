"""사용법:
  python render.py themes/saturn.py                  # out/saturn.mp4
  python render.py themes/saturn.py --still 3 8 15   # 해당 초의 PNG만
  python render.py themes/saturn.py --seconds 5      # 앞 5초만 빠르게 확인
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import Renderer  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("-o", "--out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--still", type=float, nargs="*")
    a = ap.parse_args()

    r = Renderer(a.theme, fps=a.fps)
    stem = Path(a.theme).stem
    outdir = Path(__file__).resolve().parent / "out"
    outdir.mkdir(exist_ok=True)
    if a.still is not None:
        for t in a.still:
            p = outdir / f"{stem}_{t:05.1f}s.png"
            r.still(t, p)
            print(p)
        return
    out = Path(a.out) if a.out else outdir / f"{stem}.mp4"
    r.video(out, a.seconds)
    print(out)


if __name__ == "__main__":
    main()
