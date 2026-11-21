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


# ---------- 조명 ----------
VIEW = np.array([0.0, 0.0, 1.0])            # 카메라 쪽(+z)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def light(n, t, seed=None, key=(0.0, -0.8, 0.6), rim_speed=0.9,
          ambient=0.12, key_w=0.55, rim_w=0.55, spec_w=0.6,
          glint_rate=3.0, glint_cut=0.45):
    """화면 기준 법선 n(N,3) -> 밝기(N,)와 반짝임 여부(N,).

    주광(key): 위 앞쪽에서 고정. 테두리광(rim): 물체 둘레를 돌며 윤곽을 밝힌다.
    반짝임(glint): 주광 반사(spec)가 센 점이 점마다 다른 박자로 번쩍인다.
    seed: 점마다 고정 난수(N,) - 없으면 법선으로 만든다(같은 점은 같은 박자).
    """
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    k = _unit(key)
    r = _unit([np.cos(t * rim_speed), -0.4, np.sin(t * rim_speed)])
    diff = np.clip(n @ k, 0, 1)
    edge = (1 - np.abs(n[:, 2])) ** 1.5
    rim = np.clip(n @ r, 0, 1) * edge
    h = _unit(k + VIEW)
    spec = np.clip(n @ h, 0, 1) ** 12
    if seed is None:
        seed = (np.abs(np.sin(n @ np.array([12.9, 78.2, 37.7]) * 43758.5))) % 1
    # 밝은 면(반사 + 윤곽)일수록 자주, 점마다 다른 박자로 짧게 번쩍인다
    tw = np.clip(np.sin(t * glint_rate + seed * 6.283), 0, 1) ** 8
    glint = (0.6 * spec + 0.6 * rim + 0.3 * diff) * tw > glint_cut
    lum = ambient + key_w * diff + rim_w * rim + spec_w * spec + 0.6 * glint
    return lum, glint


def splat_reflection(g, P, rgb, lum, floor_y, strength=0.22, depth=0.35, **kw):
    """바닥(y = floor_y)에 비친 흐린 거울상. 본체보다 먼저 그린다.
    depth: 바닥에서 이만큼 멀어지면 반사가 완전히 사라진다."""
    Q = P.copy()
    Q[:, 1] = 2 * floor_y - P[:, 1]
    fall = np.clip(1 - (Q[:, 1] - floor_y) / depth, 0, 1) ** 1.5
    return splat(g, Q, rgb * strength, lum * fall, **kw)


# ---------- 실사 영상 소스 ----------
class Footage:
    """영상/이미지 파일 -> 칸 해상도(108x61) 프레임 묶음. 처음에 한 번 다 읽어 둔다.

    위쪽 화면 비율에 맞게 가운데를 잘라 채운다(cover). start/length로 쓸 구간(초)을 고른다.
    """

    def __init__(self, path, fps=30, start=0.0, length=None):
        path = Path(path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        vf = (f"fps={fps},scale={W}:{TOP_H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{TOP_H},scale={COLS}:{ROWS}:flags=area")
        cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", str(path)]
        if length:
            cmd += ["-t", str(length)]
        cmd += ["-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = len(raw) // (ROWS * COLS * 3)
        if n == 0:
            raise ValueError(f"소스에서 프레임을 읽지 못함: {path}")
        self.frames = np.frombuffer(raw[: n * ROWS * COLS * 3], np.uint8)
        self.frames = self.frames.reshape(n, ROWS, COLS, 3).astype(np.float32) / 255.0
        self.fps = fps

    def at(self, t, loop=True):
        i = int(t * self.fps)
        n = len(self.frames)
        return self.frames[i % n if loop else min(i, n - 1)]


def draw_footage(g, img, gain=1.0, gamma=0.9, floor=0.07, mask=None, alpha=1.0):
    """소스 프레임(ROWS, COLS, 3) -> 칸마다 밝기 계단 글자 + 원본 색.

    floor보다 어두운 칸은 비운다(배경이 보인다). gamma < 1이면 어두운 부분이 살아난다.
    mask(ROWS, COLS)를 주면 그 칸만 그린다(드러남 연출). 반환값은 그린 칸 수.
    """
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    L = np.clip((lum * gain - floor) / (1 - floor), 0, 1) ** gamma
    m = L > 0.02
    if mask is not None:
        m &= mask
    rr, cc = np.nonzero(m)
    if len(rr) == 0:
        return 0
    Lm = L[rr, cc]
    ch = RAMP[(Lm * (len(RAMP) - 1)).astype(int)]
    # 색은 원본 색상을 유지하고 밝기만 다시 매긴다
    base = img[rr, cc] / np.maximum(lum[rr, cc], 1e-3)[:, None]
    col = np.clip(base * (0.25 + 0.95 * Lm)[:, None], 0, 1.6) * alpha
    g._write(rr, cc, ch, col.astype(np.float32))
    return len(rr)


# ---------- 그림 층 (글자 아래에 깔리는 일반 이미지) ----------
PH, PW = TOP_H // 4, W // 4          # 그림 층 계산 해상도(엔진이 확대한다)


def pic_coords(h=PH, w=PW):
    """그림 층 해상도의 화면 좌표 (X: -1..1, Y: 0..1)."""
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    return (X + 0.5) / w * 2 - 1, (Y + 0.5) / h


def upscale(img):
    """그림 층(h, w, 3, 값 0~1)을 위쪽 화면 크기로 부드럽게 확대."""
    img = np.asarray(img, np.float32)
    if img.shape[:2] == (TOP_H, W):
        return img
    u8 = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return np.asarray(u8.resize((W, TOP_H), Image.BILINEAR), np.float32) / 255.0


def vgradient(stops, h=PH, w=PW):
    """세로 그라데이션. stops = [(y, (r, g, b)), ...], y는 0(위)~1(아래)."""
    ys = np.array([y for y, _ in stops], np.float32)
    cs = np.array([c for _, c in stops], np.float32)
    Y = (np.arange(h, dtype=np.float32) + 0.5) / h
    col = np.stack([np.interp(Y, ys, cs[:, k]) for k in range(3)], -1)
    return np.broadcast_to(col[:, None, :], (h, w, 3)).copy()


def noise2d(n=256, beta=2.0, seed=0):
    """이어 붙여도 이음새 없는 1/f^beta 노이즈(n x n). 값은 0~1에 고르게 퍼지도록 순위로 맞춘다.
    beta 2 안팎이면 구름, 3 이상이면 완만한 언덕, 1이면 거친 질감."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    k = np.hypot(*np.meshgrid(f, f))
    k[0, 0] = 1.0
    spec = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) / k ** (beta / 2)
    spec[0, 0] = 0
    img = np.real(np.fft.ifft2(spec))
    rank = np.empty(n * n, np.float32)
    rank[np.argsort(img.ravel())] = np.linspace(0, 1, n * n)
    return rank.reshape(n, n)


def sample(tex, u, v):
    """텍스처를 (u, v) 좌표(1 = 한 바퀴)로 반복해서 읽는다(최근접)."""
    n, m = tex.shape[:2]
    return tex[(np.asarray(v) * n).astype(int) % n, (np.asarray(u) * m).astype(int) % m]


# ---------- 바닥 평면 원근 ----------
def ground(x, z, horizon=0.5, cam=0.25, f=1.0):
    """바닥 위 점(x 옆, z 앞으로 멀어짐, 높이 0) -> 화면 (X, Y, 크기 배율).
    horizon: 지평선 화면 높이(Y), cam: 카메라 높이. 크기 배율 = f / z (z = f일 때 1)."""
    z = np.maximum(np.asarray(z, np.float32), 1e-3)
    s = f / z
    X = np.asarray(x) * s
    Y = horizon + cam * s * (W / 2) / TOP_H
    return X, Y, s


def ground_uv(X, Y, horizon=0.5, cam=0.25, f=1.0):
    """화면 (X, Y) -> 바닥 좌표 (x, z). 지평선 위는 z = inf. 바닥에 텍스처를 입힐 때 쓴다."""
    d = (np.asarray(Y) - horizon) * TOP_H / (W / 2)
    with np.errstate(divide="ignore"):
        z = np.where(d > 0, cam * f / np.maximum(d, 1e-6), np.inf)
    return np.asarray(X) * z / f, z


# ---------- 크기가 다른 글자(스프라이트) ----------
_SPRITE_CACHE = {}


def _glyph(ch, size):
    key = (ch, size)
    if key not in _SPRITE_CACHE:
        font = ImageFont.truetype(MONO_BOLD, size)
        l, tp, r, b = font.getbbox(ch)
        im = Image.new("L", (max(r - l, 1), max(b - tp, 1)), 0)
        ImageDraw.Draw(im).text((-l, -tp), ch, font=font, fill=255)
        _SPRITE_CACHE[key] = np.asarray(im, np.float32) / 255.0
    return _SPRITE_CACHE[key]


def sprite_layer(sp):
    """격자와 상관없이 원하는 위치·크기로 찍는 글자들. 원근(가까울수록 크게)에 쓴다.

    sp = dict(x=화면 X, y=화면 Y, ch=글자 문자열 또는 글자 목록, size=px, rgb=(N, 3))
    겹치면 더 밝은 쪽이 남는다. 빛 번짐은 같이 받는다."""
    out = np.zeros((TOP_H, W, 3), np.float32)
    x = np.asarray(sp["x"], np.float32)
    y = np.asarray(sp["y"], np.float32)
    n = len(x)
    ch = sp["ch"]
    ch = [ch] * n if isinstance(ch, str) and len(ch) == 1 else list(ch)
    size = np.broadcast_to(np.asarray(sp["size"], np.float32), (n,))
    rgb = np.broadcast_to(np.asarray(sp["rgb"], np.float32), (n, 3))
    px = (x * W / 2 + W / 2).astype(int)
    py = (y * TOP_H).astype(int)
    for i in np.argsort(size):              # 작은(먼) 것부터
        sz = int(np.clip(round(size[i]), 6, 96))
        gl = _glyph(ch[i], sz)
        h, w = gl.shape
        x0, y0 = px[i] - w // 2, py[i] - h // 2
        xa, ya = max(x0, 0), max(y0, 0)
        xb, yb = min(x0 + w, W), min(y0 + h, TOP_H)
        if xa >= xb or ya >= yb:
            continue
        patch = gl[ya - y0:yb - y0, xa - x0:xb - x0, None] * rgb[i]
        out[ya:yb, xa:xb] = np.maximum(out[ya:yb, xa:xb], patch)
    return out


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
CURSOR = np.array([1.0, 0.42, 0.62], np.float32)   # 커서, 경과 시간 표시색
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
        self.widths = []
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
            self.widths.append(x)
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
            # 지금 타이핑 중인 것처럼 줄 끝에 깜빡이는 블록 커서
            if hl < self.n and int(t * 2.5) % 2 == 0:
                cx = int(min(self.widths[hl] + 4, W - 16))
                frame[top + 5:top + LINE_H - 5, cx:cx + 13] = CURSOR


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


def draw_hud(img_u8, lines, t=None):
    """위쪽 화면 왼쪽 아래 상태 글자, 오른쪽 위 경과 시간(● t 3.27s)."""
    global _HUD_FONT
    if _HUD_FONT is None:
        _HUD_FONT = ImageFont.truetype(MONO, 30)
    im = Image.fromarray(img_u8)
    d = ImageDraw.Draw(im)
    if t is not None:
        pink = tuple(int(v * 255) for v in CURSOR)
        label = f"t {t:5.2f}s"
        x = W - 24 - _HUD_FONT.getlength(label)
        d.ellipse((x - 26, 30, x - 12, 44), fill=pink)
        d.text((x, 37), label, font=_HUD_FONT, fill=pink, anchor="lm")
    lines = lines or []
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
        if res.get("sprites"):
            top = np.maximum(top, sprite_layer(res["sprites"]))
        top = bloom(top, getattr(self.theme, "GLOW", 0.9))
        if res.get("under") is not None:       # 그림 층은 빛 번짐 없이 맨 아래
            top = top + upscale(res["under"])
        frame = np.zeros((H, W, 3), np.float32)
        frame[:TOP_H] = top
        self.panel.draw(frame, t, self.duration)
        out = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
        clock = t if getattr(self.theme, "SHOW_CLOCK", True) else None
        return draw_hud(out, res.get("hud"), clock)

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
