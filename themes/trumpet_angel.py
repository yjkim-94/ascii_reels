"""trumpet_angel: each golden note lights the stained glass it meets."""
import numpy as np
from engine import (CIDX, TOP_H, W, dir_chars, ease, noise2d, ramp,
                    sample, smooth)

TITLE = "Trumpet Angel"
HANDLE = "@justmade.lab"
DURATION = 18.0
GLOW = 0.9
rng = np.random.default_rng(73)

# ---------- timeline (seconds) ----------
WAVES = [0.10, 1.50, 2.90, 4.30, 5.70, 7.10, 8.50]   # a note starts
REACH = [0.40, 0.62, 0.82, 0.98, 1.12, 1.30, 1.60]   # how far it lights
T_OUTLINE = (0.3, 3.4)    # the lead lines appear behind the notes
T_BREATH = (10.0, 11.3)   # silence; the wings rise, a breath in
T_CLIMAX = 11.3           # the long note: sky and frame light up
T_GLOW = (11.8, 12.8)     # the whole window brightens from behind
RAYS_AT = [12.5, 12.9, 13.3, 13.7, 14.1]
AFTER = [13.2, 14.6, 16.0]                           # small notes
T_FADE = (16.5, 18.0)     # glass goes dark from the edge, then loop
SCENES = [("first note", 0.0, 1.0), ("outline", 1.0, 3.5),
          ("glass fills", 3.5, 10.0), ("breath", *T_BREATH),
          ("long note", T_CLIMAX, 12.5), ("lit window", 12.5, 16.5),
          ("fade", *T_FADE)]
POSTER_T = 14.6

# ---------- layout (screen: X -1..1, Y 0 top .. 1 bottom) ----------
ASPECT = TOP_H / (W / 2)  # one Y unit in X units
S = 0.48                  # reference px -> screen px
BELL = (195, 85)          # trumpet bell in the reference picture
BELL_X, HEAD_TOP = -0.32, 0.245
V_NOTE, V_LONG = 1.1, 1.45                # ring speed, X units / s
ARCH_W, ARCH_SPRING, ARCH_TOP, ARCH_LOW = 0.90, 0.50, 0.03, 0.83
BAND = 0.06               # frame thickness
ROSE = (0.0, 0.15, 0.11)  # small rose window: x, y, radius

LEAD = np.array([0.16, 0.15, 0.18])
LEAD_HOT = np.array([0.75, 0.58, 0.25])
LAPIS = np.array([[0.10, 0.22, 0.75], [0.18, 0.36, 0.90],
                  [0.30, 0.50, 0.95], [0.08, 0.16, 0.55]])
IVORY = np.array([[0.95, 0.90, 0.78], [0.90, 0.82, 0.62],
                  [0.98, 0.94, 0.86]])
PEARL = np.array([[0.88, 0.90, 1.00], [0.80, 0.84, 0.95],
                  [0.94, 0.95, 1.00]])
SKIN = np.array([0.98, 0.84, 0.70])
GOLD = np.array([[1.00, 0.76, 0.22], [1.10, 0.90, 0.45]])
HAIR = np.array([[1.00, 0.70, 0.25], [0.92, 0.58, 0.18]])
CRIMSON = np.array([[0.80, 0.08, 0.16], [0.95, 0.25, 0.30]])
EMERALD = np.array([0.10, 0.65, 0.40])
WAVE = np.array([1.30, 1.00, 0.45])
FEATHER = np.array([1.00, 0.98, 0.92])
RAY = np.array([1.00, 0.92, 0.70])


def to_ref(X, Y):
    """screen -> reference picture px (the angel is drawn there)."""
    u = BELL[0] + (X - BELL_X) * (W / 2) / S
    v = 120 + (Y - HEAD_TOP) * TOP_H / S
    return u, v


def to_screen(u, v):
    return (BELL_X + (u - BELL[0]) * S / (W / 2),
            HEAD_TOP + (v - 120) * S / TOP_H)


# ---------- shapes in reference px (traced by eye) ----------
WING_L = [(250, 240), (330, 262), (420, 300), (470, 360), (480, 450),
          (470, 560), (450, 680), (400, 760), (330, 775), (262, 742),
          (215, 650), (195, 540), (200, 420), (215, 320)]
WING_R = [(860, 240), (930, 290), (990, 370), (1040, 460),
          (1070, 560), (1066, 680), (1050, 800), (1000, 850),
          (930, 800), (880, 700), (830, 600), (790, 500), (760, 420),
          (780, 330), (820, 270)]
PIVOT_L, PIVOT_R = (480, 430), (765, 425)     # wing roots
ROBE = [(460, 400), (560, 345), (650, 345), (740, 400), (800, 470),
        (850, 560), (920, 660), (990, 760), (1060, 870), (1110, 980),
        (1100, 1080), (1000, 1120), (900, 1100), (850, 1010),
        (760, 930), (640, 900), (520, 900), (400, 912), (280, 900),
        (212, 862), (240, 820), (300, 800), (330, 640), (380, 560),
        (430, 470)]
HAIR_P = [(560, 178), (575, 140), (615, 117), (670, 110), (725, 126),
          (766, 165), (786, 222), (782, 288), (762, 338), (722, 366),
          (684, 362), (668, 322), (700, 260), (690, 170), (620, 158)]
FACE = [(585, 165), (640, 150), (690, 165), (706, 215), (690, 270),
        (655, 310), (612, 318), (585, 292), (566, 250), (572, 205)]
NECK = [(612, 300), (662, 300), (676, 352), (622, 364)]
CLOUD = [(-150, 1150, 200), (80, 1080, 190), (330, 1130, 210),
         (600, 1180, 220), (880, 1150, 210), (1120, 1060, 190),
         (1330, 1120, 200), (1520, 1200, 230)]
# capsules: (u0, v0, u1, v1, half width)
LIMBS = {"upper arm": (335, 375, 470, 430, 22),
         "forearm": (335, 375, 432, 212, 18),
         "knee": (330, 722, 520, 772, 52),
         "shin": (688, 862, 800, 1215, 34),
         "foot": (792, 1212, 872, 1268, 22)}
BLOBS = {"hand": (440, 192, 30, 38), "shoulder": (732, 430, 46, 34)}
MOUTH = (566, 241)
# painted lines on the face (like lead): brows, lids, nose, lips
FACE_LINES = [[(614, 182), (628, 176), (642, 178)],
              [(664, 172), (678, 168), (692, 172)],
              [(620, 198), (632, 194), (642, 197)],
              [(666, 190), (678, 187), (688, 190)],
              [(626, 210), (608, 234), (618, 240)],
              [(586, 252), (598, 258)],
              [(612, 304), (644, 300), (678, 280)]]


def in_poly(x, y, pts):
    p = np.asarray(pts, float)
    inside = np.zeros(x.shape, bool)
    for (x1, y1), (x2, y2) in zip(p, np.roll(p, -1, 0)):
        cross = (y1 > y) != (y2 > y)
        xi = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
        inside ^= cross & (x < xi)
    return inside


def seg_dist(x, y, u0, v0, u1, v1):
    dx, dy = u1 - u0, v1 - v0
    k = np.clip(((x - u0) * dx + (y - v0) * dy) / (dx * dx + dy * dy),
                0, 1)
    return np.hypot(x - u0 - k * dx, y - v0 - k * dy)


def trumpet_dist(x, y):
    """tube from the lips, flaring into the bell; < 0 is inside."""
    ax, ay = BELL[0] - MOUTH[0], BELL[1] - MOUTH[1]
    ln = np.hypot(ax, ay)
    s = ((x - MOUTH[0]) * ax + (y - MOUTH[1]) * ay) / ln ** 2
    off = np.abs((x - MOUTH[0]) * ay - (y - MOUTH[1]) * ax) / ln
    half = 6 + 52 * np.clip(s, 0, 1) ** 7
    return np.where((s > -0.01) & (s < 1.0), off - half, 99), s


def rot(x, y, c, a):
    ca, sa = np.cos(a), np.sin(a)
    dx, dy = x - c[0], y - c[1]
    return c[0] + dx * ca + dy * sa, c[1] - dx * sa + dy * ca


def arch(X, Y, w):
    """pointed arch of half width w (two circles meet at the top)."""
    h = (ARCH_SPRING - ARCH_TOP) * ASPECT
    c = (h * h - w * w) / (2 * w)
    R = w + c
    dy = (ARCH_SPRING - Y) * ASPECT
    top = (np.hypot(X - c, dy) <= R) & (np.hypot(X + c, dy) <= R)
    return np.where(Y >= ARCH_SPRING, np.abs(X) <= w, top) \
        & (Y <= ARCH_LOW)


# ---------- panes: every part is cut into pieces of glass ----------
PANE_COL, PANE_PART, PANE_XY = [], [], []
PARTS = ["sky", "frame", "rose", "cloud", "wing", "robe", "skin",
         "hair", "face", "trumpet"]
# how strongly each part's glass glows in the picture layer
FILL = np.array([0.26, 0.30, 0.34, 0.30, 0.44, 0.34, 0.42, 0.45,
                 0.55, 0.60])


def new_panes(part, cols, xy):
    first = len(PANE_COL)
    PANE_COL.extend(cols)
    PANE_PART.extend([PARTS.index(part)] * len(cols))
    PANE_XY.extend(xy)
    return first


def seeds_in(test, box, n, seed):
    r = np.random.default_rng(seed)
    out = []
    while len(out) < n:
        x = r.uniform(box[0], box[1], 400)
        y = r.uniform(box[2], box[3], 400)
        out.extend(np.stack([x, y], -1)[test(x, y)])
    return np.array(out[:n])


def voronoi(x, y, sd, sx=1.0, sy=1.0, axis=None):
    """nearest seed; sx, sy stretch the cells, axis bends them."""
    best = np.full(x.shape, np.inf)
    lab = np.zeros(x.shape, int)
    for i, (a, b) in enumerate(sd):
        dx, dy = x - a, y - b
        if axis is not None:               # long along root -> seed
            ex, ey = a - axis[0], b - axis[1]
            n = np.hypot(ex, ey) + 1e-9
            along = (dx * ex + dy * ey) / n
            dx, dy = (dx * ey - dy * ex) / n, along
        d = (dx * sx) ** 2 + (dy * sy) ** 2
        m = d < best
        best[m], lab[m] = d[m], i
    return lab


def pick(pal, n, r):
    base = pal[r.integers(0, len(pal), n)]
    return np.clip(base * r.uniform(0.88, 1.08, (n, 1)), 0, 1.2)


_r = np.random.default_rng(5)
SKY_SD = seeds_in(lambda x, y: arch(x, y, ARCH_W - BAND),
                  (-0.9, 0.9, 0.03, 0.83), 58, 1)
SKY0 = new_panes("sky", pick(LAPIS, 58, _r), SKY_SD)
N_FRAME = 30
FR_COL = [CRIMSON[0], GOLD[0], EMERALD, GOLD[0]] * 8
FRAME0 = new_panes("frame", FR_COL[:N_FRAME], [(0, 0)] * N_FRAME)
ROSE0 = new_panes("rose", [GOLD[1]] + [CRIMSON[0], LAPIS[1]] * 4,
                  [ROSE[:2]] * 9)
CL_SD = np.array([(u, v - r * 0.35) for u, v, r in CLOUD]
                 + [(u + 110, v + 60) for u, v, r in CLOUD]
                 + [(u - 90, v + 150) for u, v, r in CLOUD])
CLOUD0 = new_panes("cloud", pick(IVORY, len(CL_SD), _r),
                   [to_screen(*p) for p in CL_SD])
WL_SD = seeds_in(lambda x, y: in_poly(x, y, WING_L),
                 (190, 485, 235, 780), 9, 2)
WR_SD = seeds_in(lambda x, y: in_poly(x, y, WING_R),
                 (755, 1075, 235, 855), 9, 3)
WING0 = new_panes("wing", pick(PEARL, 18, _r),
                  [to_screen(*p) for p in np.vstack([WL_SD, WR_SD])])
RB_SD = seeds_in(lambda x, y: in_poly(x, y, ROBE),
                 (210, 1115, 340, 1125), 22, 4)
rb_col = pick(IVORY, 22, _r)
rb_col[np.argsort(-RB_SD[:, 1])[:5]] = CRIMSON[[0, 1, 0, 1, 0]]
ROBE0 = new_panes("robe", rb_col, [to_screen(*p) for p in RB_SD])
SKIN_NAMES = list(LIMBS) + list(BLOBS) + ["neck"]
SKIN0 = new_panes("skin", [SKIN * 0.95] * len(SKIN_NAMES),
                  [to_screen(*LIMBS[k][:2]) if k in LIMBS
                   else to_screen(*BLOBS[k][:2]) if k in BLOBS
                   else to_screen(640, 330) for k in SKIN_NAMES])
HR_SD = seeds_in(lambda x, y: in_poly(x, y, HAIR_P),
                 (555, 790, 105, 370), 3, 6)
HAIR0 = new_panes("hair", pick(HAIR, 3, _r),
                  [to_screen(*p) for p in HR_SD])
FACE0 = new_panes("face", [SKIN], [to_screen(640, 235)])
TRUMP0 = new_panes("trumpet", [GOLD[0], GOLD[1], GOLD[0]],
                   [to_screen(470, 200), to_screen(330, 140),
                    to_screen(*BELL)])
PANE_COL = np.array(PANE_COL, float)
PANE_PART = np.array(PANE_PART)
PANE_XY = np.array(PANE_XY, float)
N_PANES = len(PANE_COL)


def label_static(X, Y):
    """pane id per point for everything but the wings (-1: none)."""
    u, v = to_ref(X, Y)
    lab = np.full(X.shape, -1)
    win = arch(X, Y, ARCH_W - BAND)
    lab[win] = SKY0 + voronoi(X[win], Y[win] * ASPECT,
                              SKY_SD * [1, ASPECT])
    band = arch(X, Y, ARCH_W) & ~win
    ang = np.arctan2((ARCH_SPRING + 0.05 - Y) * ASPECT, X)
    seg = np.clip(((ang + 0.6) / (np.pi + 1.2) * N_FRAME).astype(int),
                  0, N_FRAME - 1)
    lab[band] = FRAME0 + seg[band]
    rd = np.hypot(X - ROSE[0], (Y - ROSE[1]) * ASPECT)
    rose = rd < ROSE[2]
    ra = np.arctan2(Y - ROSE[1], X - ROSE[0])
    petal = ((ra + np.pi) / (2 * np.pi) * 8).astype(int) % 8
    inner = rd < ROSE[2] * 0.38
    lab[rose] = ROSE0 + np.where(inner, 0, 1 + petal)[rose]
    cloud = np.zeros(X.shape, bool)
    for cu, cv, cr in CLOUD:
        cloud |= np.hypot(u - cu, (v - cv) * 1.25) < cr
    cloud &= win
    lab[cloud] = CLOUD0 + voronoi(u[cloud], v[cloud], CL_SD, 0.55, 1.0)
    return lab


def label_front(X, Y):
    """parts in front of the wings."""
    u, v = to_ref(X, Y)
    lab = np.full(X.shape, -1)
    m = in_poly(u, v, ROBE)
    lab[m] = ROBE0 + voronoi(u[m], v[m], RB_SD, 1.0, 0.45)
    order = ["knee", "shin", "foot", "shoulder", "neck", "upper arm",
             "forearm"]
    for k in order:
        if k in LIMBS:
            m = seg_dist(u, v, *LIMBS[k][:4]) < LIMBS[k][4]
        elif k in BLOBS:
            cu, cv, a, b = BLOBS[k]
            m = ((u - cu) / a) ** 2 + ((v - cv) / b) ** 2 < 1
        else:
            m = in_poly(u, v, NECK)
        lab[m] = SKIN0 + SKIN_NAMES.index(k)
        if k == "neck":
            m = in_poly(u, v, HAIR_P)
            lab[m] = HAIR0 + voronoi(u[m], v[m], HR_SD)
            lab[in_poly(u, v, FACE)] = FACE0
    d, s = trumpet_dist(u, v)
    m = d < 0
    lab[m] = TRUMP0 + np.where(s > 0.82, 2, np.where(s > 0.45, 1, 0))[m]
    cu, cv, a, b = BLOBS["hand"]
    lab[((u - cu) / a) ** 2 + ((v - cv) / b) ** 2 < 1] = \
        SKIN0 + SKIN_NAMES.index("hand")
    return lab


def label_wings(X, Y, lift):
    """wings rotate up around their roots by `lift` radians."""
    u, v = to_ref(X, Y)
    lab = np.full(X.shape, -1)
    for sd, poly, piv, sgn, base in ((WL_SD, WING_L, PIVOT_L, 1, 0),
                                     (WR_SD, WING_R, PIVOT_R, -1, 9)):
        a, b = rot(u, v, piv, -sgn * lift)
        m = in_poly(a, b, poly)
        lab[m] = WING0 + base + voronoi(a[m], b[m], sd, 1.0, 0.45, piv)
    return lab


def lead_of(lab):
    """1-2 px lines where neighbouring glass changes."""
    e = np.zeros(lab.shape, bool)
    for k in (1, 2):
        e[:, :-k] |= lab[:, :-k] != lab[:, k:]
        e[:-k, :] |= lab[:-k, :] != lab[k:, :]
    return e & ((lab >= 0) | np.roll(lab >= 0, 1, 0)
                | np.roll(lab >= 0, 1, 1))


# picture layer at half resolution (finer than the letter grid)
QH, QW = TOP_H // 2, W // 2
QY, QX = np.mgrid[0:QH, 0:QW].astype(float)
QX, QY = (QX + 0.5) / QW * 2 - 1, (QY + 0.5) / QH
Q_STATIC, Q_FRONT = label_static(QX, QY), label_front(QX, QY)
QU, QV = to_ref(QX, QY)
FACE_INK = np.zeros(QX.shape, bool)
for line in FACE_LINES:
    for p0, p1 in zip(line[:-1], line[1:]):
        FACE_INK |= seg_dist(QU, QV, *p0, *p1) < 3.2
FACE_INK &= Q_FRONT == FACE0
# wing box: only this part is relabelled every frame
Q_WIN = arch(QX, QY, ARCH_W - BAND)
WB = (slice(int(0.25 * QH), int(0.80 * QH)), slice(0, QW))

# letter grid labels (cell centres)
GR, GC = np.mgrid[0:61, 0:108]
GX = ((GC + 0.5) * 10 - W / 2) / (W / 2)
GY = (GR + 0.5) * 18 / TOP_H
G_STATIC, G_FRONT = label_static(GX, GY), label_front(GX, GY)
G_TEX = rng.random(GX.shape)
_pl, _pr = to_screen(*PIVOT_L), to_screen(*PIVOT_R)
FEATHER_L = dir_chars(GX - _pl[0], (GY - _pl[1]) * ASPECT)
FEATHER_R = dir_chars(GX - _pr[0], (GY - _pr[1]) * ASPECT)
G_PH = rng.uniform(0, 2 * np.pi, GX.shape)

# pane timing: which note lights it, and when
BX, BY = to_screen(*BELL)
BELL_Y = BY
BLOW = np.arctan2(BELL[1] - MOUTH[1], BELL[0] - MOUTH[0])  # up-left
D_PANE = np.hypot(PANE_XY[:, 0] - BX, (PANE_XY[:, 1] - BY) * ASPECT)
LATE = np.isin(PANE_PART, [PARTS.index(p) for p in
                           ("sky", "frame", "rose")])
# first note allowed to light each part: trumpet, then the angel
FIRST = {"trumpet": 0, "skin": 1, "hair": 1, "face": 1, "wing": 2,
         "robe": 2, "cloud": 4}
LEGS = ("knee", "shin", "foot")
T_LIT = np.empty(N_PANES)
for i in range(N_PANES):
    d = D_PANE[i]
    if LATE[i]:
        T_LIT[i] = T_CLIMAX + d / V_LONG
        continue
    lo = FIRST[PARTS[PANE_PART[i]]]
    if i - SKIN0 in [SKIN_NAMES.index(k) for k in LEGS]:
        lo = 3                                # legs come with the robe
    w = next((k for k, R in enumerate(REACH) if R >= d and k >= lo),
             None)
    T_LIT[i] = (WAVES[w] + d / V_NOTE if w is not None
                else T_CLIMAX + d / V_LONG)
T_LIT += rng.uniform(0, 0.12, N_PANES)
D_MAX = D_PANE.max()
T_OFF = T_FADE[0] + (1 - D_PANE / D_MAX) * 1.0

# curls: small letters over the hair, brighter on the outline
_cu = seeds_in(lambda x, y: in_poly(x, y, HAIR_P)
               & ~in_poly(x, y, FACE), (555, 790, 105, 370), 70, 8)
CURL_XY = np.array([to_screen(*p) for p in _cu])
CURL_CH = ["@" if k % 3 else "o" for k in range(len(_cu))]
CURL_PH = rng.uniform(0, 2 * np.pi, len(_cu))

# falling feathers: (start time, x, y) along the wing tips
N_FEATHER = 22
FE_T = np.sort(np.concatenate([[1.9], np.linspace(2.6, 9.6, 8),
                               np.linspace(10.2, 16.2, 13)]))
_edge = np.array([to_screen(*p) for p in WING_L[6:12] + WING_R[5:10]])
FE_XY = _edge[rng.integers(0, len(_edge), N_FEATHER)]
FE_V = rng.uniform(0.045, 0.07, N_FEATHER)
FE_PH = rng.uniform(0, 2 * np.pi, N_FEATHER)
FE_SZ = rng.integers(15, 22, N_FEATHER)
FLIP = "\\-/-"

# light rays after the long note, and the dust inside them
RAY_X = np.array([-0.62, -0.30, 0.02, 0.34, 0.64])
N_DUST = 160
DU_R = rng.integers(0, 5, N_DUST)
DU_S = rng.random(N_DUST)
DU_PH = rng.uniform(0, 2 * np.pi, N_DUST)


# light behind the glass drifts slowly, so the panes breathe
SHIM = noise2d(128, beta=2.2, seed=11)
# golden motes thrown from the bell with every note
N_MOTE = 48
MO_A = rng.normal(0, 0.9, N_MOTE)          # angle off the bell axis
MO_V = rng.uniform(0.35, 0.95, N_MOTE)     # share of the ring speed
MO_K = rng.random(N_MOTE)


def notes(t):
    """(start, reach, speed, width, gain) of every ring alive at t."""
    # rings travel on past the glass they light, fading out
    out = [(a, max(R, 1.0), V_NOTE, 0.024, 1.25 if a < 1 else 1.0)
           for a, R in zip(WAVES, REACH)]
    out.append((T_CLIMAX, 1.9, V_LONG, 0.05, 1.5))
    out += [(a, 1.0, V_NOTE, 0.02, 0.8) for a in AFTER]
    return [n for n in out if 0 <= t - n[0] < n[1] / n[2] + 0.3]


def ring(D, ang, t, n):
    """ring brightness at distance D, strongest toward the bell."""
    a, R, V, wd, gain = n
    r = (t - a) * V
    face = np.cos(ang - BLOW)
    dirf = 0.35 + 0.65 * np.clip(face, 0, 1) ** 1.5
    life = (1 - smooth(np.clip(r / (R * 1.15), 0, 1))) * gain
    w = wd * (0.6 + 0.4 * dirf)
    return np.exp(-((D - r) / w) ** 2) * dirf * life, r


def draw(g, t):
    lift = 0.05 * smooth(ramp(t, T_BREATH[0], 10.7)) \
        * (1 - smooth(ramp(t, 11.0, 12.2))) + 0.012 * np.sin(1.6 * t)
    glow = 1 + 0.35 * smooth(ramp(t, *T_GLOW))
    pulse = 1 + 0.07 * np.sin(2 * np.pi * (t - T_BREATH[0]) / 1.3) \
        * (T_BREATH[0] < t < T_CLIMAX)
    age = t - T_LIT
    lit = smooth(np.clip(age / 0.4, 0, 1)) \
        * (1 - smooth(np.clip((t - T_OFF) / 0.5, 0, 1)))
    flash = 1 + 0.8 * np.exp(-np.clip(age, 0, None) / 0.25) * (age > 0)
    pane = PANE_COL * (lit * flash * glow * pulse)[:, None]
    fade = 1 - ease(ramp(t, *T_FADE))
    seen = smooth(ramp(t, *T_OUTLINE)) * fade

    # ---------------- picture layer: glass, lead, face ------------
    lab = Q_STATIC.copy()
    sub = lab[WB]
    wl = label_wings(QX[WB], QY[WB], lift)
    sub[wl >= 0] = wl[wl >= 0]
    fr = Q_FRONT >= 0
    lab[fr] = Q_FRONT[fr]
    under = np.zeros((QH, QW, 3))
    on = lab >= 0
    shim = 0.8 + 0.4 * sample(SHIM, QX * 0.6 - 0.08 * t,
                              QY * 1.2 + 0.05 * t)
    under[on] = pane[lab[on]] * (FILL[PANE_PART[lab[on]]]
                                 * shim[on])[:, None]
    lead = lead_of(lab) | FACE_INK
    QD = np.hypot(QX - BX, (QY - BY) * ASPECT)
    reveal = np.clip((t - 0.3) / 3.1 * 1.9 - QD, 0, 1) * fade
    hot = np.zeros(QX.shape)
    qang = np.arctan2((QY - BY) * ASPECT, QX - BX)
    for n in notes(t):
        rg, _ = ring(QD, qang, t, n)
        hot += rg
        wide, _ = ring(QD, qang, t, n[:3] + (n[3] * 4, n[4] * 0.3))
        under += ((rg * 0.28 + wide) * fade)[..., None] * WAVE
    under[lead] = (LEAD * (reveal * seen)[lead, None] * 0.9
                   + LEAD_HOT * np.clip(hot[lead], 0, 1)[:, None])
    rays_on = [smooth(ramp(t, a, a + 0.8)) * fade for a in RAYS_AT]
    for k, x0 in enumerate(RAY_X):
        if rays_on[k] > 0:
            sway = 0.03 * np.sin(0.7 * t + k)
            off = QX - (x0 + sway) + (QY - 0.05) * 0.45
            band = np.exp(-(off / 0.05) ** 2) * Q_WIN
            under += (band * 0.16 * rays_on[k])[..., None] * RAY

    # ---------------- letter grid: glass texture -------------------
    glab = G_STATIC.copy()
    gw = label_wings(GX, GY, lift)
    glab[gw >= 0] = gw[gw >= 0]
    gf = G_FRONT >= 0
    glab[gf] = G_FRONT[gf]
    edge = np.zeros(glab.shape, bool)
    edge[:, :-1] |= glab[:, :-1] != glab[:, 1:]
    edge[:-1, :] |= glab[:-1, :] != glab[1:, :]
    ok = (glab >= 0) & ~edge & (PANE_PART[glab] != PARTS.index("face"))
    shimmer = (0.55 + 0.35 * G_TEX + 0.10 * np.sin(1.5 * t + G_PH)) \
        * (0.8 + 0.4 * sample(SHIM, GX * 0.6 - 0.08 * t,
                              GY * 1.2 + 0.05 * t))
    col = pane[np.where(ok, glab, 0)] * shimmer[..., None] * 0.9
    part = PANE_PART[np.where(ok, glab, 0)]
    ch = np.where(G_TEX > 0.66, CIDX["#"],
                  np.where(G_TEX > 0.33, CIDX["%"], CIDX["+"]))
    wing = part == PARTS.index("wing")
    ch = np.where(wing, np.where(GX < 0.2, FEATHER_L, FEATHER_R), ch)
    ch = np.where(part == PARTS.index("hair"),
                  np.where(G_TEX > 0.5, CIDX["@"], CIDX["&"]), ch)
    ch = np.where(part == PARTS.index("trumpet"), CIDX["="], ch)
    ch = np.where(part == PARTS.index("robe"),
                  np.where(G_TEX > 0.5, CIDX["|"], CIDX["%"]), ch)
    ch = np.where(part == PARTS.index("cloud"),
                  np.where(G_TEX > 0.5, CIDX["o"], CIDX["~"]), ch)
    show = ok & (col.max(-1) > 0.02)
    g.put(show, ch[show], col[show])

    # ---------------- golden notes: rings of letters ---------------
    D = np.hypot(GX - BX, (GY - BY) * ASPECT)
    gang = np.arctan2((GY - BY) * ASPECT, GX - BX)
    n_notes = 0
    for n in notes(t):
        rg, r = ring(D, gang, t, n)
        m = rg > 0.12
        tx, ty = -np.sin(gang), np.cos(gang)
        rch = dir_chars(tx, ty)
        rch = np.where(np.abs(ty) > 0.8,
                       np.where(GX < BX, CIDX["("], CIDX[")"]), rch)
        g.put(m, rch[m], WAVE[None] * np.clip(rg[m], 0, 1.2)[:, None]
              * fade)
        a, R, V = n[:3]                     # motes ride the ring
        rm = (t - a) * V * MO_V
        am = BLOW + MO_A
        life = np.clip(1 - rm / (R * 0.9), 0, 1) * n[4]
        mx = BX + rm * np.cos(am)
        my = BY + rm * np.sin(am) / ASPECT
        rr, cc = g.to_cell(mx, my)
        g.put_cells(rr, cc, np.where(MO_K > 0.7, CIDX["*"],
                                     np.where(MO_K > 0.3, CIDX["+"],
                                              CIDX["."])),
                    WAVE[None] * (life * fade)[:, None])
    n_notes = sum(t >= a for a in WAVES + [T_CLIMAX] + AFTER)

    # ---------------- rays and dust ---------------------------------
    for k, x0 in enumerate(RAY_X):
        if rays_on[k] <= 0:
            continue
        sway = 0.03 * np.sin(0.7 * t + k)
        ys = np.linspace(0.06, 0.80, 40)
        xs = x0 + sway - (ys - 0.05) * 0.45
        inw = arch(xs, ys, ARCH_W - BAND)
        rr, cc = g.to_cell(xs[inw], ys[inw])
        g.put_cells(rr, cc, CIDX["/"], RAY[None] * 0.22 * rays_on[k])
        m = DU_R == k
        dy = (DU_S[m] + 0.05 * t) % 1.0
        dx = 0.035 * np.sin(DU_PH[m] + 0.9 * t)
        y = 0.06 + dy * 0.74
        x = x0 + sway - (y - 0.05) * 0.45 + dx
        tw = (0.5 + 0.5 * np.sin(3 * t + DU_PH[m])) \
            * arch(x, y, ARCH_W - BAND)
        rr, cc = g.to_cell(x, y)
        dust = 0.7 * tw * rays_on[k]
        g.put_cells(rr, cc, CIDX["."], RAY[None] * dust[:, None])

    # ---------------- falling feathers (sprites) --------------------
    sp = dict(x=[], y=[], ch=[], size=[], rgb=[])
    n_fe = 0
    for i in range(N_FEATHER):
        a = t - FE_T[i]
        if a < 0:
            continue
        n_fe += 1
        y = FE_XY[i, 1] + FE_V[i] * a
        if y > 0.82:
            continue
        x = FE_XY[i, 0] + 0.035 * np.sin(1.8 * a + FE_PH[i]) \
            - 0.01 * a
        k = int((1.8 * a + FE_PH[i]) / np.pi * 2) % 4
        vis = smooth(np.clip(a / 0.3, 0, 1)) \
            * (1 - smooth(np.clip((y - 0.74) / 0.08, 0, 1))) * fade
        sp["x"].append(x)
        sp["y"].append(y)
        sp["ch"].append(FLIP[k])
        sp["size"].append(int(FE_SZ[i]))
        sp["rgb"].append(FEATHER * vis)

    k = lit[HAIR0] * flash[HAIR0] * glow * fade
    if k > 0.01:
        tw = 0.75 + 0.25 * np.sin(2 * t + CURL_PH)
        sp["x"].extend(CURL_XY[:, 0])
        sp["y"].extend(CURL_XY[:, 1])
        sp["ch"].extend(CURL_CH)
        sp["size"].extend([11] * len(CURL_CH))
        sp["rgb"].extend(HAIR[0] * (0.8 * k * tw)[:, None])

    n_lit = int((lit > 0.5).sum())
    return {"under": np.clip(under, 0, 1),
            "sprites": sp if sp["x"] else None,
            "hud": [HANDLE,
                    f"feathers {n_fe}   notes {n_notes}   "
                    f"rays {sum(r > 0.5 for r in rays_on)}",
                    f"panes {n_lit}"]}
