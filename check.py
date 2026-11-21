"""주제 스크립트 자동 점검. 사람이 보기 전에 기계로 걸러낼 수 있는 것을 거른다.

  python check.py themes/jellyfish.py

결과: 터미널 보고서 + out/<slug>_check.png (장면별 정지 화면 모음).
실패 항목이 있으면 종료 코드 1.
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import MAX_DURATION, MONO, TOP_H, W, Renderer  # noqa: E402

MAX_LINE = 72          # 코드 패널에서 잘리지 않는 대략의 줄 길이
STILL_DIFF = 0.004     # 이보다 움직임이 작으면 "정지 구간"
LOOP_DIFF = 0.03       # 첫 프레임과 마지막 프레임 차이 허용치


def top(img):
    return img[:TOP_H].astype(np.float32) / 255.0


def motion(r, t):
    """t 시점에서 한 프레임 사이 위쪽 화면이 얼마나 바뀌는지."""
    a, b = top(r.frame(t)), top(r.frame(t + 1.0 / r.fps))
    return float(np.abs(a - b).mean())


def sheet(r, samples, path):
    tw, th, lab = 270, 274, 30
    cols = min(6, len(samples))
    rows = (len(samples) + cols - 1) // cols
    out = Image.new("RGB", (cols * tw, rows * (th + lab)), (12, 12, 16))
    font = ImageFont.truetype(MONO, 15)
    d = ImageDraw.Draw(out)
    for i, (t, name) in enumerate(samples):
        im = Image.fromarray(r.frame(t)[:TOP_H]).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + lab)
        out.paste(im, (x, y))
        d.text((x + 6, y + th + 6), f"{t:5.2f}s {name}"[:30], font=font,
               fill=(210, 210, 215))
    out.save(path)


def main(theme_path):
    fails, warns = [], []
    src = Path(theme_path).read_text(encoding="utf-8")

    # 1) 소스 규칙
    for n, ln in enumerate(src.split("\n"), 1):
        if any(ord(ch) > 126 and ch != "°" for ch in ln):
            fails.append(f"{n}행: 코드 글꼴에 없는 글자(한글 등) - 주석은 영어로")
        if len(ln) > MAX_LINE:
            warns.append(f"{n}행: {len(ln)}자, 코드 패널에서 잘림")

    # 2) 불러오기와 필수 상수
    try:
        r = Renderer(theme_path)
    except Exception as e:  # 길이 초과, 문법 오류 등
        print(f"FAIL 불러오기: {e}")
        return 1
    th = r.theme
    D = r.duration
    for name in ("TITLE", "SCENES", "DURATION"):
        if not hasattr(th, name):
            fails.append(f"{name} 상수가 없음")
    scenes = list(getattr(th, "SCENES", []))
    for nm, a, b in scenes:
        if not (0 <= a < b <= D):
            fails.append(f"장면 '{nm}' 구간 {a}~{b}가 0~{D} 밖")

    # 3) 장면별 정지 화면 + 예외
    samples = [(0.0, "start")]
    for nm, a, b in scenes:
        samples += [((a + b) / 2, nm), (b - 0.05, nm + " end")]
    samples.append((D - 1.0 / r.fps, "last"))
    samples = sorted({round(t, 2): n for t, n in samples}.items())
    t0 = time.time()
    try:
        slug = Path(theme_path).stem
        out = Path(__file__).resolve().parent / "out"
        out.mkdir(exist_ok=True)
        sheet(r, samples, out / f"{slug}_check.png")
    except Exception as e:
        print(f"FAIL 렌더 중 예외: {type(e).__name__}: {e}")
        return 1
    per = (time.time() - t0) / len(samples)

    # 4) 같은 t는 같은 그림(상태 없음)
    mid = D * 0.5
    if not np.array_equal(r.frame(mid), r.frame(mid)):
        fails.append("같은 시간의 프레임이 매번 다름 - draw()가 전역 상태를 바꿈")

    # 5) 움직임: 첫 1초 안에 변화가 있어야 하고, 장면 안에 정지가 없어야 한다
    if max(motion(r, t) for t in (0.2, 0.5, 0.9)) < STILL_DIFF:
        fails.append("첫 1초에 움직임이 없음 - 시작부터 무언가 변해야 한다")
    for nm, a, b in scenes:
        m = motion(r, (a + b) / 2)
        if m < STILL_DIFF:
            warns.append(f"장면 '{nm}' 가운데가 거의 정지({m:.4f})")

    # 6) 반복 재생 이음새
    loop = float(np.abs(top(r.frame(0.0)) - top(r.frame(D - 1.0 / r.fps))).mean())
    if loop > LOOP_DIFF:
        warns.append(f"첫/끝 프레임 차이 {loop:.3f} - 반복 재생이 끊겨 보일 수 있음")

    print(f"주제: {getattr(th, 'TITLE', '?')}  길이 {D:.1f}s (최대 {MAX_DURATION:.0f})")
    print(f"장면 {len(scenes)}개, 정지 화면 {len(samples)}장 -> out/{slug}_check.png")
    print(f"프레임당 {per * 1000:.0f}ms, 전체 렌더 예상 {per * D * r.fps:.0f}s")
    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print("결과:", "실패" if fails else "통과")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
