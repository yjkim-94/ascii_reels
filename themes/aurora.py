"""aurora: stars wake, curtains grow, then a substorm erupts."""
import numpy as np
from engine import (CIDX, dir_chars, ease, noise2d, pic_coords, ramp,
                    smooth, vgradient)

TITLE = "Aurora"
HANDLE = "@justmade.lab"
DURATION = 18.0
GLOW = 1.0
rng = np.random.default_rng(41)

# ---------- timeline (seconds) ----------
T_METEOR = (0.0, 1.2)     # a shooting star lights the first stars
T_REVEAL = (1.0, 4.0)     # sky, forest and lake appear
T_BANDS = [4.0, 7.0, 8.0, 9.0, 10.0]   # each aurora band is born
T_CALM = (11.0, 12.0)     # the curtains dim and hold their breath
T_WAVE = (12.0, 12.8)     # a pulse runs along the bands, left->right
T_STORM = (12.8, 15.0)    # substorm: folds, tall rays, pink hems
T_SETTLE = (15.0, 16.5)   # it slows down into soft green
T_FADE = (16.5, 18.0)     # aurora, land, then stars fade to black
SCENES = [("meteor", 0.0, 1.5), ("landscape", *T_REVEAL),
          ("first band", 4.0, 7.0), ("more bands", 7.0, 11.0),
          ("calm", *T_CALM), ("light wave", *T_WAVE),
          ("substorm", *T_STORM), ("afterglow", *T_SETTLE),
          ("fade", *T_FADE)]
POSTER_T = 14.2

# ---------- layout (screen: X -1..1, Y 0 top .. 1 bottom) ----------
HORIZON = 0.60            # tree line / far shore
MIRROR = 0.612            # lake reflects the sky about this line
LAKE_END = 0.86
ASPECT = 1098 / 540

GREEN_EDGE = np.array([0.35, 1.00, 0.60])
GREEN = np.array([0.10, 0.80, 0.45])
VIOLET = np.array([0.60, 0.30, 0.95])
PINK = np.array([1.00, 0.40, 0.70])
WHITE = np.array([0.90, 1.00, 0.95])
STAR = np.array([0.85, 0.90, 1.00])
ICE = np.array([0.05, 0.10, 0.18])

# five bands: base height, wave amplitude, frequency, phase, height
B_BASE = np.array([0.50, 0.42, 0.35, 0.28, 0.21])
B_AMP = np.array([0.030, 0.040, 0.045, 0.050, 0.040])
B_FREQ = np.array([2.2, 1.7, 2.6, 1.9, 2.4])
B_PH = rng.uniform(0, 2 * np.pi, 5)
B_H = np.array([0.10, 0.13, 0.15, 0.16, 0.14])
RAYS = noise2d(256, beta=1.3, seed=8)
MILKY = noise2d(256, beta=2.2, seed=9)
RIPPLE = noise2d(128, beta=1.6, seed=10)

PX, PY = pic_coords()
SKY = vgradient([(0.0, (0.01, 0.02, 0.06)), (HORIZON, (0.04, 0.07,
                                                        0.16)),
                 (HORIZON, ICE), (1.0, (0.01, 0.02, 0.04))])

# forest: pine triangles along the horizon
N_TREE = 70
TR_X = np.sort(rng.uniform(-1.05, 1.05, N_TREE))
TR_H = rng.uniform(0.025, 0.085, N_TREE)
TR_W = TR_H * rng.uniform(0.35, 0.5, N_TREE)

# stars: the first 60 hug the meteor path, the rest fill the sky
N_STAR = 400
MET_A = np.array([-0.95, 0.20])
MET_B = np.array([0.85, 0.48])
_s = rng.uniform(0, 1, 60)
ST_X = np.concatenate([MET_A[0] + (MET_B[0] - MET_A[0]) * _s
                       + rng.normal(0, 0.06, 60),
                       rng.uniform(-1, 1, N_STAR - 60)])
ST_Y = np.concatenate([MET_A[1] + (MET_B[1] - MET_A[1]) * _s
                       + rng.normal(0, 0.03, 60),
                       rng.uniform(0.0, HORIZON - 0.06, N_STAR - 60)])
ST_ON = np.concatenate([T_METEOR[0] + _s * 1.2,
                        rng.uniform(1.4, 3.6, N_STAR - 60)])
ST_PH = rng.uniform(0, 2 * np.pi, N_STAR)

# storm level over time and its running integral (faster motion)
_TT = np.linspace(0, DURATION, 2000)
_G = smooth(np.clip((_TT - 12.5) / 0.7, 0, 1)) \
    * (1 - smooth(np.clip((_TT - T_SETTLE[0]) / 1.5, 0, 1)))
_GI = np.concatenate([[0], np.cumsum((_G[1:] + _G[:-1]) / 2
                                     * np.diff(_TT))])


def storm(t):
    """global storm level and its integral up to t."""
    return float(np.interp(t, _TT, _G)), float(np.interp(t, _TT, _GI))


def aurora(X, Y, t):
    """aurora light at screen points: (intensity, rgb)."""
    A = np.zeros_like(X)
    C = np.zeros(X.shape + (3,))
    kv = smooth(ramp(t, 7.0, 11.0))            # violet tops grow
    calm = 1 - 0.3 * smooth(ramp(t, 11.0, 11.5)) \
        * (1 - smooth(ramp(t, *T_WAVE)))
    G, GI = storm(t)
    xw = -1.3 + 2.8 * ramp(t, *T_WAVE)         # light wave front
    awake = smooth(np.clip((xw - X) / 0.4, 0, 1)) \
        * (t >= T_WAVE[0]) * (1 - smooth(ramp(t, 15.0, 16.5)))
    pulse = np.exp(-((X - xw) / 0.12) ** 2) * (0 < ramp(t, *T_WAVE) < 1)
    S = awake * smooth(ramp(t, 12.3, 13.3))     # storm where awake
    phase = 0.7 * t + 2.2 * GI                 # faster when stormy
    drift = 0.03 * t + 0.12 * GI
    for b in range(5):
        a = smooth(ramp(t, T_BANDS[b], T_BANDS[b] + 1.5))
        if a <= 0:
            continue
        base = B_BASE[b] + (0.08 if b == 0 else 0.0) \
            * (1 - smooth(ramp(t, 4.0, 7.0)))   # first band rises
        y0 = base + B_AMP[b] * np.sin(B_FREQ[b] * X + phase + B_PH[b]) \
            + 0.012 * np.sin(5.3 * X - 1.6 * phase + b)
        # substorm folds: tighter S-curls that roll along the band
        y0 = y0 + S * 0.045 * np.sin(4.2 * X + 2.4 * phase + b * 1.7)
        hgt = y0 - Y                           # height above the edge
        u = (X * 0.35 + drift * (1 + b % 2) + b * 0.2) % 1.0
        ray = RAYS[(b * 37) % 256, (u * 256).astype(int)]
        ray = 0.35 + 0.65 * np.clip((ray - 0.25) / 0.6, 0, 1) ** 1.5
        tall = B_H[b] * (1 + 1.8 * S)          # rays reach the top
        curtain = np.where(hgt >= 0, np.exp(-hgt / tall),
                           np.exp(hgt / 0.006))
        side = np.clip(1.15 - np.abs(X) * 0.5, 0, 1)
        I = a * curtain * ray * side * (0.55 + 0.1 * b) * calm \
            * (1 + 0.7 * S + 1.2 * pulse)
        edge = np.exp(-np.clip(hgt, 0, None) / 0.035)[..., None]
        top = (1 - edge) * (0.35 + 0.65 * kv)
        col = GREEN_EDGE * edge + GREEN * (1 - edge) * (1 - top) \
            + VIOLET * top
        hem = (S * 0.85)[..., None] * edge     # pink lower hems
        col = col + (PINK - col) * hem
        col = col + (WHITE - col) * (0.6 * pulse)[..., None]
        C += col * I[..., None]
        A += I
    return A, C


def camera(t):
    keys = [(0.0, 1.25, 0.0, 0.68), (1.0, 1.25, 0.0, 0.68),
            (4.0, 1.0, 0.0, 0.60), (11.0, 1.08, 0.0, 0.30),
            (12.0, 1.08, -0.25, 0.32), (12.8, 1.08, 0.25, 0.32),
            (14.2, 1.0, 0.0, 0.30), (15.0, 1.0, 0.0, 0.30),
            (16.5, 1.05, 0.0, 0.30), (18.0, 1.25, 0.0, 0.68)]
    i = max(j for j in range(len(keys)) if keys[j][0] <= t)
    k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
    u = smooth(ramp(t, k0[0], k1[0])) if k1[0] > k0[0] else 0.0
    z, fx, fy = (a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
    return dict(zoom=z, focus=(fx, fy))


def meteor(g, a, b, k, bright, tail=0.18, width=1):
    """a shooting star at progress k from a to b, with a tail."""
    n = 30
    s = np.linspace(max(k - tail, 0), k, n)
    X = a[0] + (b[0] - a[0]) * s
    Y = a[1] + (b[1] - a[1]) * s
    ch = dir_chars(np.full(n, b[0] - a[0]),
                   np.full(n, (b[1] - a[1]) * ASPECT))
    lum = np.linspace(0.1, 1.0, n) ** 2 * bright
    for off in range(-width + 1, width):        # thicker trail
        rr, cc = g.to_cell(X, Y + off * 0.017)
        g.put_cells(rr, cc, ch,
                    STAR[None] * 1.6 * (lum * (1 - 0.4 * abs(off)))
                    [:, None])
    rr, cc = g.to_cell(X[-1:], Y[-1:])
    g.put_cells(rr, cc, CIDX["@"], (STAR * 2.0 * bright)[None])
    return X[-1], Y[-1]


def draw(g, t):
    f_aur = 1 - ease(ramp(t, 16.5, 17.3))      # staged fade-out
    f_land = 1 - ease(ramp(t, 17.0, 17.6))
    f_star = 1 - ease(ramp(t, 17.3, 18.0))
    reveal = smooth(ramp(t, *T_REVEAL))

    # ================= picture layer =================
    sky = SKY * (reveal * f_land)
    mw = MILKY[(PY * 200).astype(int) % 256,
               ((PX * 0.6 + PY * 0.9) * 256).astype(int) % 256]
    band = np.exp(-((PX * 0.5 + PY - 0.32) / 0.12) ** 2)
    sky = sky + (np.clip(mw - 0.5, 0, 1) * band * 0.12 * reveal
                 * f_star)[..., None] * STAR
    A, C = aurora(PX, PY, t)
    sky = sky + C * (0.55 * f_aur) * (PY < HORIZON)[..., None]
    if t < T_METEOR[1] + 0.2:                  # meteor glow
        k = ramp(t, *T_METEOR)
        mx = MET_A[0] + (MET_B[0] - MET_A[0]) * k
        my = MET_A[1] + (MET_B[1] - MET_A[1]) * k
        dd = np.hypot(PX - mx, (PY - my) * ASPECT)
        sky = sky + (0.7 * np.exp(-dd / 0.07) * (k < 1))[..., None]
    # forest silhouette
    trees = np.zeros_like(PX, bool)
    for x, h, w in zip(TR_X, TR_H, TR_W):
        trees |= (PY < HORIZON + 0.004) \
            & (PY > HORIZON - h * (1 - np.abs(PX - x) / w))
    sky[trees] = np.array([0.008, 0.012, 0.025]) * (0.5 + 0.5
                                                    * reveal)
    # lake: the sky flipped about the mirror line, rippled and dimmed
    h, w = PY.shape
    rows = np.arange(h)
    src = np.clip(((2 * MIRROR - PY[:, 0]) * h).astype(int), 0, h - 1)
    lake = PY[:, 0] > MIRROR
    rip = RIPPLE[(rows * 3) % 128][:, (np.arange(w) * 2) % 128]
    shift = ((rip - 0.5) * 6 * (PY - MIRROR) * 10).astype(int)
    cols = (np.arange(w)[None, :] + shift) % w
    refl = sky[src[:, None], cols]
    lake_img = SKY * (reveal * f_land) + refl * 0.45
    under = np.where(lake[:, None, None], lake_img, sky)

    # ============= grid: stars, meteors, aurora rays =============
    tw = 0.35 + 0.65 * np.clip(np.sin((2 + 3 * smooth(ramp(
        t, *T_CALM))) * t + ST_PH), 0, 1) ** 2
    on = (t >= ST_ON)
    pop_ = 1 + 1.5 * np.exp(-np.clip(t - ST_ON, 0, None) / 0.15)
    sl = np.clip((t - ST_ON) / 0.1, 0, 1) * tw * f_star * on * pop_
    rr, cc = g.to_cell(ST_X, ST_Y)
    sch = np.where(tw > 0.85, CIDX["*"],
                   np.where(tw > 0.55, CIDX["+"], CIDX["."]))
    g.put_cells(rr, cc, sch, STAR[None] * sl[:, None])
    n_stars = int(on.sum())
    if t < T_METEOR[1]:
        meteor(g, MET_A, MET_B, ease(ramp(t, *T_METEOR)), 1.2,
               tail=0.35, width=2)

    A_g, C_g = aurora(g.X, g.Y, t)             # rays as letters
    sky_cells = g.Y < HORIZON - 0.01
    m = sky_cells & (A_g > 0.12)
    ch = np.where(A_g > 0.55, CIDX["|"],
                  np.where(A_g > 0.28, CIDX[":"], CIDX["."]))
    g.put(m, ch[m], (C_g / np.maximum(A_g, 1e-6)[..., None]
                     * np.clip(A_g, 0, 1.3)[..., None])[m] * f_aur)
    # their reflection on the ice, as flat water strokes
    lake_cells = (g.Y > MIRROR + 0.01) & (g.Y < LAKE_END)
    Ar, Cr = aurora(g.X, 2 * MIRROR - g.Y, t)
    m = lake_cells & (Ar > 0.2)
    rch = np.where(np.sin(g.c * 0.9 + g.r * 2.3 + 2 * t) > 0,
                   CIDX["-"], CIDX["~"])
    g.put(m, rch[m], (Cr / np.maximum(Ar, 1e-6)[..., None]
                      * np.clip(Ar, 0, 1)[..., None])[m]
          * 0.5 * f_aur * f_land)
    # stars mirrored in the lake, stretched a little by the ripples
    ry = 2 * MIRROR - ST_Y
    inl = (ry > MIRROR + 0.008) & (ry < LAKE_END) & on
    if inl.any():
        sh = 0.006 * np.sin(3 * t + ST_PH[inl] * 4)
        rl = sl[inl] * 0.5 * f_land
        for k, w in ((0, 1.0), (1, 0.45)):
            rr, cc = g.to_cell(ST_X[inl] + sh, ry[inl] + k * 0.017)
            g.put_cells(rr, cc, np.where(rl > 0.4, CIDX["+"],
                                         CIDX["."]),
                        STAR[None] * (rl * w)[:, None])

    bands = sum(t >= T_BANDS[b] + 0.75 for b in range(5))
    kp = 1 + 2 * ramp(t, 4.0, 7.0) + 3 * ramp(t, 7.0, 11.0) \
        + 2 * ramp(t, *T_WAVE) + ramp(t, 12.8, 13.3)
    n_lit = int((g.col.max(-1) > 0.05).sum())
    return {"under": np.clip(under, 0, 1), "camera": camera(t),
            "hud": [HANDLE,
                    f"stars {n_stars}   bands {bands}   kp {kp:.0f}",
                    f"letters {n_lit:,}"]}
