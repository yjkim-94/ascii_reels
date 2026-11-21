"""아스키 릴스 엔진.

주제 스크립트(themes/*.py)는 draw(g, t)만 구현한다. 엔진은
글자 그리드 -> 이미지 합성, 빛 번짐(glow), HUD, 하단 코드 패널, mp4 인코딩을 맡는다.
모든 프레임은 시간 t만으로 결정된다(상태 없음). 그래서 아무 프레임이나 따로 뽑아 볼 수 있다.
"""
import importlib.util
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- 화면 규격 (인스타 릴스 9:16) ----------
W, H = 1080, 1920
CW, CH = 10, 18                      # 글자 칸 크기(px)
COLS, ROWS = W // CW, 61             # 108 x 61 칸
TOP_H = ROWS * CH                    # 위쪽 렌더 영역 높이 1098px
BAR_H = 62                           # 코드 패널 머리줄
CODE_Y = TOP_H + BAR_H
MAX_DURATION = 15.0                  # 모든 영상은 15초 이내

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
MONO = FONT_DIR + "DejaVuSansMono.ttf"
MONO_BOLD = FONT_DIR + "DejaVuSansMono-Bold.ttf"

# ---------- glyph atlas ----------
CHARS = list(" .,:;*+'`|-/\\_~=#@%&o0O" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "0123456789"
             + "abcdefghijklmnopqrstuvwxyz" + "$!?<>{}[]()^\"")
CHARS = list(dict.fromkeys(CHARS))   # 중복 제거, 순서 유지
CIDX = {c: i for i, c in enumerate(CHARS)}


def _build_atlas():
    font = ImageFont.truetype(MONO_BOLD, 15)
    atlas = np.zeros((len(CHARS), CH, CW), np.float32)
    for i, c in enumerate(CHARS):
        im = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(im).text((0, 0), c, font=font, fill=255)
        atlas[i] = np.asarray(im, np.float32) / 255.0
    return atlas


ATLAS = _build_atlas()


def _build_ramp(n=28):
    """잉크 면적(글자가 칸을 채우는 비율) 순으로 고른 밝기 계단. 0번은 가장 옅은 '.'."""
    cover = ATLAS.mean(axis=(1, 2))
    order = [i for i in np.argsort(cover) if CHARS[i] != " " and CHARS[i] != "_"]
    pick = np.linspace(0, len(order) - 1, n).round().astype(int)
    return np.array([order[i] for i in pick], np.int32)


RAMP = _build_ramp()


def idx(s):
    """문자열 -> 글자 번호 배열. 아틀라스에 없는 글자는 공백."""
    return np.array([CIDX.get(c, 0) for c in s], np.int32)


# ---------- 시간 도우미 ----------
def ramp(t, a, b):
    """구간 (a, b)에서 0 -> 1."""
    return float(np.clip((t - a) / (b - a), 0.0, 1.0))


def ease(x):
    """ease-out cubic: 빠르게 시작해서 부드럽게 멈춘다."""
    return 1.0 - (1.0 - x) ** 3


def smooth(x):
    """smoothstep: 천천히 시작해 천천히 멈춘다. 자라는 장면처럼 고르게 보여야 할 때."""
    return x * x * (3.0 - 2.0 * x)


def pop(x):
    """살짝 넘쳤다 돌아오는 back-out. 튀어나오는 장식에 쓴다."""
    s = 1.70158
    x = x - 1.0
    return 1.0 + (s + 1) * x ** 3 + s * x ** 2


# ---------- 글자 그리드 ----------
class Grid:
    """위쪽 화면의 글자 칸. 칸마다 글자 번호와 RGB(0~1, 1 넘으면 더 밝게 번짐)를 가진다."""

    def __init__(self):
        self.ch = np.zeros((ROWS, COLS), np.int32)
        self.col = np.zeros((ROWS, COLS, 3), np.float32)
        r, c = np.mgrid[0:ROWS, 0:COLS]
        self.r, self.c = r, c
        # 정규화 좌표: X는 가운데 0, 좌우 -1..1 / Y는 위 0, 아래 1 (픽셀 비율 유지)
        self.X = ((c + 0.5) * CW - W / 2) / (W / 2)
        self.Y = (r + 0.5) * CH / TOP_H

    def _write(self, rr, cc, chars, colors):
        """이미 있는 글자보다 어두운 글자는 덮지 않는다(밝기 최댓값 합성).
        사라지는 물체가 배경을 검게 가리지 않고, 페이드 때 배경이 자연스럽게 드러난다."""
        old = self.col[rr, cc].max(-1)
        new = colors.max(-1)
        m = new >= old
        self.ch[rr[m], cc[m]] = chars[m]
        self.col[rr[m], cc[m]] = colors[m]

    def put(self, mask, chars, color, alpha=1.0):
        """mask 칸에 글자와 색을 쓴다. chars/color는 하나 또는 mask 개수만큼."""
        rr, cc = np.nonzero(mask)
        if len(rr) == 0:
            return
        chars = np.broadcast_to(np.asarray(chars), rr.shape)
        colors = np.broadcast_to(np.asarray(color, np.float32) * alpha, rr.shape + (3,))
        self._write(rr, cc, chars, colors)

    def put_cells(self, rr, cc, chars, colors):
        """흩어진 점(행, 열 배열)을 찍는다. 화면 밖 점은 버린다."""
        rr, cc = np.asarray(rr, int), np.asarray(cc, int)
        ok = (rr >= 0) & (rr < ROWS) & (cc >= 0) & (cc < COLS)
        chars = np.broadcast_to(np.asarray(chars), rr.shape)[ok]
        colors = np.broadcast_to(np.asarray(colors, np.float32), rr.shape + (3,))[ok]
        self._write(rr[ok], cc[ok], chars, colors)

    def text(self, row, col, s, color):
        cc = col + np.arange(len(s))
        self.put_cells(np.full(len(s), row), cc, idx(s), color)

    def to_cell(self, x, y):
        """정규화 좌표 -> (행, 열)."""
        cc = np.floor((np.asarray(x) * (W / 2) + W / 2) / CW).astype(int)
        rr = np.floor(np.asarray(y) * TOP_H / CH).astype(int)
        return rr, cc


# ---------- 3D 점 구름 ----------
def rot_y(P, a):
    """세로축 회전. P: (N, 3) = (x 오른쪽, y 아래, z 화면 앞쪽)."""
    c, s = np.cos(a), np.sin(a)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return np.stack([c * x + s * z, y, -s * x + c * z], -1)


def rot_x(P, a):
    """가로축 회전(앞으로 숙이기)."""
    c, s = np.cos(a), np.sin(a)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return np.stack([x, c * y - s * z, s * y + c * z], -1)


def dir_chars(dx, dy):
    """화면에서 선이 뻗는 방향 -> | / \\ - 글자. 촉수, 빛줄기 같은 선에 쓴다."""
    a = np.degrees(np.arctan2(dy, dx)) % 180
    return np.select([(a < 22.5) | (a >= 157.5), a < 67.5, a < 112.5],
                     [CIDX["-"], CIDX["\\"], CIDX["|"]], CIDX["/"])


def splat(g, P, rgb, lum, chars=None, cy=0.5, scale=1.0, f=3.2):
    """3D 점 -> 원근 투영 -> 칸마다 가장 앞 점 하나(z-buffer) -> 밝기로 글자 선택.

    P: (N, 3), rgb: (N, 3), lum: (N,) 0~1.
    chars: (N,) 글자 번호, -1이면 밝기 계단 사용. 반환값은 실제로 찍힌 칸 수.
    """
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    k = f / np.maximum(f - z, 0.2) * scale
    # x는 화면 폭 절반 = 1, y도 같은 픽셀 길이가 되게 맞춘다
    rr, cc = g.to_cell(x * k, cy + y * k * (W / 2) / TOP_H)
    ok = (rr >= 0) & (rr < ROWS) & (cc >= 0) & (cc < COLS) & (lum > 0.02)
    if not np.any(ok):
        return 0
    ids = np.nonzero(ok)[0]
    key = rr[ids] * COLS + cc[ids]
    order = np.lexsort((-z[ids], key))           # 칸별로 가장 앞(z 큰) 점이 먼저
    key = key[order]
    first = np.r_[True, key[1:] != key[:-1]]
    sel = ids[order[first]]
    L = np.clip(lum[sel], 0, 1)
    ch = RAMP[(L * (len(RAMP) - 1)).astype(int)]
    if chars is not None:
        own = np.asarray(chars)[sel]
        ch = np.where(own >= 0, own, ch)
    g._write(rr[sel], cc[sel], ch, (rgb[sel] * (0.35 + 0.9 * L)[:, None]).astype(np.float32))
    return len(sel)


# ---------- 배경 도우미 ----------
class LetterRain:
    """화면 전체에 흐리게 깔리는 글자. 열마다 다른 속도로 천천히 내려온다."""

    def __init__(self, rng, density=0.55):
        letters = idx("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.base = letters[rng.integers(0, 26, (ROWS * 3, COLS))]
        self.on = rng.random((ROWS * 3, COLS)) < density
        self.speed = rng.uniform(0.4, 1.6, COLS)
        self.phase = rng.uniform(0, 6.28, (ROWS, COLS))

    def draw(self, g, t, color, flicker=0.35):
        off = (t * self.speed).astype(int)
        rows = (g.r - off[None, :]) % self.base.shape[0]
        ch = self.base[rows, g.c]
        on = self.on[rows, g.c]
        lvl = 1.0 - flicker + flicker * np.sin(t * 2.0 + self.phase)
        g.ch[on] = ch[on]
        g.col[on] = np.asarray(color, np.float32) * lvl[on][:, None]


class Snow:
    """시간만으로 위치가 정해지는 눈송이(반복 재생해도 이어진다)."""

    def __init__(self, rng, n=260):
        self.x0 = rng.uniform(-1, 1, n)
        self.y0 = rng.uniform(0, 1, n)
        self.v = rng.uniform(0.025, 0.08, n)
        self.sway = rng.uniform(0.005, 0.02, n)
        self.ph = rng.uniform(0, 6.28, n)
        self.size = rng.random(n)

    def draw(self, g, t, brightness=1.0, which=slice(None)):
        y = (self.y0 + self.v * t) % 1.0
        x = self.x0 + self.sway * np.sin(t * 1.3 + self.ph)
        rr, cc = g.to_cell(x, y)
        s = self.size
        chars = np.where(s > 0.8, CIDX["*"], np.where(s > 0.45, CIDX["+"], CIDX["."]))
        lvl = (0.45 + 0.55 * s) * brightness
        colors = np.stack([lvl * 0.92, lvl * 0.95, lvl * 1.0], -1)
        g.put_cells(rr[which], cc[which], chars[which], colors[which])


# ---------- 이미지 합성 ----------
def compose(g):
    glyph = ATLAS[g.ch]                                     # (R, C, CH, CW)
    img = glyph[..., None] * g.col[:, :, None, None, :]     # (R, C, CH, CW, 3)
    return img.transpose(0, 2, 1, 3, 4).reshape(TOP_H, W, 3)


def bloom(img, strength=0.9):
    """밝은 글자 주변으로 빛이 번지는 효과. 감성 톤의 핵심."""
    lo = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    small = lo.resize((W // 4, TOP_H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    glow = np.asarray(small.resize((W, TOP_H), Image.BILINEAR), np.float32) / 255.0
    return img + strength * glow


# ---------- 코드 패널 ----------
CODE_FONT = 24
LINE_H = 36
GUTTER = 64
CODE_COLORS = {
    "kw": (198, 120, 221), "func": (97, 175, 239), "str": (152, 195, 121),
    "num": (209, 154, 102), "com": (106, 115, 125), "const": (86, 182, 194),
    "builtin": (229, 192, 123), "op": (171, 178, 191), "text": (220, 223, 228),
}


def _token_color(ttype, value):
    from pygments.token import Comment, Keyword, Name, Number, Operator, String
    if ttype in Comment:
        return CODE_COLORS["com"]
    if ttype in Keyword:
        return CODE_COLORS["kw"]
    if ttype in String:
        return CODE_COLORS["str"]
    if ttype in Number:
        return CODE_COLORS["num"]
    if ttype in Name.Function or ttype in Name.Class:
        return CODE_COLORS["func"]
    if ttype in Name.Builtin:
        return CODE_COLORS["builtin"]
    if ttype in Name and value.isupper() and len(value) > 1:
        return CODE_COLORS["const"]
    if ttype in Operator:
        return CODE_COLORS["op"]
    return CODE_COLORS["text"]


def _highlight(lines):
    """줄마다 [(글자들, 색)] 목록. pygments가 없으면 단색."""
    try:
        from pygments.lexers import PythonLexer
    except ImportError:
        return [[(ln, CODE_COLORS["text"])] for ln in lines]
    out, cur = [], []
    for ttype, value in PythonLexer(stripnl=False).get_tokens("\n".join(lines)):
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                out.append(cur)
                cur = []
            if part:
                cur.append((part, _token_color(ttype, part)))
    out.append(cur)
    return out[: len(lines)]


class CodePanel:
    """주제 스크립트 소스를 미리 긴 이미지 한 장으로 그려 두고, 프레임마다 잘라 쓴다."""

    def __init__(self, source, filename, fps):
        self.filename, self.fps = filename, fps
        lines = source.rstrip("\n").split("\n")
        self.n = len(lines)
        font = ImageFont.truetype(MONO, CODE_FONT)
        small = ImageFont.truetype(MONO, 20)
        sheet = Image.new("RGB", (W, (self.n + 30) * LINE_H), (22, 24, 29))
        d = ImageDraw.Draw(sheet)
        for i, segs in enumerate(_highlight(lines)):
            y = i * LINE_H + 4
            d.text((GUTTER - 14, y + 4), f"{i + 1}", font=small, fill=(78, 84, 96), anchor="ra")
            x = GUTTER
            for text, color in segs:
                d.text((x, y), text, font=font, fill=color)
                x += font.getlength(text)
        self.sheet = np.asarray(sheet, np.float32) / 255.0
        self.visible = (H - CODE_Y) // LINE_H

        bar = Image.new("RGB", (W, BAR_H), (30, 32, 38))
        bd = ImageDraw.Draw(bar)
        bfont = ImageFont.truetype(MONO, 26)
        bd.text((24, BAR_H // 2), filename, font=bfont, fill=(205, 208, 214), anchor="lm")
        status = f"running · {fps} fps"
        sx = W - 24 - bfont.getlength(status)
        bd.ellipse((sx - 30, BAR_H // 2 - 8, sx - 14, BAR_H // 2 + 8), fill=(63, 185, 80))
        bd.text((sx, BAR_H // 2), status, font=bfont, fill=(150, 156, 166), anchor="lm")
        self.bar = np.asarray(bar, np.float32) / 255.0

    def draw(self, frame, t, duration):
        # 영상 길이의 92% 동안 파일 끝까지 부드럽게 내려간다
        span = max(self.n - self.visible + 4, 0)
        span = min(span, duration * 6.0)        # 초당 6줄을 넘지 않게
        s = span * ease(min(t / (duration * 0.92), 1.0) ** 1.15)
        y0 = int(s * LINE_H)
        h = H - CODE_Y
        frame[TOP_H:CODE_Y] = self.bar
        frame[CODE_Y:] = self.sheet[y0:y0 + h]
        # 현재 실행 중인 줄처럼 보이는 강조 띠
        hl = int(s) + 6
        top = CODE_Y + hl * LINE_H - y0
        if CODE_Y <= top < H - LINE_H:
            frame[top:top + LINE_H] += np.array([0.05, 0.06, 0.09], np.float32)


# ---------- 큰 글씨 자막 ----------
_CAP_FONT = None


def caption_layer(text, shown, y, color, size=46, spacing=0.35, cursor=False):
    """위쪽 화면 y(0~1) 높이에 자간을 넓힌 큰 글씨.
    text 전체 길이로 가운데 자리를 잡고 앞 shown 글자만 그린다(타이핑 효과).
    그리드 밖에 그리지만 빛 번짐은 같이 받는다."""
    global _CAP_FONT
    if _CAP_FONT is None or _CAP_FONT.size != size:
        _CAP_FONT = ImageFont.truetype(MONO_BOLD, size)
    adv = _CAP_FONT.getlength("M") * (1 + spacing)
    x0 = (W - adv * len(text) + adv * spacing / (1 + spacing)) / 2
    im = Image.new("L", (W, TOP_H), 0)
    d = ImageDraw.Draw(im)
    body = text[:shown] + ("_" if cursor and shown < len(text) else "")
    for i, c in enumerate(body):
        d.text((x0 + i * adv, y * TOP_H), c, font=_CAP_FONT, fill=255, anchor="lm")
    a = np.asarray(im, np.float32)[..., None] / 255.0
    return a * np.asarray(color, np.float32)


# ---------- HUD ----------
_HUD_FONT = None


def draw_hud(img_u8, lines):
    """위쪽 화면 왼쪽 아래에 상태 글자(손잡이, 회전각, 전구 수 등)를 얹는다."""
    global _HUD_FONT
    if not lines:
        return img_u8
    if _HUD_FONT is None:
        _HUD_FONT = ImageFont.truetype(MONO, 30)
    im = Image.fromarray(img_u8)
    d = ImageDraw.Draw(im)
    y = TOP_H - 22 - len(lines) * 40
    for ln in lines:
        d.text((22, y), ln, font=_HUD_FONT, fill=(232, 234, 238))
        y += 40
    return np.asarray(im)


# ---------- 렌더링 ----------
def load_theme(path):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path.read_text(encoding="utf-8"), path.name


class Renderer:
    def __init__(self, theme_path, fps=30):
        self.theme, src, name = load_theme(theme_path)
        self.fps = fps
        self.duration = float(getattr(self.theme, "DURATION", MAX_DURATION))
        if self.duration > MAX_DURATION:
            raise ValueError(f"DURATION {self.duration}s > {MAX_DURATION}s 제한")
        self.panel = CodePanel(src, name, fps)
        self.grid = Grid()

    def frame(self, t):
        g = self.grid
        g.ch[:] = 0
        g.col[:] = 0
        res = self.theme.draw(g, t)
        if not isinstance(res, dict):          # 목록만 돌려주면 HUD로 본다
            res = {"hud": res}
        top = compose(g)
        if res.get("caption"):
            top += caption_layer(*res["caption"])
        top = bloom(top, getattr(self.theme, "GLOW", 0.9))
        frame = np.zeros((H, W, 3), np.float32)
        frame[:TOP_H] = top
        self.panel.draw(frame, t, self.duration)
        out = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
        return draw_hud(out, res.get("hud"))

    def still(self, t, path):
        Image.fromarray(self.frame(t)).save(path)

    def video(self, out_path, seconds=None, progress=True):
        seconds = min(seconds or self.duration, self.duration)
        n = int(round(seconds * self.fps))
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(self.fps), "-i", "-",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(out_path),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            proc.stdin.write(self.frame(i / self.fps).tobytes())
            if progress and (i % self.fps == 0 or i == n - 1):
                print(f"\r{i + 1}/{n} frames", end="", flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg 인코딩 실패")
        if progress:
            print()
