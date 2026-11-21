"""forest_goddess: flowers rise where she steps; the forest wakes."""
import numpy as np
from engine import (CIDX, dir_chars, ease, noise2d, pic_coords, pop,
                    ramp, smooth, vgradient)

TITLE = "Forest Goddess"
HANDLE = "@justmade.lab"
DURATION = 20.0
GLOW = 1.0
rng = np.random.default_rng(51)

# ---------- timeline (seconds) ----------
STEPS = [0.2, 2.6, 3.8, 5.0, 6.2, 7.4, 8.6]   # a foot lands
T_REVEAL = (0.0, 3.5)     # the dusk forest and the dead tree appear
T_WALK = (1.6, 9.5)       # she walks to the tree
T_REACH = (9.8, 10.6)     # she reaches out and touches the bark
T_TOUCH = 10.6            # stage 1: green light runs up the tree
T_ARMS = (12.0, 12.6)     # she steps back and spreads her arms
T_RING = (12.6, 15.0)     # stage 2: a green ring runs over the land
T_DOWN = (15.5, 16.5)     # her arms come down
T_FADE = (18.5, 20.0)     # dusk falls back to dark, then loop
SCENES = [("first footprint", 0.0, 1.2), ("reveal", 1.0, 3.5),
          ("walk", 3.5, 9.5), ("reach", 9.5, 10.6),
          ("tree wakes", 10.6, 12.0), ("arms open", *T_ARMS),
          ("forest wakes", *T_RING), ("afterglow", 15.0, 18.5),
          ("fade", *T_FADE)]
POSTER_T = 15.6

# ---------- layout (screen: X -1..1, Y 0 top .. 1 bottom) ----------
GROUND = 0.78
ASPECT = 1098 / 540
FIG_PX = 0.40 * 1098      # her height in pixels
X_START, X_END = -0.72, 0.16
TREE_X = 0.42
TOUCH = (0.36, 0.60)      # where her hand meets the bark
RING_SPEED = 0.8          # X units per second

SKY_TOP = (0.10, 0.08, 0.12)
SKY_LOW = (0.45, 0.30, 0.22)
BARK = np.array([0.62, 0.54, 0.46])
BARK_FAR = np.array([0.30, 0.26, 0.24])
BARK_ALIVE = np.array([0.60, 0.50, 0.28])
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
GRASS_DRY = np.array([0.45, 0.35, 0.22])
GRASS_NEW = np.array([0.35, 0.85, 0.40])


def walk_x(t):
    """her position: walks in, then a small step back to cast."""
    x = X_START + (X_END - X_START) * smooth(ramp(t, *T_WALK))
    return x - 0.05 * smooth(ramp(t, *T_ARMS))


# ---------- trees: recursive branches (X units, y up) ----------
def make_tree(x0, length, depth_max, seed):
    r = np.random.default_rng(seed)
    segs = []

    def grow(x, y, ang, ln, depth, path):
        x1, y1 = x + ln * np.cos(ang), y + ln * np.sin(ang)
        segs.append((x, y, x1, y1, depth, path + ln))
        if depth >= depth_max:
            return
        for s in (-1, 1):
            grow(x1, y1, ang + s * r.uniform(0.28, 0.6),
                 ln * r.uniform(0.66, 0.8), depth + 1, path + ln)
        if depth < 3 and r.random() < 0.6:        # side twig
            grow(x1, y1, ang + r.normal(0, 0.9), ln * 0.55, depth + 2,
                 path + ln)

    grow(x0, 0.0, np.pi / 2 + r.normal(0, 0.05), length, 0, 0.0)
    return np.array(segs)


def sample_tree(segs, step=0.008):
    out = []
    for x0, y0, x1, y1, d, pl in segs:
        ln = np.hypot(x1 - x0, y1 - y0)
        s = np.linspace(0, 1, max(int(ln / step), 2))
        out.append((x0 + (x1 - x0) * s, y0 + (y1 - y0) * s,
                    pl - ln * (1 - s), int(d), x1 - x0, y1 - y0))
    return out


MAIN = make_tree(TREE_X, 0.42, 7, 3)
MAIN_PTS = sample_tree(MAIN)
MAXPATH = MAIN[:, 5].max()
TOUCH_PATH = 0.30
LIGHT_SPEED = MAXPATH / 1.1
TIPS = MAIN[MAIN[:, 4] >= 4][:, [2, 3, 5]]
N_LEAF = 3000
_ti = rng.integers(0, len(TIPS), N_LEAF)
LF_BX, LF_BY = TIPS[_ti, 0], TIPS[_ti, 1]
LF_X = LF_BX + rng.normal(0, 0.045, N_LEAF)
LF_Y = LF_BY + rng.normal(0, 0.035, N_LEAF)
LF_T = T_TOUCH + np.abs(TIPS[_ti, 2] - TOUCH_PATH) / LIGHT_SPEED \
    + rng.uniform(0, 0.25, N_LEAF)
LF_K = rng.integers(0, 10, N_LEAF)
LF_PH = rng.uniform(0, 2 * np.pi, N_LEAF)

# the far trees: smaller, darker; they wake when the ring arrives
FAR_X = np.array([-0.92, -0.66, -0.40, -0.12, 0.80, 0.97, 0.62])
FAR_S = np.array([0.20, 0.26, 0.18, 0.23, 0.22, 0.17, 0.15])
FAR_B = np.array([0.050, 0.035, 0.060, 0.045, 0.040, 0.060, 0.070])
FAR = []
for i, (x, s_, b) in enumerate(zip(FAR_X, FAR_S, FAR_B)):
    segs = make_tree(x, s_, 6, 100 + i)
    tips = segs[segs[:, 4] >= 4][:, [2, 3]]
    n = 285
    k = rng.integers(0, len(tips), n)
    FAR.append(dict(pts=sample_tree(segs), base=b,
                    bx=tips[k, 0], by=tips[k, 1],
                    lx=tips[k, 0] + rng.normal(0, 0.03, n),
                    ly=tips[k, 1] + rng.normal(0, 0.022, n),
                    lt=rng.uniform(0, 0.35, n),
                    lk=rng.integers(0, 10, n),
                    ph=rng.uniform(0, 2 * np.pi, n)))

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

# the goddess is drawn with small sprites on a lattice finer than
# the letter grid (7 x 11 px): profile, arms, folds, hair strands
LAT_X, LAT_Y = np.meshgrid(np.arange(-0.36, 0.36, 7 / FIG_PX),
                           np.arange(0, 1.0, 11 / FIG_PX))
LAT_X, LAT_Y = LAT_X.ravel(), LAT_Y.ravel()
N_HAIR = 30
HA_L = rng.uniform(0.7, 1.1, N_HAIR)
HA_O = rng.uniform(-0.07, 0.03, N_HAIR)
HA_PH = rng.uniform(0, 2 * np.pi, N_HAIR)
HS = np.linspace(0, 1, 34)
GLYPH = {CIDX[c]: c for c in "|/\\-"}

# background
PX, PY = pic_coords()
SKY = vgradient([(0.0, SKY_TOP), (0.62, SKY_LOW), (GROUND, (0.28, 0.18,
                                                             0.14)),
                 (GROUND, (0.08, 0.06, 0.05)), (1.0, (0.03, 0.02,
                                                       0.02))])
RIDGE = (PY > 0.71 - 0.02 * noise2d(256, 2.5, 3)[0][(
    (PX + 1) * 120).astype(int) % 256]) & (PY < GROUND)
MIST = noise2d(128, beta=1.8, seed=4)
N_GRASS = 320
GR_X = rng.uniform(-1, 1, N_GRASS)
GR_Y = rng.uniform(GROUND + 0.004, 0.85, N_GRASS)
N_FLY = 80
FY_X = rng.uniform(-0.95, 0.95, N_FLY)
FY_Y = rng.uniform(0.25, 0.78, N_FLY)
FY_PH = rng.uniform(0, 2 * np.pi, N_FLY)


def camera(t):
    f1 = walk_x(STEPS[0])
    xe = walk_x(13.0)
    keys = [(0.0, 1.38, f1, 0.74), (1.0, 1.3, f1, 0.74),
            (3.5, 1.0, 0.0, 0.55), (9.5, 1.04, 0.1, 0.6),
            (10.6, 1.18, TOUCH[0], TOUCH[1]),
            (12.0, 1.0, 0.3, 0.5), (12.6, 1.08, xe, 0.62),
            (15.0, 1.0, 0.0, 0.5), (18.5, 1.0, 0.0, 0.5),
            (20.0, 1.38, f1, 0.74)]
    i = max(j for j in range(len(keys)) if keys[j][0] <= t)
    k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
    u = smooth(ramp(t, k0[0], k1[0])) if k1[0] > k0[0] else 0.0
    z, fx, fy = (a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
    return dict(zoom=z, focus=(fx, fy))


def ring_reach(x):
    """time the green ring reaches screen X."""
    return T_RING[0] + np.abs(np.asarray(x) - walk_x(13.0)) / RING_SPEED


def draw_tree(g, pts, base_y, col0, lum0, light=None, wake=0.0,
              fade=1.0):
    """branches with direction glyphs; thick trunk near the root."""
    for xs, ys, path, d, dx, dy in pts:
        X, Y = xs, base_y - ys / ASPECT
        w = max(0, 3 - d) if light is not None else max(0, 1 - d)
        lit = hint = np.zeros(len(X))
        col = np.broadcast_to(col0, (len(X), 3))
        if light is not None:
            front, pre = light
            dist = np.abs(path - TOUCH_PATH)
            lit = np.exp(-((dist - front) / 0.08) ** 2) \
                * (front > 0) * fade
            hint = pre * np.exp(-dist / 0.08)
            alive = (dist < front).astype(float)[:, None] * wake
            col = col0 + (BARK_ALIVE - col0) * alive
            col = col * (1 - lit - hint)[:, None] \
                + MINT * (lit + hint)[:, None]
        lum = lum0 + 1.6 * lit + 0.9 * hint
        ch = dir_chars(np.full(len(X), dx), np.full(len(X), dy))
        for off in range(-w, w + 1):
            rr, cc = g.to_cell(X + off * 0.009, Y)
            g.put_cells(rr, cc, CIDX["#"] if abs(off) < w else ch,
                        col * lum[:, None])


def leaves(g, bx, by, lx, ly, birth, kind, ph, base_y, t, fade, k_):
    """leaves burst out from their twig, then sway."""
    age = t - birth
    on = age > 0
    if not on.any():
        return 0
    k = np.clip(pop(np.clip(age[on] / 0.45, 0, 1)), 0, 1.3)
    sway = 0.006 * k_ * np.sin(2.0 * t + ph[on]) * (age[on] > 0.5)
    x = bx[on] + (lx[on] - bx[on]) * k + sway
    y = by[on] + (ly[on] - by[on]) * k
    kd = kind[on]
    ch = np.select([kd < 4, kd < 7, kd < 9],
                   [CIDX["*"], CIDX["o"], CIDX["@"]], CIDX["&"])
    cidx = np.where(kd == 9, 2, kd % 2)
    flash = 1 + 1.2 * np.exp(-age[on] / 0.2)
    lum = (0.75 + 0.25 * np.sin(3 * t + ph[on])) * flash * k_
    rr, cc = g.to_cell(x, base_y - y / ASPECT)
    g.put_cells(rr, cc, ch, LEAF_C[cidx] * (lum * fade)[:, None])
    return int(on.sum())


def goddess(t, a_g, sp):
    """sprites for her figure: dress folds, profile, arms, hair."""
    xg = walk_x(t)
    moving = 0 < ramp(t, *T_WALK) < 1
    ph = np.pi * (t - 1.6) / 1.2
    bob = 0.004 * abs(np.sin(ph)) * moving
    lean = 0.05 * moving
    u = LAT_X - lean * LAT_Y                   # height fractions
    v = LAT_Y
    flutter = 0.025 * np.sin(9 * u + 5 * t) * (v < 0.15)
    half = np.interp(v, [0, 0.10, 0.30, 0.52, 0.62, 0.76, 0.80, 0.84],
                     [0.26, 0.20, 0.13, 0.075, 0.085, 0.11, 0.035,
                      0.035]) + flutter
    body = (v <= 0.84) & (np.abs(u) < half)
    hx, hy = 0.02, 0.90
    head = ((u - hx) / 0.072) ** 2 + ((v - hy) / 0.066) ** 2 < 1
    # side profile facing right: brow, nose, lips, chin
    face = (v > 0.83) & (v < 0.97) & (u > hx) & (u < hx + np.interp(
        v, [0.83, 0.85, 0.875, 0.895, 0.915, 0.94, 0.97],
        [0.045, 0.060, 0.072, 0.092, 0.082, 0.080, 0.060]))
    inner = body & (np.abs(u) < half - 0.03)
    edge = body & ~inner
    fold = np.cos(u / np.maximum(half, 1e-3) * np.pi * 2.5
                  + 0.3 * np.sin(2 * t + v * 6))
    shade = (0.55 + 0.45 * fold) * (0.6 + 0.4 * (1 - v))
    X = xg + u * FIG_PX / 540
    Y = GROUND - bob - v * FIG_PX / 1098

    def put(m, ch, col):
        n = int(m.sum())
        if n:
            sp["x"].extend(X[m])
            sp["y"].extend(Y[m])
            sp["ch"].extend(ch if isinstance(ch, list) else [ch] * n)
            sp["size"].extend([12] * n)
            sp["rgb"].extend(np.broadcast_to(col, (n, 3)))

    dcol = (DRESS + (HEM - DRESS) * (1 - v)[:, None] ** 2) \
        * (shade * a_g)[:, None]
    fch = np.where(fold > 0.55, "|", np.where(fold > -0.2, "#", "%"))
    put(inner, list(fch[inner]), dcol[inner])
    put(edge, list(np.where(u[edge] > 0, ")", "(")), MINT * 1.1 * a_g)
    put(head & ~face, "@", SKIN * 0.75 * a_g)
    put(face, ")", SKIN * 1.1 * a_g)

    def at(fu, fv):
        return (xg + (fu + lean * fv) * FIG_PX / 540,
                GROUND - bob - fv * FIG_PX / 1098)

    def strand(xs, ys, col):
        ch = dir_chars(np.gradient(xs), np.gradient(ys) * ASPECT)
        sp["x"].extend(xs)
        sp["y"].extend(ys)
        sp["ch"].extend(GLYPH[c] for c in ch)
        sp["size"].extend([12] * len(xs))
        sp["rgb"].extend(col)

    reach = smooth(ramp(t, *T_REACH)) * (1 - smooth(ramp(t, 11.6,
                                                         12.0)))
    spread = smooth(ramp(t, *T_ARMS)) * (1 - smooth(ramp(t, *T_DOWN)))
    swing = 0.06 * np.sin(ph) * moving
    s16 = np.linspace(0, 1, 18)
    for side in (1, -1):                       # front, back arm
        sx, sy = at(0.07 * side, 0.76)
        hx_, hy_ = at(0.06 * side + swing * side, 0.46)
        if side == 1:                          # the front arm reaches
            hx_ += (TOUCH[0] - hx_) * reach
            hy_ += (TOUCH[1] - hy_) * reach
        ox, oy = at(side * 0.42, 1.02)         # both arms spread wide
        hx_ += (ox - hx_) * spread
        hy_ += (oy - hy_) * spread
        col = SKIN * (1.0 if side == 1 else 0.7) * a_g
        strand(sx + (hx_ - sx) * s16, sy + (hy_ - sy) * s16,
               np.broadcast_to(col, (18, 3)))
        sp["x"].append(hx_)
        sp["y"].append(hy_)
        sp["ch"].append("o")
        sp["size"].append(13)
        sp["rgb"].append(col)
    # hair: strands down her back, the ends drift; the crown shines
    for j in range(N_HAIR):
        s = HS
        wave = 0.06 * np.sin(2.3 * t - 5 * s + HA_PH[j]) * s ** 1.5
        trail = (0.10 + 0.10 * moving + 0.06 * spread) * s ** 2
        hu = HA_O[j] - 0.04 - 0.10 * s * HA_L[j] - trail + wave
        hv = 0.97 - s * 0.55 * HA_L[j]
        xs, ys = at(hu, hv)
        col = (EMERALD if j % 2 else MINT) * (1.2 - 0.5 * s)[:, None]
        col = col + 0.4 * np.exp(-s / 0.12)[:, None]
        strand(xs, ys, col * a_g)
    return xg


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    rv = smooth(ramp(t, *T_REVEAL)) * fade
    w1 = smooth(ramp(t, T_TOUCH, 12.0))         # stage 1
    rad = (t - T_RING[0]) * RING_SPEED          # stage 2 ring radius
    w2 = smooth(ramp(t, *T_RING))
    xe = walk_x(13.0)

    # ================= picture layer =================
    under = SKY * (0.15 + 0.85 * rv)
    mist = MIST[(PY * 3 * 128).astype(int) % 128,
                ((PX * 0.5 + 0.01 * t) * 128).astype(int) % 128]
    under += ((PY > 0.6) & (PY < GROUND))[..., None] \
        * (mist * 0.08 * rv)[..., None] * np.array([0.5, 0.45, 0.5])
    under[RIDGE] = under[RIDGE] * 0.35
    warm = (0.6 * w1 + 0.6 * w2) * (1 - 0.3 * ramp(t, 15.0, 18.5))
    glow = np.exp(-np.hypot(PX - TREE_X, (PY - 0.45) * ASPECT) / 0.6)
    under += (glow * 0.3 * warm * fade)[..., None] \
        * np.array([1.0, 0.85, 0.40])
    if rad > 0:                                 # green land, ring edge
        land = (np.abs(PX - xe) < rad) & (PY > GROUND)
        under += (land * 0.10 * fade)[..., None] \
            * np.array([0.3, 0.8, 0.35])
        edge = np.exp(-((np.abs(PX - xe) - rad) / 0.05) ** 2) \
            * np.exp(-((PY - GROUND - 0.02) / 0.03) ** 2) * (rad < 2.2)
        under += (edge * 0.5 * fade)[..., None] * MINT

    # ================= ground grass: dry, then green =================
    green = ring_reach(GR_X) < t
    rr, cc = g.to_cell(GR_X, GR_Y)
    gch = np.where(green, np.where(np.arange(N_GRASS) % 2, CIDX["|"],
                                   CIDX['"']),
                   np.where(np.arange(N_GRASS) % 3, CIDX[","],
                            CIDX["'"]))
    gcol = np.where(green[:, None], GRASS_NEW * 1.6, GRASS_DRY)
    g.put_cells(rr, cc, gch, gcol * 0.28 * rv)
    if 0 < rad < 2.2:                           # the ring's bright edge
        for sgn in (-1, 1):
            xs = xe + sgn * rad + np.linspace(-0.03, 0.03, 7)
            for dy in (0.0, 0.02, 0.04):
                rr, cc = g.to_cell(xs, np.full(7, GROUND + 0.005 + dy))
                g.put_cells(rr, cc, CIDX["~"],
                            (MINT * 1.5 * fade)[None])

    # ================= far trees (wake with the ring) =================
    n_leaf = 0
    for tr, x in zip(FAR, FAR_X):
        by = 0.72 + tr["base"]
        draw_tree(g, tr["pts"], by, BARK_FAR, 0.8 * rv)
        n_leaf += leaves(g, tr["bx"], tr["by"], tr["lx"], tr["ly"],
                         ring_reach(x) + tr["lt"], tr["lk"], tr["ph"],
                         by, t, fade, 0.85)

    # ================= the touched tree =================
    pre = smooth(ramp(t, 10.0, T_TOUCH)) \
        * (1 - smooth(ramp(t, T_TOUCH, 11.2))) * fade
    front = (t - T_TOUCH) * LIGHT_SPEED
    draw_tree(g, MAIN_PTS, GROUND, BARK, rv, (front, pre), w1, fade)
    n_leaf += leaves(g, LF_BX, LF_BY, LF_X, LF_Y, LF_T, LF_K, LF_PH,
                     GROUND, t, fade, 1.0)

    # ================= flowers =================
    fage = t - FL[:, 2]
    fon = fage > 0
    n_fl = int(fon.sum())
    if n_fl:
        F = FL[fon]
        a = fage[fon]
        h = F[:, 3] * smooth(np.clip(a / 0.35, 0, 1))
        sway = 0.004 * np.sin(2.2 * t + F[:, 5] * 6)
        for s in (0.3, 0.65):
            rr, cc = g.to_cell(F[:, 0] + sway * s, F[:, 1] - h * s)
            g.put_cells(rr, cc, np.where(F[:, 5] > 0.5, CIDX["|"],
                                         CIDX["'"]),
                        STEM[None] * 0.8 * fade)
        bl = np.clip((a - 0.25) / 0.2, 0, 1)
        pk = 1 + 1.0 * np.exp(-np.clip(a - 0.25, 0, None) / 0.15)
        ch = np.where(F[:, 5] > 0.7, CIDX["@"],
                      np.where(F[:, 5] > 0.35, CIDX["*"], CIDX["o"]))
        rr, cc = g.to_cell(F[:, 0] + sway, F[:, 1] - h)
        g.put_cells(rr, cc, ch, FLOWER_C[F[:, 4].astype(int)]
                    * (bl * pk * fade)[:, None])

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
    for ts in STEPS:                            # footprint rings
        a = t - ts
        if 0 < a < 0.8:
            fx = walk_x(ts)
            ang = np.linspace(0, 2 * np.pi, 18, endpoint=False)
            r = 0.02 + 0.08 * a
            rr, cc = g.to_cell(fx + r * np.cos(ang),
                               GROUND + 0.012 + r * np.sin(ang) * 0.15)
            g.put_cells(rr, cc, CIDX["."],
                        (MINT * 1.2 * (1 - a / 0.8))[None])
            under += (0.8 * (1 - a / 0.8) * np.exp(
                -np.hypot(PX - fx, (PY - GROUND) * ASPECT) / 0.05)
                * fade)[..., None] * EMERALD

    # ================= the goddess (fine sprites) =================
    a_g = smooth(ramp(t, 0.6, 2.4)) * fade
    sp = dict(x=[], y=[], ch=[], size=[], rgb=[])
    xg = goddess(t, a_g, sp)
    aura = 0.22 + 0.5 * smooth(ramp(t, *T_ARMS)) \
        * (1 - smooth(ramp(t, 15.0, 17.0)))
    under += (aura * a_g * np.exp(-np.hypot(
        PX - xg, (PY - (GROUND - 0.2)) * ASPECT) / 0.2))[..., None] \
        * EMERALD
    if smooth(ramp(t, *T_REACH)) > 0.95 and t < 12.2:
        under += (0.6 * np.exp(-np.hypot(PX - TOUCH[0], (
            PY - TOUCH[1]) * ASPECT) / 0.05) * fade)[..., None] * MINT

    # ================= afterglow: fireflies =================
    kf = smooth(ramp(t, 13.5, 15.0)) * fade
    if kf > 0:
        x = FY_X + 0.03 * np.sin(0.8 * t + FY_PH)
        y = FY_Y - 0.02 * (t - 13.5) - 0.01 * np.sin(1.3 * t + FY_PH)
        fl = kf * (0.5 + 0.5 * np.clip(np.sin(3 * t + FY_PH), 0, 1))
        rr, cc = g.to_cell(x, y)
        g.put_cells(rr, cc, np.where(np.arange(N_FLY) % 4, CIDX["."],
                                     CIDX["+"]),
                    np.array([0.8, 1.0, 0.5])[None] * fl[:, None])

    n_steps = sum(t >= s for s in STEPS)
    n_lit = int((g.col.max(-1) > 0.05).sum())
    return {"under": np.clip(under, 0, 1), "camera": camera(t),
            "sprites": sp if sp["x"] else None,
            "hud": [HANDLE,
                    f"steps {n_steps}   flowers {n_fl}   "
                    f"leaves {n_leaf:,}",
                    f"letters {n_lit:,}"]}
