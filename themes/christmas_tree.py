"""christmas_tree: a ribbon of light draws a tree, then it ignites."""
import numpy as np
from engine import (CIDX, Snow, dir_chars, ease, light, noise2d,
                    pic_coords, pop, ramp, rot_x, rot_y, smooth,
                    splat, vgradient)

TITLE = "Christmas Tree"
HANDLE = "@justmade.lab"
DURATION = 15.0
GLOW = 1.05
rng = np.random.default_rng(25)

# ---------- timeline (seconds) ----------
T_RIBBON = (0.0, 4.5)     # light ribbon spirals up and draws the tree
T_BULBS = (4.5, 7.5)      # 480 bulbs light up, bottom to top
T_ORN = (5.0, 7.5)        # 60 ornaments pop in
T_CHASE = (7.5, 9.0)      # colours chase upward
T_CHARGE = (9.0, 9.6)     # sparks rush up, the star fills
T_IGNITE = 9.6            # star ignites: flash + shockwave
T_TEXT = (10.0, 11.4)     # MERRY CHRISTMAS types out
T_FADE = (13.5, 15.0)     # fade to sky and snow, then loop
BURSTS = [9.9, 10.3, 10.7, 11.0, 11.4, 11.8, 12.2]   # fireworks
SCENES = [("hook", 0.0, 1.0), ("ribbon draws tree", 0.5, 4.5),
          ("bulbs + ornaments", 4.5, 7.5), ("colour chase", *T_CHASE),
          ("star charges", *T_CHARGE),
          ("ignite + fireworks", 9.6, 12.5),
          ("hold", 12.5, 13.5), ("fade", *T_FADE)]
POSTER_T = 11.6

# ---------- layout (model units, y down, z toward us) ----------
CY = 0.47                 # model y = 0 -> screen Y 0.47
APEX, BASE = -0.59, 0.59  # tree tip and base (screen Y 0.18 .. 0.76)
TRUNK_Y = 0.67            # trunk bottom (screen Y 0.80)
GROUND = 0.80
SPIN, TILT = 0.35, -0.15  # tree turns; we look slightly down on it
STAR_Y = CY + (APEX - 0.09) * 540 / 1098      # star centre on screen
STAR_R, STAR_IN = 0.11, 0.045                 # outer / inner radius
ASPECT = 1098 / 540       # screen Y units -> X units

# four tiers along the height h (0 tip .. 1 base)
TIERS = [(0.00, 0.32, 0.02, 0.17), (0.22, 0.55, 0.08, 0.26),
         (0.45, 0.80, 0.12, 0.35), (0.70, 1.00, 0.18, 0.42)]

SKY_TOP = (0.01, 0.02, 0.08)
SKY_LOW = (0.04, 0.07, 0.22)
EMERALD = np.array([0.10, 0.75, 0.35])
GOLD = np.array([1.00, 0.82, 0.35])
WHITE = np.array([1.00, 0.95, 0.85])
RED = np.array([1.00, 0.20, 0.20])
SNOW_C = np.array([0.85, 0.90, 1.00])
BULB_C = np.stack([GOLD, RED, WHITE])
ORN_C = np.array([[1.0, 0.18, 0.18], [1.0, 0.80, 0.30],
                  [0.85, 0.88, 0.95], [0.30, 0.50, 1.00]])
FW_C = np.array([[1.0, 0.25, 0.25], [1.0, 0.82, 0.35],
                 [0.30, 1.00, 0.45], [0.40, 0.80, 1.00],
                 [1.0, 0.45, 0.80], [0.70, 0.45, 1.00],
                 [1.0, 1.00, 1.00]])


def radius(h):
    """tree radius and skirt shadow at height h (0 tip .. 1 base)."""
    h = np.asarray(h, float)
    r = np.zeros_like(h)
    shade = np.ones_like(h)
    for k, (a, b, r0, r1) in enumerate(TIERS):
        u = (h - a) / (b - a)
        m = (u >= 0) & (u <= 1)
        rr = r0 + (r1 - r0) * np.clip(u, 0, 1) ** 0.9
        r = np.where(m, np.maximum(r, rr), r)
        if k:
            dark = 0.35 + 0.65 * np.clip(u * 3.5, 0, 1)
            shade = np.where(m & (u < 0.3), dark, shade)
    return r, shade


def ypos(h):
    return APEX + (BASE - APEX) * h


def on_cone(h, ang, out=1.0):
    r, _ = radius(h)
    r = r * out
    return np.stack([r * np.cos(ang), ypos(h), r * np.sin(ang)], -1)


def view(P, t):
    return rot_x(rot_y(P, SPIN * t), TILT)


# ---------- tree, trunk ----------
N_TREE = 9000
TH = rng.random(N_TREE) ** 0.8
TA = rng.uniform(0, 2 * np.pi, N_TREE)
TJ = 0.92 + 0.12 * rng.random(N_TREE)            # needle jitter
TREE = on_cone(TH, TA, TJ)
TN = np.stack([np.cos(TA), -0.35 + 0 * TA, np.sin(TA)], -1)
_, TSHADE = radius(TH)
TRK_H = rng.uniform(0, 1, 500)
TRK_A = rng.uniform(0, 2 * np.pi, 500)
TRUNK = np.stack([0.05 * np.cos(TRK_A),
                  BASE + (TRUNK_Y - BASE) * TRK_H,
                  0.05 * np.sin(TRK_A)], -1)

# ribbon / garland: 5 turns from the front of the base to the tip
NQ = 900
Q = np.linspace(0, 1, NQ)


def spiral(q):
    return on_cone(1 - q, np.pi / 2 + 2 * np.pi * 5 * q, 1.06)


GARLAND = spiral(Q)
# when does the ribbon head pass each q? (inverse of smoothstep)
_tt = np.linspace(*T_RIBBON, 2000)
_qq = smooth(np.clip((_tt - T_RIBBON[0])
                     / (T_RIBBON[1] - T_RIBBON[0]), 0, 1))
N_SPARK = 260
SP_Q = rng.uniform(0, 1, N_SPARK)
SP_T = np.interp(SP_Q, _qq, _tt)
SP_V = rng.normal(0, 0.25, (N_SPARK, 3))

# bulbs: 3 strands x 160 on the cone
N_BULB = 480
BQ = (np.arange(160) + 0.5) / 160
BH = np.tile(1 - BQ * 0.96, 3)
BA = np.concatenate([np.pi / 2 + 2 * np.pi * 4 * BQ + s * 2.094
                     for s in range(3)])
BULB = on_cone(BH, BA, 1.03)
B_ON = T_BULBS[0] + (T_BULBS[1] - T_BULBS[0]) * (1 - BH)
B_PH = rng.uniform(0, 2 * np.pi, N_BULB)

# ornaments
N_ORN = 60
OH = rng.uniform(0.12, 0.95, N_ORN)
OA = rng.uniform(0, 2 * np.pi, N_ORN)
ORN = on_cone(OH, OA, 1.05)
O_T = np.sort(rng.uniform(*T_ORN, N_ORN))
O_K = rng.integers(0, 4, N_ORN)

# star charge sparks
N_CHG = 220
CG = TREE[rng.integers(0, N_TREE, N_CHG)]
CG_D = rng.uniform(0, 0.3, N_CHG)

# fireworks: 7 bursts behind the tree (screen space, z = -1.4)
FW_Z = -1.4
FW_K = 3.2 / (3.2 - FW_Z)
FW_X = np.array([-0.62, 0.55, -0.25, 0.70, -0.70, 0.20, -0.05])
FW_Y = np.array([0.20, 0.16, 0.10, 0.30, 0.34, 0.08, 0.24])
N_FP = 120
FP_A = rng.uniform(0, 2 * np.pi, (7, N_FP))
FP_S = rng.uniform(0.25, 0.50, (7, N_FP))
FP_C = rng.integers(0, 7, (7, 2))

# sky, stars, snow
PX, PY = pic_coords()
SKY = vgradient([(0.0, SKY_TOP), (GROUND, SKY_LOW),
                 (GROUND, (0.10, 0.13, 0.25)),
                 (1.0, (0.05, 0.06, 0.12))])
DRIFT = noise2d(128, beta=2.0, seed=7)
N_STAR = 150
S_X = rng.uniform(-1, 1, N_STAR)
S_Y = rng.uniform(0, 0.62, N_STAR)
S_PH = rng.uniform(0, 2 * np.pi, N_STAR)
snow = Snow(rng, n=280)
FRONT = rng.random(280) < 0.28


def to_model(X, Y, z):
    """screen point -> model point at depth z (for the z-buffer)."""
    k = 3.2 / (3.2 - z)
    return np.stack([X / k, (Y - CY) / (k * 540 / 1098),
                     np.full_like(X, z)], -1)


def star_shape(g, t):
    """polar distance of every cell to the star outline."""
    dx = g.X
    dy = (g.Y - STAR_Y) * ASPECT
    d = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    rot = 0.08 * np.sin(0.7 * t)
    f = ((th + np.pi / 2 - rot) / (2 * np.pi / 5)) % 1.0
    edge = STAR_IN + (STAR_R - STAR_IN) * np.abs(1 - 2 * f)
    return d, edge, dy


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    ign = smooth(ramp(t, T_IGNITE, T_IGNITE + 0.35))
    flash = np.exp(-((t - T_IGNITE) / 0.12) ** 2)
    pulse = 1.0 + 0.25 * np.sin(8 * t)

    # ---------- picture layer: sky, glows, firework tints ----------
    under = SKY.copy()
    sd = np.hypot(PX, (PY - STAR_Y) * ASPECT)
    halo = (ign * (0.35 + 0.1 * np.sin(8 * t)) + 0.6 * flash) \
        * np.exp(-sd / 0.16)
    under += halo[..., None] * GOLD * fade
    under += (0.16 * flash * fade) * np.ones(3)
    lit = smooth(ramp(t, *T_BULBS))
    gd = np.hypot(PX / 0.6, (PY - GROUND) * 5)
    under += (0.12 * lit * np.exp(-gd) * fade)[..., None] * GOLD
    qh = smooth(ramp(t, *T_RIBBON))
    if 0 < qh < 1:                       # glow around the ribbon head
        hp = view(spiral(np.array([qh])), t)[0]
        k = 3.2 / (3.2 - hp[2])
        hx, hy = hp[0] * k, CY + hp[1] * k * 540 / 1098
        hd = np.hypot(PX - hx, (PY - hy) * ASPECT)
        a_in = np.clip(t / 0.2, 0, 1)
        under += (0.5 * a_in * np.exp(-hd / 0.05))[..., None] * GOLD
    n_fw = 0
    for b, tb in enumerate(BURSTS):
        age = t - tb
        if age > 0:
            n_fw += 1
            tint = 0.10 * np.exp(-age / 0.35) * fade
            under[PY < GROUND] += tint * FW_C[FP_C[b, 0]]

    # ---------- stars + back snow ----------
    tw = 0.3 + 0.7 * np.clip(np.sin(2.4 * t + S_PH), 0, 1) ** 3
    rr, cc = g.to_cell(S_X, S_Y)
    sch = np.where(tw > 0.8, CIDX["*"],
                   np.where(tw > 0.5, CIDX["+"], CIDX["."]))
    g.put_cells(rr, cc, sch, SNOW_C[None] * (tw * 0.6)[:, None])
    snow.draw(g, t * 0.5, 0.55, ~FRONT)
    gm = (g.Y > GROUND) & (g.Y < GROUND + 0.016)
    g.put(gm, np.where((g.c + g.r) % 4 == 0, CIDX["~"], CIDX["_"])[gm],
          SNOW_C, 0.35)

    pts, cols, lums, chars = [], [], [], []

    def add(P, c, l, ch=None):
        P = np.asarray(P, float).reshape(-1, 3)
        n = len(P)
        pts.append(P)
        cols.append(np.broadcast_to(np.asarray(c, float),
                                    (n, 3)).copy())
        lums.append(np.broadcast_to(np.asarray(l, float), (n,)))
        chars.append(np.full(n, -1) if ch is None
                     else np.broadcast_to(ch, (n,)))

    key = np.array([-0.4, -0.7, 0.6])

    # ---------- ribbon head, garland, tree reveal ----------
    head_h = 1 - qh
    vis = (TH > head_h) & (qh > 0)
    lum, _ = light(view(TN, t), t, key=key, ambient=0.15, key_w=0.6,
                   rim_w=0.3, spec_w=0.1, glint_cut=9)
    lum = lum * TSHADE * (0.8 + 0.4 * lit)
    grow = np.exp(-((TH - head_h) / 0.03) ** 2) * (qh < 1)
    tc = EMERALD + (GOLD - EMERALD) * (0.15 * lit + 0.6 * grow[:, None])
    add(view(TREE, t), tc, np.where(vis, lum + 0.8 * grow, 0))
    trunk_l = 0.45 * (head_h < 0.95) * (qh > 0)
    add(view(TRUNK, t), np.array([0.55, 0.32, 0.15]), trunk_l)

    gv = view(GARLAND, t)
    gt = np.gradient(gv, axis=0)
    gch = dir_chars(gt[:, 0], gt[:, 1])
    gon = Q <= qh
    gl = np.where(gon, 0.5 + 0.2 * np.sin(6 * t - 30 * Q), 0)
    add(gv, GOLD, gl, gch)
    if 0 < qh < 1:
        hp = view(spiral(np.array([qh])), t)
        comet = np.clip(1 - (qh - Q) / 0.05, 0, 1) * (Q <= qh)
        add(gv, GOLD * 1.6, comet, gch)
        add(hp, WHITE * 1.8, np.clip(t / 0.2, 0, 1), CIDX["@"])
    # sparks thrown off the ribbon head
    age = t - SP_T
    al = (age > 0) & (age < 0.7)
    if al.any():
        base = np.stack([rot_y(spiral(SP_Q[i:i + 1]), SPIN * SP_T[i])[0]
                         for i in np.nonzero(al)[0]])
        a_ = age[al][:, None]
        fall = np.array([0, 0.6, 0]) * a_ ** 2
        sp = rot_x(base + SP_V[al] * a_ + fall, TILT)
        sl = 1.1 * (1 - age[al] / 0.7)
        sch = np.where(np.arange(len(sl)) % 3 == 0,
                       CIDX["*"], CIDX["+"])
        add(sp, GOLD * 1.4, sl, sch)
    # top flash when the ribbon reaches the tip
    tip = np.exp(-((t - T_RIBBON[1]) / 0.15) ** 2)

    # ---------- bulbs: chain lighting, chase, climax waves ----------
    on = t >= B_ON
    pk = np.clip((t - B_ON) / 0.25, 0, 1)
    wave = int(4 * t) if t > T_CHASE[0] else 0
    ci = (np.arange(N_BULB) + wave - (6 * (1 - BH)).astype(int)) % 3
    ci = np.where(t > T_CHASE[0], ci, np.arange(N_BULB) % 3)
    tw = 0.7 + 0.3 * np.sin(5 * t + B_PH)
    bl = np.where(on, tw * (1 + 0.8 * (1 - pk)), 0)
    bch = np.where(pk < 1, CIDX["*"], np.where(tw > 0.9, CIDX["*"],
                                              CIDX["+"]))
    add(view(BULB, t), BULB_C[ci] * 1.5, bl, bch)
    n_lights = int(on.sum())

    # ---------- fireworks (behind the tree, same z-buffer) ----------
    for b, tb in enumerate(BURSTS):
        rise = ramp(t, tb - 0.45, tb)
        if 0 < rise < 1:
            ry = GROUND - (GROUND - FW_Y[b]) * ease(rise)
            ys = ry + np.linspace(0, 0.08, 8)
            add(to_model(np.full(8, FW_X[b]), ys, FW_Z), WHITE,
                np.linspace(1, 0.2, 8), CIDX["|"])
        age = t - tb
        if 0 < age < 1.8:
            for lag, w in ((0.0, 1.0), (0.05, 0.6), (0.10, 0.35)):
                a_ = max(age - lag, 0)
                rad = FP_S[b] * (1 - np.exp(-a_ * 2.5)) / 2.5 * 2.2
                X = FW_X[b] + rad * np.cos(FP_A[b])
                Y = FW_Y[b] + (rad * np.sin(FP_A[b]) + 0.09 * a_ ** 2) \
                    / ASPECT
                vx = np.cos(FP_A[b])
                vy = np.sin(FP_A[b]) + 0.3 * a_
                ch = dir_chars(vx, vy) if lag else np.where(
                    np.arange(N_FP) % 4 == 0, CIDX["*"], CIDX["+"])
                cidx = np.where(np.arange(N_FP) % 2, FP_C[b, 0],
                                FP_C[b, 1])
                fl = w * 1.6 * np.exp(-age / 1.0) \
                    * (0.7 + 0.3 * np.sin(20 * age + FP_A[b] * 5))
                add(to_model(X, Y, FW_Z), FW_C[cidx] * 1.4, fl, ch)

    # ---------- star charge: sparks rush to the tip ----------
    kc = ramp(t, *T_CHARGE)
    if 0 < kc < 1:
        k_ = smooth(np.clip((kc - CG_D) / 0.7, 0, 1))[:, None]
        tgt = np.array([0, APEX - 0.09, 0.1])
        cp = view(CG, t) * (1 - k_) + tgt * k_
        add(cp, GOLD * 1.5, 0.9 * (1 - k_[:, 0] ** 4), CIDX["*"])

    allP = np.concatenate(pts)
    allC = np.concatenate(cols) * fade
    allL = np.clip(np.concatenate(lums), 0, 1)
    n_lit = splat(g, allP, allC, allL, np.concatenate(chars), cy=CY)

    # ---------- ornaments: sprites, front side only ----------
    ov = view(ORN, t)
    ok = np.clip((t - O_T) / 0.35, 0, 1)
    front = (ov[:, 2] > 0.02) & (ok > 0)
    sx = ov[:, 0] * 3.2 / (3.2 - ov[:, 2])
    sy = CY + ov[:, 1] * 3.2 / (3.2 - ov[:, 2]) * 540 / 1098
    sprites = dict(x=[], y=[], ch=[], size=[], rgb=[])
    for i in np.nonzero(front)[0]:
        s = np.clip(pop(ok[i]), 0, 1.3)
        c = ORN_C[O_K[i]] * (1.0 + 0.4 * lit) * fade
        sprites["x"] += [sx[i], sx[i] - 0.008]
        sprites["y"] += [sy[i], sy[i] - 0.006]
        sprites["ch"] += ["O", "'"]
        sprites["size"] += [26 * s + 4, 14 * s + 4]
        sprites["rgb"] += [c, WHITE * 1.2 * fade]
        if ok[i] < 1:                                # pop ring
            ra = 0.015 + 0.05 * ok[i]
            ang = np.linspace(0, 2 * np.pi, 10, endpoint=False)
            rr, cc = g.to_cell(sx[i] + ra * np.cos(ang),
                               sy[i] + ra * np.sin(ang) / ASPECT)
            g.put_cells(rr, cc, CIDX["."],
                        (ORN_C[O_K[i]] * 1.4 * (1 - ok[i]))[None])
    n_orn = int((ok > 0).sum())

    # ---------- the star: outline, charge fill, ignite ----------
    d, edge, dy = star_shape(g, t)
    shown = qh >= 1
    if shown:
        rim = np.abs(d - edge) < 0.012
        dim = 0.45 + 0.8 * tip
        g.put(rim, CIDX["*"], GOLD * dim * fade, 1.0)
        fill = max(kc, ign)
        body = (d < edge) & (dy > STAR_R - 2 * STAR_R * smooth(fill))
        core = d < 0.5 * edge
        col = GOLD * (0.9 + 0.7 * ign) * pulse + WHITE * flash
        g.put(body & core, CIDX["@"], (WHITE * 1.2 + col * 0.3) * fade)
        g.put(body & ~core, CIDX["#"], col * fade)
        g.put(rim & (ign > 0), CIDX["*"], WHITE * 1.5 * fade, 1.0)
    if ign > 0:
        # rotating rays + long cross flare + orbiting sparkles
        rows, cols_, chs, cl = [], [], [], []
        for k in range(16):
            a = k / 16 * 2 * np.pi + 0.3 * (t - T_IGNITE)
            ln = (0.14 if k % 2 else 0.24) * ign * pulse
            s = np.linspace(STAR_R * 1.05, STAR_R + ln, 10)
            rows.append(s * np.cos(a))
            cols_.append(s * np.sin(a))
            chs.append(dir_chars(np.full(10, np.cos(a)),
                                 np.full(10, np.sin(a))))
            cl.append(np.linspace(1.3, 0.2, 10))
        for a, ln in ((0, 0.55), (np.pi / 2, 0.30), (np.pi, 0.55),
                      (-np.pi / 2, 0.22)):
            ln = ln * ign * (0.85 + 0.15 * np.sin(6 * t))
            s = np.linspace(STAR_R, STAR_R + ln, 40)
            rows.append(s * np.cos(a))
            cols_.append(s * np.sin(a))
            chs.append(dir_chars(np.full(40, np.cos(a)),
                                 np.full(40, np.sin(a))))
            cl.append(np.linspace(1.6, 0.1, 40))
        oa = np.linspace(0, 2 * np.pi, 12, endpoint=False) + 1.5 * t
        orr = STAR_R * 1.5
        rows.append(orr * np.cos(oa))
        cols_.append(orr * np.sin(oa))
        chs.append(np.full(12, CIDX["*"]))
        cl.append(0.8 + 0.6 * np.clip(np.sin(9 * t + oa * 3), 0, 1))
        X = np.concatenate(rows)
        Y = STAR_Y + np.concatenate(cols_) / ASPECT
        L = np.concatenate(cl) * ign
        rr, cc = g.to_cell(X, Y)
        rc = (WHITE * 0.5 + GOLD * 0.9)[None] * (L * fade)[:, None]
        g.put_cells(rr, cc, np.concatenate(chs), rc)
        # shockwave ring
        age = t - T_IGNITE
        if age < 0.9:
            ring = np.abs(np.hypot(g.X, (g.Y - STAR_Y) * ASPECT)
                          - age * 1.9) < 0.03
            g.put(ring, np.where((g.c + g.r) % 2, CIDX["o"],
                                 CIDX["."])[ring],
                  (WHITE * 0.6 + GOLD * 0.6) * (1 - age / 0.9) * fade)

    # ---------- caption sparkle + front snow ----------
    pt = ramp(t, *T_TEXT)
    text = "MERRY CHRISTMAS"
    n_typed = int(round(pt * len(text)))
    if 0 < pt:
        m = (np.abs(g.Y - 0.835) < 0.03) & (np.abs(g.X) < 0.75 * pt)
        tw2 = np.sin(13 * t + g.c * 1.7 + g.r * 3.1) > 0.93
        g.put(m & tw2, CIDX["*"], GOLD * 1.2 * fade)
    snow.draw(g, t * 0.5, 0.9, FRONT)

    caption = (text, n_typed, 0.835, GOLD * 1.1 * fade, 46, 0.35,
               0 < pt < 1 and int(t * 4) % 2 == 0)
    if 0 < qh < 1:                       # big bright ribbon head
        sprites["x"].append(hx)
        sprites["y"].append(hy)
        sprites["ch"].append("@")
        sprites["size"].append(34)
        sprites["rgb"].append(WHITE * 1.6 * a_in)
    if not sprites["x"]:
        sprites = None
    return {"under": under, "sprites": sprites, "caption": caption,
            "hud": [HANDLE,
                    f"lights {n_lights}   ornaments {n_orn}   "
                    f"fireworks {n_fw}",
                    f"letters {n_lit:,}"]}
