"""forest_goddess: flowers rise where she steps; the tree wakes."""
import numpy as np
from engine import (CIDX, dir_chars, ease, noise2d, pic_coords, pop,
                    ramp, smooth, vgradient)

TITLE = "Forest Goddess"
HANDLE = "@justmade.lab"
DURATION = 18.0
GLOW = 1.0
rng = np.random.default_rng(51)

# ---------- timeline (seconds) ----------
STEPS = [0.2, 2.6, 3.8, 5.0, 6.2, 7.4, 8.6]   # a foot lands
T_REVEAL = (0.0, 3.5)     # the dusk forest and the dead tree appear
T_WALK = (1.6, 9.5)       # she walks to the tree
T_REACH = (9.5, 10.6)     # she stops, reaches out, touches the bark
T_TOUCH = 10.6            # green light runs up into every branch
T_WAKE = (10.6, 13.0)     # leaves burst from every branch tip
T_FADE = (16.5, 18.0)     # dusk falls back to dark, then loop
SCENES = [("first footprint", 0.0, 1.2), ("reveal", 1.0, 3.5),
          ("walk", 3.5, 9.5), ("reach", *T_REACH),
          ("tree wakes", *T_WAKE), ("afterglow", 13.0, 16.5),
          ("fade", *T_FADE)]
POSTER_T = 14.0

# ---------- layout (screen: X -1..1, Y 0 top .. 1 bottom) ----------
GROUND = 0.78
ASPECT = 1098 / 540
FIG_H = 0.40              # her height in screen Y units
FX = FIG_H * ASPECT       # 1 height-fraction across, in X units
X_START, X_END = -0.72, 0.16
TREE_X = 0.42
TOUCH = (0.36, 0.60)      # where her hand meets the bark

SKY_TOP = (0.10, 0.08, 0.12)
SKY_LOW = (0.45, 0.30, 0.22)
BARK = np.array([0.35, 0.30, 0.26])
BARK_ALIVE = np.array([0.45, 0.38, 0.22])
EMERALD = np.array([0.20, 0.90, 0.55])
MINT = np.array([0.55, 1.00, 0.75])
DRESS = np.array([0.10, 0.65, 0.40])
HEM = np.array([0.40, 0.90, 0.60])
SKIN = np.array([0.95, 0.90, 0.85])
FLOWER_C = np.array([[1.00, 0.55, 0.75], [1.00, 0.97, 0.90],
                     [1.00, 0.85, 0.35]])
LEAF_C = np.array([[0.30, 0.85, 0.35], [0.55, 0.95, 0.40],
                   [1.00, 0.85, 0.40]])
STEM = np.array([0.20, 0.50, 0.25])


def walk_x(t):
    """her position along the path."""
    return X_START + (X_END - X_START) * smooth(ramp(t, *T_WALK))


# ---------- the tree: recursive branches (X units, y up) ----------
SEGS = []                 # x0, y0, x1, y1, depth, path length at end


def grow(x, y, ang, ln, depth, path):
    x1, y1 = x + ln * np.cos(ang), y + ln * np.sin(ang)
    SEGS.append((x, y, x1, y1, depth, path + ln))
    if depth >= 7:
        return
    for s in (-1, 1):
        da = s * rng.uniform(0.28, 0.6)
        grow(x1, y1, ang + da, ln * rng.uniform(0.66, 0.8), depth + 1,
             path + ln)
    if depth < 3 and rng.random() < 0.6:          # extra side twig
        grow(x1, y1, ang + rng.normal(0, 0.9), ln * 0.55, depth + 2,
             path + ln)


grow(TREE_X, 0.0, np.pi / 2 + 0.05, 0.42, 0, 0.0)
SEGS = np.array(SEGS)
MAXPATH = SEGS[:, 5].max()
TIPS = SEGS[SEGS[:, 4] >= 4][:, [2, 3, 5]]     # tips and inner twigs


def to_screen(x, y_up):
    return x, GROUND - y_up / ASPECT


# segment samples for drawing
SEG_PTS = []
for x0, y0, x1, y1, d, pl in SEGS:
    n = max(int(np.hypot(x1 - x0, y1 - y0) / 0.008), 2)
    s = np.linspace(0, 1, n)
    xs, ys = x0 + (x1 - x0) * s, y0 + (y1 - y0) * s
    path = pl - np.hypot(x1 - x0, y1 - y0) * (1 - s)
    w = max(0, 3 - int(d))                     # thick near the root
    SEG_PTS.append((xs, ys, path, w, x1 - x0, y1 - y0))

# leaves: ~3000 around the branch tips, each with its burst time
N_LEAF = 3000
_ti = rng.integers(0, len(TIPS), N_LEAF)
LF_X = TIPS[_ti, 0] + rng.normal(0, 0.045, N_LEAF)
LF_Y = TIPS[_ti, 1] + rng.normal(0, 0.035, N_LEAF)
LF_BX, LF_BY = TIPS[_ti, 0], TIPS[_ti, 1]
LIGHT_SPEED = MAXPATH / 1.3                     # path units / s
_touch_path = 0.30
LF_T = T_TOUCH + np.abs(TIPS[_ti, 2] - _touch_path) / LIGHT_SPEED \
    + rng.uniform(0, 0.3, N_LEAF)
LF_K = rng.integers(0, 10, N_LEAF)
LF_PH = rng.uniform(0, 2 * np.pi, N_LEAF)

# flowers: bigger clumps with every step (sum 480)
FL_N = [40, 50, 60, 70, 80, 85, 95]
FL = []
for k, (ts, n) in enumerate(zip(STEPS, FL_N)):
    fx = walk_x(ts) + (0.03 if k % 2 else -0.02)
    spread = 0.035 + 0.014 * k
    dx = rng.normal(0, spread, n)
    dy = rng.uniform(-0.004, 0.05, n)
    d = np.hypot(dx / spread, dy / 0.05)
    tb = ts + 0.08 + 0.35 * d / 2.5 + rng.uniform(0, 0.12, n)
    FL.append(np.stack([fx + dx, GROUND + dy, tb,
                        rng.uniform(0.012, 0.045, n),
                        rng.integers(0, 3, n), rng.random(n)], -1))
FL = np.concatenate(FL)

# hair: strands flowing behind her head
N_HAIR = 26
HA_L = rng.uniform(0.7, 1.1, N_HAIR)
HA_O = rng.uniform(-0.06, 0.03, N_HAIR)        # root offset on head
HA_PH = rng.uniform(0, 2 * np.pi, N_HAIR)
HS = np.linspace(0, 1, 26)

# background
PX, PY = pic_coords()
SKY = vgradient([(0.0, SKY_TOP), (0.62, SKY_LOW), (GROUND, (0.28, 0.18,
                                                             0.14)),
                 (GROUND, (0.08, 0.06, 0.05)), (1.0, (0.03, 0.02,
                                                       0.02))])
FAR = np.zeros_like(PX, bool)                  # far dead tree line
for _ in range(22):
    x0 = rng.uniform(-1.05, 1.05)
    h = rng.uniform(0.08, 0.22)
    FAR |= (np.abs(PX - x0) < 0.006) & (PY > 0.70 - h) & (PY < 0.72)
    for _b in range(3):
        yb = 0.70 - h * rng.uniform(0.3, 0.9)
        dx_ = rng.choice([-1, 1]) * rng.uniform(0.02, 0.06)
        s = np.clip((PX - x0) / dx_, 0, 1)
        FAR |= (np.abs(PY - (yb - 0.03 * s)) < 0.004) & (s > 0) \
            & (s < 1)
FAR |= (PY > 0.70 - 0.02 * noise2d(256, 2.5, 3)[0][(
    (PX + 1) * 120).astype(int) % 256]) & (PY < GROUND)
MIST = noise2d(128, beta=1.8, seed=4)
N_GRASS = 260
GR_X = rng.uniform(-1, 1, N_GRASS)
GR_Y = rng.uniform(GROUND + 0.004, 0.85, N_GRASS)
N_FLY = 70
FY_X = rng.uniform(-0.9, 0.95, N_FLY)
FY_Y = rng.uniform(0.25, 0.78, N_FLY)
FY_PH = rng.uniform(0, 2 * np.pi, N_FLY)


def camera(t):
    f1 = walk_x(STEPS[0])
    keys = [(0.0, 1.38, f1, 0.74), (1.0, 1.3, f1, 0.74),
            (3.5, 1.0, 0.0, 0.55), (9.5, 1.04, 0.1, 0.6),
            (10.6, 1.18, TOUCH[0], TOUCH[1]),
            (13.0, 1.0, 0.3, 0.5), (16.5, 1.0, 0.3, 0.5),
            (18.0, 1.38, f1, 0.74)]
    i = max(j for j in range(len(keys)) if keys[j][0] <= t)
    k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
    u = smooth(ramp(t, k0[0], k1[0])) if k1[0] > k0[0] else 0.0
    z, fx, fy = (a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
    return dict(zoom=z, focus=(fx, fy))


def line(g, X, Y, col, lum):
    """polyline with direction glyphs."""
    if len(X) < 2:
        return
    ch = dir_chars(np.gradient(X), np.gradient(Y) * ASPECT)
    rr, cc = g.to_cell(X, Y)
    g.put_cells(rr, cc, ch, np.asarray(col) * np.reshape(lum, (-1, 1)))


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    rv = smooth(ramp(t, *T_REVEAL)) * fade
    wake = smooth(ramp(t, *T_WAKE))
    warm = wake * (1 - 0.3 * ramp(t, 13.0, 16.5))

    # ================= picture layer =================
    under = SKY * (0.15 + 0.85 * rv)
    mist = MIST[(PY * 3 * 128).astype(int) % 128,
                ((PX * 0.5 + 0.01 * t) * 128).astype(int) % 128]
    under += ((PY > 0.6) & (PY < GROUND))[..., None] \
        * (mist * 0.08 * rv)[..., None] * np.array([0.5, 0.45, 0.5])
    under[FAR] = under[FAR] * 0.35
    glow = np.exp(-np.hypot(PX - TREE_X, (PY - 0.45) * ASPECT) / 0.5)
    under += (glow * 0.35 * warm * fade)[..., None] \
        * np.array([1.0, 0.85, 0.40])
    under += ((PY > 0.55) & (PY < GROUND))[..., None] \
        * (0.12 * warm * fade) * np.array([0.6, 0.8, 0.3])

    # ================= ground: dry grass =================
    gl = 0.25 * rv
    rr, cc = g.to_cell(GR_X, GR_Y)
    g.put_cells(rr, cc, np.where(np.arange(N_GRASS) % 3, CIDX[","],
                                 CIDX["'"]),
                np.array([0.45, 0.35, 0.22]) * gl)

    # ================= the tree =================
    vein_pre = smooth(ramp(t, 9.9, T_TOUCH))   # hint before the touch
    front = (t - T_TOUCH) * LIGHT_SPEED         # light along the path
    for xs, ys, path, w, dx, dy in SEG_PTS:
        X, Y = to_screen(xs, ys)
        dist = np.abs(path - _touch_path)
        lit = np.exp(-((dist - front) / 0.08) ** 2) * (front > 0)
        hint = vein_pre * np.exp(-dist / 0.08)
        passed = (dist < front).astype(float)
        col = BARK + (BARK_ALIVE - BARK) * passed[:, None] * wake
        lum = (0.75 * rv + 1.6 * lit + 0.9 * hint)[:, None]
        col = col * (1 - lit - hint)[:, None] \
            + MINT * (lit + hint)[:, None]
        ch = dir_chars(np.full(len(X), dx), np.full(len(X), dy))
        for off in range(-w, w + 1):
            rr, cc = g.to_cell(X + off * 0.009, Y)
            g.put_cells(rr, cc, CIDX["#"] if abs(off) < w else ch,
                        col * lum * fade)
        if w == 0:
            rr, cc = g.to_cell(X, Y)
            g.put_cells(rr, cc, ch, col * lum * fade)

    # leaves burst outward from the tips, then sway
    age = t - LF_T
    on = age > 0
    n_leaf = int(on.sum())
    if n_leaf:
        k = np.clip(pop(np.clip(age[on] / 0.45, 0, 1)), 0, 1.3)
        sway = 0.006 * np.sin(2.0 * t + LF_PH[on]) * (age[on] > 0.5)
        x = LF_BX[on] + (LF_X[on] - LF_BX[on]) * k + sway
        y = LF_BY[on] + (LF_Y[on] - LF_BY[on]) * k
        X, Y = to_screen(x, y)
        kind = LF_K[on]
        ch = np.select([kind < 4, kind < 7, kind < 9],
                       [CIDX["*"], CIDX["o"], CIDX["@"]], CIDX["&"])
        cidx = np.where(kind == 9, 2, kind % 2)
        flash = 1 + 1.2 * np.exp(-age[on] / 0.2)
        lum = (0.75 + 0.25 * np.sin(3 * t + LF_PH[on])) * flash
        rr, cc = g.to_cell(X, Y)
        g.put_cells(rr, cc, ch, LEAF_C[cidx] * (lum * fade)[:, None])

    # ================= flowers =================
    fage = t - FL[:, 2]
    fon = fage > 0
    n_fl = int(fon.sum())
    if n_fl:
        F = FL[fon]
        a = fage[fon]
        h = F[:, 3] * smooth(np.clip(a / 0.35, 0, 1))
        sway = 0.004 * np.sin(2.2 * t + F[:, 5] * 6)
        for s in (0.3, 0.65):                  # stems
            rr, cc = g.to_cell(F[:, 0] + sway * s, F[:, 1] - h * s)
            g.put_cells(rr, cc, np.where(F[:, 5] > 0.5, CIDX["|"],
                                         CIDX["'"]),
                        STEM[None] * 0.8 * fade)
        bl = np.clip((a - 0.25) / 0.2, 0, 1)
        pk = 1 + 1.0 * np.exp(-np.clip(a - 0.25, 0, None) / 0.15)
        ch = np.where(F[:, 5] > 0.7, CIDX["@"],
                      np.where(F[:, 5] > 0.35, CIDX["*"], CIDX["o"]))
        rr, cc = g.to_cell(F[:, 0] + sway, F[:, 1] - h)
        col = FLOWER_C[F[:, 4].astype(int)] * (bl * pk * fade)[:, None]
        g.put_cells(rr, cc, ch, col)

    # hook: light motes rise from the first footprint
    a0 = t - STEPS[0]
    if 0 < a0 < 1.6:
        n = 110
        ph = np.arange(n) / n
        x = walk_x(STEPS[0]) + 0.12 * np.sin(ph * 37 + 3 * a0) * ph
        y = GROUND - 0.35 * a0 * (0.3 + ph)
        lum = 1.4 * (1 - a0 / 1.6) * (0.5 + 0.5 * np.sin(ph * 19))
        rr, cc = g.to_cell(x, y)
        g.put_cells(rr, cc, np.where(np.arange(n) % 3, CIDX["."],
                                     CIDX["*"]),
                    MINT[None] * lum[:, None])

    # footprint glow + ring at every landing
    for ts in STEPS:
        a = t - ts
        if 0 < a < 0.8:
            fx = walk_x(ts)
            a = a * (0.7 if ts == STEPS[0] else 1.0)
            ang = np.linspace(0, 2 * np.pi, 18, endpoint=False)
            r = 0.02 + 0.08 * a
            rr, cc = g.to_cell(fx + r * np.cos(ang),
                               GROUND + 0.012 + r * np.sin(ang) * 0.15)
            g.put_cells(rr, cc, CIDX["."],
                        (MINT * 1.2 * (1 - a / 0.8))[None])
            under += (0.8 * (1 - a / 0.8) * np.exp(
                -np.hypot(PX - fx, (PY - GROUND) * ASPECT) / 0.05)
                * fade)[..., None] * EMERALD

    # ================= the goddess =================
    xg = walk_x(t)
    moving = 0 < ramp(t, *T_WALK) < 1
    bob = 0.004 * abs(np.sin(np.pi * (t - 1.6) / 1.2)) * moving
    du = (g.X - xg) / FX                       # in height fractions
    dv = (GROUND - bob - g.Y) / FIG_H
    lean = 0.04 * moving
    du = du - lean * dv
    flutter = 0.025 * np.sin(9 * du + 5 * t) * (dv < 0.15)
    half = np.interp(dv, [0, 0.10, 0.30, 0.52, 0.62, 0.76, 0.80,
                          0.84],
                     [0.26, 0.20, 0.13, 0.075, 0.085, 0.11, 0.035,
                      0.035]) + flutter
    body = (dv >= 0) & (dv <= 0.84) & (np.abs(du) < half)
    head = (du / 0.075) ** 2 + ((dv - 0.90) / 0.065) ** 2 < 1
    a_g = smooth(ramp(t, 0.6, 2.4)) * fade
    shade = np.clip(1 - dv, 0, 1)
    dcol = DRESS + (HEM - DRESS) * shade[..., None] ** 2
    edge = body & ~(np.roll(body, 1, 1) & np.roll(body, -1, 1)
                    & np.roll(body, 1, 0))
    g.put(body, np.where((g.c + g.r) % 3 == 0, CIDX["%"],
                         CIDX["#"])[body], (dcol * 0.85 * a_g)[body])
    g.put(edge, CIDX["|"], MINT * 1.1 * a_g)
    g.put(head, CIDX["o"], SKIN * 0.9 * a_g)
    under += (0.22 * a_g * np.exp(-np.hypot(
        PX - xg, (PY - (GROUND - 0.5 * FIG_H)) * ASPECT) / 0.18)
    )[..., None] * EMERALD
    # flowing hair: strands from the back of the head
    for j in range(N_HAIR):
        s = HS
        # falls down the back to the waist, the ends drift behind
        wave = 0.06 * np.sin(2.3 * t - 5 * s + HA_PH[j]) * s ** 1.5
        trail = (0.10 + 0.10 * moving) * s ** 2
        hu = HA_O[j] - 0.05 - 0.10 * s * HA_L[j] - trail + wave
        hv = 0.95 - s * 0.55 * HA_L[j]
        X = xg + (hu + lean * hv) * FX
        Y = GROUND - bob - hv * FIG_H
        col = EMERALD if j % 2 else MINT
        line(g, X, Y, col, (1.1 - 0.4 * s) * a_g)
    # arm: swings while walking, reaches for the bark at the end
    reach = smooth(ramp(t, 9.8, T_TOUCH))
    sx, sy = xg + 0.07 * FX, GROUND - bob - 0.76 * FIG_H
    swing = 0.05 * np.sin(np.pi * (t - 1.6) / 1.2) * moving
    hx0, hy0 = xg + (0.06 + swing) * FX, GROUND - 0.45 * FIG_H
    hx = hx0 + (TOUCH[0] - hx0) * reach
    hy = hy0 + (TOUCH[1] - hy0) * reach
    s = np.linspace(0, 1, 16)
    line(g, sx + (hx - sx) * s, sy + (hy - sy) * s, SKIN,
         0.8 * a_g * np.ones(16))
    if reach > 0.95:                           # touch glow
        under += (0.6 * np.exp(-np.hypot(PX - TOUCH[0], (
            PY - TOUCH[1]) * ASPECT) / 0.05) * fade)[..., None] * MINT

    # ================= afterglow: fireflies and drifting petals ======
    kf = smooth(ramp(t, 12.0, 13.5)) * fade
    if kf > 0:
        x = FY_X + 0.03 * np.sin(0.8 * t + FY_PH)
        y = FY_Y - 0.02 * (t - 12) - 0.01 * np.sin(1.3 * t + FY_PH)
        fl = kf * (0.5 + 0.5 * np.clip(np.sin(3 * t + FY_PH), 0, 1))
        rr, cc = g.to_cell(x, y)
        g.put_cells(rr, cc, np.where(np.arange(N_FLY) % 4, CIDX["."],
                                     CIDX["+"]),
                    np.array([0.8, 1.0, 0.5])[None] * fl[:, None])

    n_steps = sum(t >= s for s in STEPS)
    n_lit = int((g.col.max(-1) > 0.05).sum())
    return {"under": np.clip(under, 0, 1), "camera": camera(t),
            "hud": [HANDLE,
                    f"steps {n_steps}   flowers {n_fl}   "
                    f"leaves {n_leaf:,}",
                    f"letters {n_lit:,}"]}
