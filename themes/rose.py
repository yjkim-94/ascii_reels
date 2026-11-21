"""rose: a stem grows, a bud forms, and a big rose opens."""
import numpy as np
from engine import (CIDX, dir_chars, ease, light, ramp, rot_x, rot_y,
                    smooth, splat)

TITLE = "Rose"
HANDLE = "@justmade.lab"
DURATION = 15.0
GLOW = 1.0
rng = np.random.default_rng(21)

# ---------- timeline (seconds) ----------
T_SPARK = (0.0, 1.2)      # sparks swirl into one point of the soil
T_STEM = (0.6, 4.0)       # stem pushes out of the soil and grows
T_LEAF = (2.4, 4.0)       # two leaves unfold
T_BUD = (4.0, 5.5)        # a bud forms on the tip and swells
T_SEPAL = (5.5, 6.5)      # green sepals fold back
T_OPEN = (6.5, 10.0)      # petals open, outer layer first
T_BURST = (10.0, 12.0)    # full bloom: golden light + pollen
T_FADE = (13.5, 15.0)     # fade to the drifting motes, then loop
SCENES = [("stem breaks soil", 0.0, 1.0), ("stem + leaves", 0.8, 4.0),
          ("bud", *T_BUD), ("sepals", *T_SEPAL),
          ("petals open", *T_OPEN), ("bloom burst", *T_BURST),
          ("hold", 12.0, 13.5), ("fade", *T_FADE)]
POSTER_T = 11.4

# ---------- layout (model units, y down, z toward us) ----------
CY, SCALE = 0.44, 1.0     # model y = 0 (top of stem) -> screen Y 0.44
BASE_Y = 0.79             # stem base sits on the soil at screen Y 0.83
GROUND = 0.83
STEM_R = 0.022
HEAD_TILT = -0.85         # lean the flower so we look into it
SPIN = 0.25               # flower turns around its own axis, rad / s

# five petal layers, inner (0) to outer (4)
N_LAYER = [3, 5, 7, 9, 10]                       # 34 petals
P_LEN = [0.20, 0.28, 0.36, 0.44, 0.50]
P_R0 = [0.014, 0.036, 0.058, 0.080, 0.098]
P_WIDE = [0.78, 0.72, 0.68, 0.64, 0.62]          # gaps show between
P_SHUT = [0.08, 0.14, 0.20, 0.26, 0.32]          # bud angle (rad)
P_OPEN = [0.20, 0.42, 0.65, 0.88, 1.05]          # bloom angle
P_CURL = [0.15, 0.30, 0.45, 0.60, 0.75]          # tip curls back
OPEN_STEP, OPEN_DUR = 0.6, 1.1                   # outer layer first

CRIMSON = np.array([0.78, 0.05, 0.15])
SCARLET = np.array([1.00, 0.25, 0.35])
PINK = np.array([1.00, 0.60, 0.70])
GREEN = np.array([0.18, 0.65, 0.28])
SEPAL_G = np.array([0.20, 0.55, 0.25])
GOLD = np.array([1.00, 0.82, 0.40])
MOTE = np.array([0.60, 0.30, 0.30])
SOIL = np.array([0.35, 0.22, 0.15])

# ---------- petals as one batch: (petal, u along, v across) ----------
NU, NV = 18, 13
U = np.linspace(0.02, 1, NU)[None, :, None]
V = np.linspace(-1, 1, NV)[None, None, :]
layer = np.concatenate([[k] * n for k, n in enumerate(N_LAYER)])
phi = np.concatenate([np.arange(n) / n * 2 * np.pi + k * 2.4
                      for k, n in enumerate(N_LAYER)])
L_ = layer[:, None, None]
PH = phi[:, None, None]
in_layer = np.concatenate([np.arange(n) for n in N_LAYER])
P_START = (T_OPEN[0] + (4 - layer) * OPEN_STEP + in_layer * 0.05
           + rng.uniform(0, 0.08, len(layer)))
# every petal a little different
J_LEN = 1 + rng.normal(0, 0.07, len(layer))
J_TH = rng.normal(0, 0.06, len(layer))
J_CURL = rng.normal(0, 0.10, len(layer))
# outlines: both long edges and the rounded tip of every petal
UO = np.linspace(0.05, 1, 36)[None, :, None]
VO = np.array([-1.0, 1.0])[None, None, :]
UT = np.ones((1, 1, 1))
VT = np.linspace(-1, 1, 20)[None, None, :]
EDGE = np.maximum(np.abs(V) ** 4, U ** 6)        # rim of each petal
P_COL = (CRIMSON + (SCARLET - CRIMSON) * (1 - L_[..., None] / 4.0)
         * 0.8) * (0.55 + 0.45 * np.minimum(U / 0.25, 1))[..., None]


def petal_cloud(theta, curl, length, r0, cup, phi_, u=U, v=V,
                widen=0.8, reflex=0.0):
    """curved petal surfaces; returns points (n, nu, nv, 3)."""
    rad = np.stack([np.cos(phi_), 0 * phi_, np.sin(phi_)], -1)
    tan = np.stack([-np.sin(phi_), 0 * phi_, np.cos(phi_)], -1)
    up = np.array([0.0, -1.0, 0.0])
    th = theta + curl * u ** 2                    # angle along spine
    d = (np.sin(th)[..., None] * rad + np.cos(th)[..., None] * up)
    du = 1.0 / u.shape[1]
    spine = r0[..., None] * rad + np.cumsum(d, axis=1) * du \
        * length[..., None]
    w = widen * length * u ** 0.55 * (1 - 0.3 * u ** 5)
    side = tan * (v * w)[..., None]
    cupd = -rad * (cup * v ** 2 * w)[..., None]
    # the edges of an open petal roll outward
    roll = reflex * (np.clip(np.abs(v) - 0.55, 0, 1) / 0.45) ** 2
    rolld = rad * (roll * w * u)[..., None]
    return spine + side + cupd + rolld


def normals(P):
    """surface normals from the grid (n, nu, nv, 3)."""
    a = np.gradient(P, axis=1)
    b = np.gradient(P, axis=2)
    n = np.cross(a, b)
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True),
                          1e-9)


# ---------- stem: an S curve from the soil (s=0) to the tip (s=1) ----
NS, NR = 150, 10
S = np.linspace(0, 1, NS)


def stem_axis(s, t):
    sway = 0.010 * np.sin(1.2 * t + 2 * s) * s
    x = 0.045 * np.sin(np.pi * s * 1.5) + sway
    z = 0.030 * np.cos(np.pi * s * 1.2)
    return np.stack([x, BASE_Y * (1 - s), z], -1)


RING = np.linspace(0, 2 * np.pi, NR, endpoint=False)
THORN_S = np.array([0.20, 0.30, 0.45, 0.60, 0.70, 0.82])
THORN_SIDE = np.array([1, -1, 1, -1, 1, -1])
LEAF_S = np.array([0.36, 0.55])
LEAF_DIR = np.array([[-1.0, 0.0, 0.35], [1.0, 0.0, 0.25]])
LU = np.linspace(0, 1, 22)[:, None]
LV = np.linspace(-1, 1, 9)[None, :]

# ---------- particles ----------
N_MOTE = 170
M_X = rng.uniform(-1, 1, N_MOTE)
M_Y = rng.uniform(0, GROUND, N_MOTE)
M_V = rng.integers(1, 3, N_MOTE) * GROUND / DURATION   # loops exactly
M_PH = rng.uniform(0, 2 * np.pi, N_MOTE)
N_POLLEN = 320
PO_DIR = rng.normal(size=(N_POLLEN, 3))
PO_DIR[:, 1] = -np.abs(PO_DIR[:, 1]) * 0.6 - 0.1      # outward, up
PO_DIR /= np.linalg.norm(PO_DIR, axis=1, keepdims=True)
PO_SPD = rng.uniform(0.15, 0.45, N_POLLEN)
PO_T = T_BURST[0] + rng.uniform(0, 1.2, N_POLLEN)
N_SEED = 420                                     # sparks pulled in
SE_R = rng.uniform(0.25, 0.8, N_SEED)
SE_A = rng.uniform(0, 2 * np.pi, N_SEED)
SE_D = rng.uniform(0.0, 0.35, N_SEED)
N_DIRT = 70                                      # soil kicked up
DI_DIR = rng.normal(size=(N_DIRT, 2)) * [0.6, 0.0]
DI_DIR[:, 1] = -rng.uniform(0.4, 1.0, N_DIRT)
DI_SPD = rng.uniform(0.15, 0.4, N_DIRT)


def head_view(P, t):
    """flower frame -> model: spin, lean toward us, sit on the tip."""
    shp = P.shape
    Q = rot_x(rot_y(P.reshape(-1, 3), SPIN * t), HEAD_TILT)
    return Q.reshape(shp) + stem_axis(1.0, t)


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    # motes and soil (never faded: they are the loop frame)
    my = (M_Y - M_V * t) % GROUND
    tw = 0.25 + 0.75 * np.clip(np.sin(4.0 * t + M_PH), 0, 1) ** 2
    rr, cc = g.to_cell(M_X, my)
    g.put_cells(rr, cc, np.where(tw > 0.8, CIDX["+"], CIDX["."]),
                MOTE[None] * tw[:, None])
    soil = (g.Y > GROUND) & (g.Y < GROUND + 0.018)
    g.put(soil, np.where((g.c * 7 + g.r) % 3 == 0, CIDX["."],
                         CIDX["_"])[soil], SOIL, 0.6)

    # hook: sparks swirl in and sink into one point of the soil
    ks_ = np.clip((t - SE_D) / 0.85, 0, 1)
    live = (t < T_SPARK[1]) & (ks_ < 1)
    if live.any():
        r_ = SE_R * (1 - smooth(ks_))
        a_ = SE_A + 3.5 * ks_
        sx = r_ * np.cos(a_)
        sy = GROUND - 0.02 - r_ * np.abs(np.sin(a_)) * 0.55
        sl = (0.5 + 0.8 * ks_) * np.clip(t / 0.15, 0, 1)
        sch = np.where(ks_ > 0.7, CIDX["*"],
                       np.where(ks_ > 0.35, CIDX["+"], CIDX["."]))
        rr, cc = g.to_cell(sx[live], sy[live])
        g.put_cells(rr, cc, sch[live],
                    np.array([1.0, 0.55, 0.45]) * sl[live, None])

    # soil bursts where the stem breaks through
    da = ramp(t, 0.6, 1.9)
    if 0 < da < 1:
        tt = da * 1.35
        dx = DI_DIR[:, 0] * DI_SPD * tt
        dy = GROUND + DI_DIR[:, 1] * DI_SPD * tt * 0.5 \
            + 0.25 * tt ** 2
        rr, cc = g.to_cell(dx, dy)
        dl = (1 - da) * 0.9
        g.put_cells(rr, cc, np.where(np.arange(N_DIRT) % 3,
                                     CIDX["."], CIDX[","]),
                    (SOIL * 1.8 * dl)[None])
        rr, cc = g.to_cell(np.linspace(-0.1, 0.1, 21),
                           np.full(21, GROUND + 0.005))
        g.put_cells(rr, cc, CIDX["~"], (SOIL * 2.2 * dl)[None])
        # warm glow around the breaking point
        d = np.hypot(g.X / 0.12, (g.Y - GROUND) / 0.05)
        halo = (d < 1) & (g.Y < GROUND + 0.02)
        g.put(halo, CIDX["."], (np.array([1.0, 0.6, 0.35]) * dl
                                * 0.8), 1.0)

    pts, cols, lums, chars = [], [], [], []

    def add(P, c, l, ch=None):
        pts.append(P.reshape(-1, 3))
        cols.append(np.broadcast_to(c, P.shape).reshape(-1, 3))
        lums.append(np.broadcast_to(l, P.shape[:-1]).reshape(-1))
        n = lums[-1].shape[0]
        chars.append(np.full(n, -1) if ch is None
                     else np.broadcast_to(ch, (n,)))

    key = np.array([-0.45, -0.75, 0.55])

    # ----- stem -----
    grow = ease(ramp(t, *T_STEM))
    ax = stem_axis(S, t)
    tng = np.gradient(ax, axis=0)
    tng /= np.linalg.norm(tng, axis=1, keepdims=True)
    side1 = np.cross(tng, [0, 0, 1.0])
    side1 /= np.linalg.norm(side1, axis=1, keepdims=True)
    side2 = np.cross(tng, side1)
    nrm = (np.cos(RING)[None, :, None] * side1[:, None]
           + np.sin(RING)[None, :, None] * side2[:, None])
    P = ax[:, None] + STEM_R * nrm
    vis = ((S <= grow) & (grow > 0))[:, None] & np.ones(NR, bool)
    lum, _ = light(nrm.reshape(-1, 3), t, key=key, ambient=0.15,
                   key_w=0.6, rim_w=0.3, spec_w=0.1, glint_cut=9)
    lum = lum.reshape(NS, NR)
    tip = np.exp(-((S - grow) / 0.03) ** 2)[:, None] * (grow < 1)
    lum = np.where(vis, lum + 0.7 * tip, 0)
    add(P, GREEN + 0.5 * tip[..., None], lum)

    # thorns
    on = (THORN_S <= grow) & (grow > 0)
    tp = stem_axis(THORN_S, t)
    tp[:, 0] += THORN_SIDE * (STEM_R + 0.012)
    tch = np.where(THORN_SIDE > 0, CIDX[">"], CIDX["<"])
    add(tp, np.array([0.35, 0.40, 0.15]), 0.55 * on, tch)

    # ----- leaves: fold open along the midrib -----
    kl = smooth(ramp(t, *T_LEAF))
    for i in range(2):
        base = stem_axis(LEAF_S[i:i + 1], t)[0]
        dvec = LEAF_DIR[i] / np.linalg.norm(LEAF_DIR[i])
        ln = 0.17 * (0.3 + 0.7 * kl)
        spine = base + ln * (LU[..., None] * dvec
                             + 0.25 * LU[..., None] ** 2
                             * np.array([0, 1.0, 0]))
        w = 0.055 * np.sin(np.pi * LU) ** 0.8 \
            * (1 + 0.08 * np.sin(30 * LU))
        fold = 1.3 - 1.05 * kl
        perp = np.cross(dvec, [0, -1.0, 0])
        perp /= np.linalg.norm(perp)
        P = (spine + (LV * w * np.cos(fold))[..., None] * perp
             + (np.abs(LV) * w * np.sin(fold))[..., None]
             * np.array([0, -1.0, 0]))
        n = normals(P[None])[0]
        n = np.where(n[..., 2:3] < 0, -n, n)     # two-sided
        lum, _ = light(n.reshape(-1, 3), t, key=key, ambient=0.15,
                       key_w=0.65, rim_w=0.3, spec_w=0.15,
                       glint_cut=9)
        lum = lum.reshape(P.shape[:2]) * (kl > 0)
        rib = (np.abs(LV) < 0.15) * 0.25
        add(P, GREEN, lum + rib * (kl > 0))

    # ----- head: bud swells, sepals peel, petals open -----
    kb = smooth(ramp(t, *T_BUD))
    ks = smooth(ramp(t, *T_SEPAL))
    po = smooth(np.clip((t - P_START) / OPEN_DUR, 0, 1))  # per petal
    size = (0.75 * kb + 0.25 * po.mean()) * (kb > 0)
    if size > 0:
        lk = np.array(P_LEN)[layer] * J_LEN
        th = np.array(P_SHUT)[layer] + (np.array(P_OPEN)[layer]
                                       + J_TH
                                       - np.array(P_SHUT)[layer]) * po
        cu = (np.array(P_CURL)[layer] + J_CURL) * po
        cup = 0.5 - 0.25 * po

        def petals(u, v):
            c = lambda a: a[:, None, None]
            return petal_cloud(c(th), c(cu), c(lk) * size,
                               c(np.array(P_R0)[layer]) * size,
                               c(cup), PH, u, v,
                               c(np.array(P_WIDE)[layer]),
                               c(0.5 * po))
        P = petals(U, V)
        n = normals(P)
        Pv = head_view(P, t)
        nv = head_view(n, t) - stem_axis(1.0, t)
        nv = np.where(nv[..., 2:3] < 0, -nv, nv)  # two-sided
        lum, _ = light(nv.reshape(-1, 3), t, key=key, ambient=0.12,
                       key_w=0.6, rim_w=0.35, spec_w=0.2,
                       glint_cut=9)
        # darker toward the base, bright rims: each petal reads alone
        vein = 0.85 + 0.15 * np.cos(V * 9) * (U > 0.15)
        lum = lum.reshape(P.shape[:3]) * (0.5 + 0.5 * U) * vein
        # each layer's rim flares while it opens
        flare = np.sin(np.pi * po)[:, None, None] * EDGE * 0.5
        kc = smooth(ramp(t, 10.0, 10.6)) \
            * (1 - 0.5 * smooth(ramp(t, 10.8, 12.0)))
        core = kc * (1 - L_ / 4.0) * 0.45 * (1 - U)
        lum = lum + 0.6 * flare + kc * EDGE * 0.3 + core
        col = P_COL + (PINK - P_COL) * (EDGE * (0.2 * po[:, None, None]
                                                + 0.3 * kc))[..., None]
        col = col + (GOLD - col) * core[..., None]
        add(Pv, col, lum)

        # petal outlines: bright edge lines in direction glyphs, nudged
        # toward us so a front petal's rim cuts across the ones behind
        rim_on = 0.85 + 0.15 * np.sin(np.pi * po)[:, None, None]
        rim_col = np.array([1.0, 0.45, 0.55])
        for uu, vv, ax_ in ((UO, VO, 1), (UT, VT, 2)):
            E = head_view(petals(uu, vv), t)
            dE = np.gradient(E, axis=ax_)
            ech = dir_chars(dE[..., 0].ravel(), dE[..., 1].ravel())
            E = E + np.array([0, 0, 0.004])
            el = np.broadcast_to(rim_on, E.shape[:3]) * (1 + kc * 0.4)
            ec = rim_col + (PINK - rim_col) * kc * 0.5
            add(E, ec, el, ech)

        # sepals: five green blades that fold back and down
        sphi = np.arange(5)[:, None, None] / 5 * 2 * np.pi + 0.3
        sth = np.full((5, 1, 1), 0.12 + 2.2 * ks)
        sl = np.full((5, 1, 1), 0.20 * size + 0.02)
        S_ = petal_cloud(sth, np.full((5, 1, 1), 0.3 * ks), sl,
                         np.full((5, 1, 1), 0.05 * size), 0.3, sphi,
                         U, V, widen=0.35)
        sn = head_view(normals(S_), t) - stem_axis(1.0, t)
        sn = np.where(sn[..., 2:3] < 0, -sn, sn)
        sl_, _ = light(sn.reshape(-1, 3), t, key=key, ambient=0.15,
                       key_w=0.6, rim_w=0.3, spec_w=0.1, glint_cut=9)
        add(head_view(S_, t), SEPAL_G, sl_.reshape(S_.shape[:3]))

    # ----- pollen: bursts from the heart and drifts up -----
    age = t - PO_T
    alive = (age > 0) & (age < 3.5)
    heart = head_view(np.array([[0.0, -0.06, 0.0]]), t)[0]
    a = np.clip(age, 0, None)[:, None]
    pp = heart + PO_DIR * PO_SPD[:, None] * a ** 0.6 \
        + np.array([0, -0.04, 0]) * a
    pl = np.where(alive, 1.2 * np.exp(-np.clip(age, 0, None) / 1.6), 0)
    pch = np.where(np.arange(N_POLLEN) % 5 == 0, CIDX["*"],
                   np.where(np.arange(N_POLLEN) % 2, CIDX["."],
                            CIDX["+"]))
    add(pp, GOLD * 1.3, pl, pch)

    allP = np.concatenate(pts)
    allC = np.concatenate(cols) * fade
    allL = np.clip(np.concatenate(lums), 0, 1)
    n_lit = splat(g, allP, allC, allL, np.concatenate(chars),
                  cy=CY, scale=SCALE)

    # ----- light burst: rays from the heart, drawn over the petals ---
    kr = smooth(ramp(t, 10.0, 10.5)) * (1 - 0.6 * smooth(ramp(t, 10.6,
                                                              12.0)))
    if kr > 0:
        rp, rl, rc = [], [], []
        for k in range(16):
            ang = k / 16 * 2 * np.pi
            ln = 0.12 + 0.48 * kr * (1 + 0.35 * np.cos(4 * ang))
            s = np.linspace(0.06, ln, 16)
            rp.append(heart + np.stack([np.cos(ang) * s,
                                        np.sin(ang) * s,
                                        np.full_like(s, 0.3)], -1))
            rl.append((1 - 0.85 * s / ln) * kr)
            rc.append(dir_chars(np.full(16, np.cos(ang)),
                                np.full(16, np.sin(ang))))
        rp = np.concatenate(rp)
        splat(g, rp, np.broadcast_to(GOLD * 2.4 * fade, rp.shape),
              np.concatenate(rl), np.concatenate(rc), cy=CY,
              scale=SCALE)

    petals = int(round(po.sum()))
    layers = int(sum(po[layer == k].min() > 0.99 for k in range(5)))
    return [HANDLE,
            f"petals {petals:2d}   layers {layers}   "
            f"bloom {po.mean() * 100:3.0f}%",
            f"letters {n_lit:,}"]
