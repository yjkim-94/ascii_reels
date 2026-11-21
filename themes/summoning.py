"""summoning: four mages draw four circles and call a phoenix."""
import numpy as np
from engine import (CIDX, dir_chars, ease, noise2d, pic_coords, pop,
                    ramp, smooth, splat, vgradient)

TITLE = "Summoning"
HANDLE = "@justmade.lab"
DURATION = 20.0
GLOW = 1.1
rng = np.random.default_rng(31)

# ---------- timeline (seconds) ----------
T_SPARK = (0.0, 0.5)      # a golden spark falls to the centre
T_SEAL = (0.5, 1.4)       # a faint ring spreads, the fog draws back
T_MAGES = (0.8, 3.0)      # four hooded mages appear in the fog
T_CAST = [3.0, 5.0, 7.0, 9.0]   # fire, water, wind, earth (2 s each)
T_UNITE = (11.0, 13.0)    # beams meet, the great circle, a pillar
T_PHOENIX = (13.0, 16.5)  # the phoenix bursts out of the pillar
T_FADE = (18.5, 20.0)     # it scatters into embers, fade, loop
SCENES = [("spark + seal", 0.0, 1.2), ("mages appear", *T_MAGES),
          ("fire", 3.0, 5.0), ("water", 5.0, 7.0),
          ("wind", 7.0, 9.0), ("earth", 9.0, 11.0),
          ("great circle", *T_UNITE), ("phoenix", *T_PHOENIX),
          ("hold", 16.5, 18.5), ("fade", *T_FADE)]
POSTER_T = 15.2

# ---------- the field: ground plane seen from a raised camera -------
HORIZON = 0.42            # screen Y of the horizon
CAM = 1.0                 # camera height above the ground
YU = 540 / 1098           # screen Y units per X unit
ZC = 2.4                  # depth of the field centre
MAGE_R = 1.0              # mages stand this far from the centre
CIRCLE_R = 0.35           # each mage's own circle
GREAT_R = 0.62            # the great circle in the middle
ASPECT = 1098 / 540

FIRE = np.array([[1.0, 0.85, 0.30], [1.0, 0.45, 0.10],
                 [1.0, 0.15, 0.10]])
WATER = np.array([[0.30, 0.70, 1.00], [0.15, 0.35, 1.00]])
WIND = np.array([[0.55, 1.00, 0.75], [0.35, 0.85, 0.40]])
EARTH = np.array([[1.00, 0.70, 0.30], [0.55, 0.35, 0.15]])
ELEM = np.array([FIRE[1], WATER[0], WIND[0], EARTH[0]])
GOLD = np.array([1.00, 0.80, 0.35])
WHITE = np.array([1.00, 0.97, 0.90])
FOG = np.array([0.20, 0.15, 0.30])
ROBE = np.array([0.03, 0.02, 0.05])

# order of casting: fire front-left, water back-right,
# wind back-left, earth front-right
d = MAGE_R * 0.707
MAGE = np.array([[-d, ZC - d], [d, ZC + d], [-d, ZC + d],
                 [d, ZC - d]])
RUNES = "RZAXKVTHNMWYF<>^#S"


def proj(x, h, z):
    """ground point x, height h, depth z -> screen X, Y, scale."""
    z = np.maximum(np.asarray(z, float), 0.05)
    return (np.asarray(x) / z,
            HORIZON + (CAM - np.asarray(h)) / z * YU, 1 / z)


def ring_pts(cx, cz, r, a0, a1, n):
    a = np.linspace(a0, a1, n)
    return cx + r * np.cos(a), cz + r * np.sin(a)


def draw_line(g, X, Y, col, lum, ch=None):
    """polyline on the grid; glyphs follow the screen direction."""
    if len(X) < 2:
        return
    dx, dy = np.gradient(X), np.gradient(Y) * ASPECT
    chars = dir_chars(dx, dy) if ch is None else ch
    rr, cc = g.to_cell(X, Y)
    c = np.broadcast_to(np.asarray(col) * np.asarray(lum)[..., None]
                        if np.ndim(lum) else np.asarray(col) * lum,
                        (len(X), 3))
    g.put_cells(rr, cc, chars, c)


def sigil(kind, cx, cz, r, p):
    """element sign inside a circle, drawn up to progress p."""
    pts = []
    if kind == 0:                                 # fire: triangle
        a = np.pi / 2 + np.array([0, 2.094, 4.189, 6.283])
        for i in range(3):
            s = np.linspace(0, 1, 30)
            pts.append((cx + r * ((1 - s) * np.cos(a[i])
                                  + s * np.cos(a[i + 1])),
                        cz + r * ((1 - s) * np.sin(a[i])
                                  + s * np.sin(a[i + 1]))))
    elif kind == 1:                               # water: waves
        for k in (-0.4, 0, 0.4):
            s = np.linspace(-0.8, 0.8, 40)
            pts.append((cx + r * s,
                        cz + r * (k + 0.12 * np.sin(s * 9))))
    elif kind == 2:                               # wind: spiral
        s = np.linspace(0, 1, 90)
        pts.append((cx + r * 0.9 * s * np.cos(s * 12),
                    cz + r * 0.9 * s * np.sin(s * 12)))
    else:                                         # earth: square
        c = np.array([[1, 1], [-1, 1], [-1, -1], [1, -1], [1, 1]])
        for i in range(4):
            s = np.linspace(0, 1, 25)[:, None]
            q = (c[i] * (1 - s) + c[i + 1] * s) * 0.6
            pts.append((cx + r * q[:, 0], cz + r * q[:, 1]))
    n = int(round(p * len(pts) * 1000))
    out = []
    for i, (x, z) in enumerate(pts):
        m = int(np.clip(n - i * 1000, 0, 1000) / 1000 * len(x))
        if m > 1:
            out.append((x[:m], z[:m]))
    return out


# ---------- fixed fields ----------
PX, PY = pic_coords()
SKY = vgradient([(0.0, (0.03, 0.01, 0.06)), (HORIZON, (0.12, 0.04,
                                                        0.10)),
                 (HORIZON, (0.05, 0.03, 0.08)),
                 (1.0, (0.02, 0.01, 0.04))])
CLOUD = noise2d(256, beta=2.2, seed=3)
MIST = noise2d(256, beta=1.8, seed=4)
RIDGE = noise2d(256, beta=2.6, seed=5)

# element spell particles
N_SP = 320
SP_PH = rng.uniform(0, 1, (4, N_SP))
SP_A = rng.uniform(0, 2 * np.pi, (4, N_SP))
CR_A = rng.uniform(0, 2 * np.pi, 12)              # earth crystals
CR_R = rng.uniform(0.05, 0.3, 12)
CR_H = rng.uniform(0.4, 0.95, 12)
CR_T = rng.uniform(0, 0.6, 12)

# phoenix
N_EMB = 320
EM_T = T_PHOENIX[0] + 0.3 + np.arange(N_EMB) / N_EMB * 6.0
EM_U = rng.uniform(0.2, 1.0, N_EMB)
EM_S = rng.choice([-1.0, 1.0], N_EMB)
EM_V = rng.normal(0, 0.12, (N_EMB, 2))
N_BURST = 300
BU_A = rng.uniform(0, 2 * np.pi, N_BURST)
BU_S = rng.uniform(0.3, 1.0, N_BURST)
WU = np.linspace(0, 1, 46)[:, None]
WV = np.linspace(0, 1, 16)[None, :]
TAIL_C = np.array([FIRE[1], WATER[0], WIND[1], EARTH[0], FIRE[2]])


def phoenix_points(t, spread):
    """phoenix in its own model frame; returns P, colour, lum, chars."""
    flap = 0.45 * np.sin(2 * np.pi * 1.0 * t) * spread \
        + 1.2 * (1 - spread)
    P, C, L, CH = [], [], [], []
    for sg in (-1, 1):
        x = sg * (0.06 + 0.82 * WU)
        y = -0.05 - 0.22 * np.sin(np.pi * WU * 0.85)
        notch = 0.5 * (1 + np.cos(2 * np.pi * 9 * WU))
        chord = 0.24 * (1 - 0.45 * WU) + 0.12 * WU * notch
        yy = y + WV * chord
        zz = 0.08 * np.sin(np.pi * WU) - 0.05 * WV
        # flap: rotate around the shoulder in the screen plane
        ang = -sg * flap * WU ** 0.8
        sx, sy = sg * 0.06, -0.05
        xr = sx + (x - sx) * np.cos(ang) - (yy - sy) * np.sin(ang)
        yr = sy + (x - sx) * np.sin(ang) + (yy - sy) * np.cos(ang)
        pts = np.stack([xr, yr, np.broadcast_to(zz, xr.shape)], -1)
        P.append(pts.reshape(-1, 3))
        L.append((0.55 + 0.45 * np.sin(23 * WU - 11 * t + WV * 5)
                  ** 2 * (1 - 0.5 * WV)).ravel())
        CH.append(np.full(pts.shape[0] * pts.shape[1], -1))
    # body and head
    P.append(BODY)
    L.append(np.full(len(BODY), 0.95))
    CH.append(np.full(len(BODY), -1))
    # tail: five streamers in the four element colours
    s = np.linspace(0, 1, 70)
    for k in range(5):
        tx = (k - 2) * 0.09 * s + 0.05 * np.sin(4 * s - 3 * t + k)
        ty = 0.16 + 0.62 * s
        tp = np.stack([tx, ty, -0.05 * s], -1)
        P.append(tp)
        L.append(1.0 - 0.7 * s)
        CH.append(dir_chars(np.gradient(tx), np.gradient(ty)))
    P = np.concatenate(P)
    L = np.concatenate(L)
    CH = np.concatenate(CH)
    dist = np.hypot(P[:, 0], P[:, 1] * 1.4)
    k1 = np.clip(dist / 0.35, 0, 1)[:, None]
    k2 = np.clip((dist - 0.35) / 0.5, 0, 1)[:, None]
    C = (FIRE[0] * 1.4) * (1 - k1) + FIRE[1] * 1.3 * k1
    C = C * (1 - k2) + FIRE[2] * 1.2 * k2
    nt = 70 * 5
    tail_c = np.repeat(TAIL_C, 70, axis=0) * 1.4
    C[-nt:] = tail_c
    return P, C, L, CH


_b = rng.normal(size=(700, 3))
_b /= np.linalg.norm(_b, axis=1, keepdims=True)
BODY = np.concatenate([_b * [0.07, 0.17, 0.07],
                       _b[:200] * 0.055 + [0, -0.22, 0.02]])


def wing_point(u, sg, t, spread):
    """a point on the leading edge of a wing (for embers)."""
    flap = 0.45 * np.sin(2 * np.pi * t) * spread + 1.2 * (1 - spread)
    x = sg * (0.06 + 0.82 * u)
    y = -0.05 - 0.22 * np.sin(np.pi * u * 0.85) + 0.12
    ang = -sg * flap * u ** 0.8
    sx, sy = sg * 0.06, -0.05
    xr = sx + (x - sx) * np.cos(ang) - (y - sy) * np.sin(ang)
    yr = sy + (x - sx) * np.sin(ang) + (y - sy) * np.cos(ang)
    return xr, yr


def phoenix_state(t):
    """rise (0..1), wing spread (0..1), screen centre Y, scale."""
    k = smooth(ramp(t, T_PHOENIX[0], T_PHOENIX[0] + 1.0))
    spread = smooth(ramp(t, 13.4, 14.2))
    cy = 0.55 - 0.27 * k + 0.012 * np.sin(2 * np.pi * t + 1.0)
    return k, spread, cy, 0.35 + 0.65 * k


# ---------- camera: keyframes (time, zoom, focus X, focus Y) ----------
def _mage_focus(e):
    X, Y, _ = proj(MAGE[e, 0], 0.5, MAGE[e, 1])
    return float(X), float(Y)


CAM_KEYS = [(0.0, 1.18, 0.0, 0.62), (2.6, 1.0, 0.0, 0.60)]
for _e, _s in enumerate([3.0, 5.0, 7.0, 9.0]):  # push in on each cast
    _fx, _fy = _mage_focus(_e)
    CAM_KEYS += [(_s + 0.1, 1.0, _fx, _fy), (_s + 0.8, 1.14, _fx, _fy),
                 (_s + 1.7, 1.14, _fx, _fy), (_s + 2.0, 1.0, _fx, _fy)]
CAM_KEYS += [(11.0, 1.0, 0.0, 0.50), (12.4, 1.12, 0.0, 0.35),
             (13.0, 1.12, 0.0, 0.35), (13.3, 1.0, 0.0, 0.35),
             (14.0, 1.0, 0.0, 0.33), (18.5, 1.12, 0.0, 0.33),
             (20.0, 1.18, 0.0, 0.62)]                # back to frame 0


def camera(t):
    ks = CAM_KEYS
    i = max(j for j in range(len(ks)) if ks[j][0] <= t)
    k0, k1 = ks[i], ks[min(i + 1, len(ks) - 1)]
    u = smooth(ramp(t, k0[0], k1[0])) if k1[0] > k0[0] else 0.0
    z, fx, fy = (a + (b - a) * u for a, b in zip(k0[1:], k1[1:]))
    hit = t - 13.3                                  # phoenix impact
    shake = 0.012 * np.exp(-hit / 0.4) if hit > 0 else 0.0
    shake += 0.003 * smooth(ramp(t, 12.0, 13.0)) * (t < 13.3)
    pk = smooth(ramp(t, 13.0, 14.0)) * (1 - ease(ramp(t, *T_FADE)))
    return dict(zoom=z, focus=(fx, fy), shake=shake,
                roll=0.015 * np.sin(0.5 * t) * pk)


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    cast = [ramp(t, s, s + 2.0) for s in T_CAST]   # 0..1 per mage
    ku = smooth(ramp(t, *T_UNITE))
    pk, spread, ph_y, ph_s = phoenix_state(t)
    burst = t - 13.3

    # ================= picture layer =================
    under = SKY.copy()
    # swirling clouds: a vortex above the field, faster near climax
    vx, vy = PX, (PY - 0.16) * ASPECT
    r = np.hypot(vx, vy)
    vort = (0.6 * ku + 1.2 * pk) * fade
    swirl = 0.05 * t + vort / (r + 0.35) * 0.4
    ang = np.arctan2(vy, vx) / (2 * np.pi) + swirl
    cl = CLOUD[(r * 90).astype(int) % 256,
               (ang * 256).astype(int) % 256]
    cl = np.clip((cl - 0.45) / 0.4, 0, 1) * (PY < HORIZON)
    under += cl[..., None] * np.array([0.10, 0.05, 0.16])
    # far ridge of rocks on the horizon
    ridge = HORIZON - 0.01 - 0.06 * RIDGE[0, ((PX + 1) * 70).astype(int)
                                          % 256] ** 2
    under[(PY > ridge) & (PY < HORIZON)] = (0.015, 0.008, 0.02)
    # element tints in the sky and on the ground
    for e in range(4):
        k = np.sin(np.pi * np.clip(cast[e] * 1.4, 0, 1)) * 0.6 \
            + 0.15 * (cast[e] >= 1) * (1 - ku)
        if k > 0:
            mx, my, _ = proj(MAGE[e, 0], 0, MAGE[e, 1])
            dd = np.hypot(PX - mx, (PY - my) * ASPECT * 0.6)
            under += (k * 0.35 * np.exp(-dd / 0.25) * fade)[..., None] \
                * ELEM[e]
            sky = (PY < HORIZON)[..., None]
            under += (k * 0.05 * fade) * ELEM[e] * sky
    # pillar of light and phoenix glow
    cx0, cy0, _ = proj(0, 0, ZC)
    pil = smooth(ramp(t, 12.0, 13.0)) \
        * (1 - smooth(ramp(t, 13.5, 15.0)))
    if pil > 0:
        top = cy0 - (cy0 + 0.05) * pil
        band = np.exp(-(PX - cx0) ** 2 / 0.004) \
            * (PY < cy0) * (PY > top)
        under += (band * 0.8 * pil * fade)[..., None] * WHITE
    if pk > 0:
        dd = np.hypot(PX, (PY - ph_y) * ASPECT)
        under += (0.35 * pk * np.exp(-dd / 0.35) * fade)[..., None] \
            * FIRE[1]
    flash = np.exp(-((t - 13.3) / 0.15) ** 2)
    under += 0.25 * flash * fade
    # fog: low, drifting, pushed away by the seal ring
    fogk = MIST[((PY * 3) * 256).astype(int) % 256,
                ((PX * 0.4 + 0.012 * t) * 256).astype(int) % 256]
    below = np.clip((PY - HORIZON) / 0.08, 0, 1)
    seal = ramp(t, *T_SEAL)
    clear = np.hypot(PX - cx0, (PY - cy0) * ASPECT * 2.2)
    push = 1 - 0.6 * np.exp(-((clear - 1.4 * seal) / 0.2) ** 2) \
        * (0 < seal < 1)
    under += (below * fogk * 0.28 * push)[..., None] * FOG

    # ================= mages (silhouettes) =================
    rims = []
    for e in range(4):
        mx, mz = MAGE[e]
        X0, Y0, s = proj(mx, 0, mz)
        a = smooth(ramp(t, T_MAGES[0] + 0.3 * e, T_MAGES[0] + 1.4
                        + 0.3 * e)) * fade

        def body(XX, YY):
            dxw = (XX - X0) * mz
            dyw = (Y0 - YY) / YU * mz
            # robe flares at the hem, narrows to the shoulders
            half = np.interp(dyw, [0, 0.30, 0.52, 0.60],
                             [0.15, 0.10, 0.12, 0.06])
            robe = (dyw >= 0) & (dyw <= 0.60) & (np.abs(dxw) < half)
            hood = (dxw / 0.075) ** 2 + ((dyw - 0.66) / 0.09) ** 2 < 1
            tip = (dyw > 0.66) & (dyw < 0.80) \
                & (np.abs(dxw + 0.03 * (dyw - 0.66) / 0.14)
                   < 0.075 * (0.80 - dyw) / 0.14)
            return robe | hood | tip

        m = body(PX, PY)
        under[m] = under[m] * (1 - a) + ROBE * a
        gm = body(g.X, g.Y)
        edge = gm & ~(np.roll(gm, 1, 1) & np.roll(gm, -1, 1)
                      & np.roll(gm, 1, 0) & np.roll(gm, -1, 0))
        act = np.sin(np.pi * np.clip(cast[e], 0, 1)) if cast[e] < 1 \
            else 0.0
        rims.append((edge, a * (0.35 + 0.9 * act) + 0.3 * ku * a, e))
        # the staff: rests, then rises and circles while casting
        side = 1 if mx < 0 else -1          # held on the inner side
        if 0 < cast[e] < 1:
            w = 2 * np.pi * 1.2 * (t - T_CAST[e])
            tipx = side * 0.18 + 0.08 * np.cos(w)
            tiph = 0.98 + 0.08 * np.sin(w)
        else:
            tipx, tiph = side * 0.2, 0.82
        sx = np.linspace(side * 0.13, tipx, 14)
        sh = np.linspace(0.36, tiph, 14)
        SX, SY, _ = proj(mx + sx, sh, mz)
        draw_line(g, SX, SY, np.array([0.35, 0.25, 0.30]), 0.6 * a)
        TX, TY, _ = proj(mx + tipx, tiph, mz)
        glow = a * (0.5 + 1.2 * act + 0.6 * ku)
        rr, cc = g.to_cell([TX], [TY])
        g.put_cells(rr, cc, CIDX["*"], (ELEM[e] * 1.5 * glow)[None])
        dd = np.hypot(PX - TX, (PY - TY) * ASPECT)
        under += (0.25 * glow * np.exp(-dd / 0.03))[..., None] * ELEM[e]

    # ================= grid: hook, circles, spells =================
    # falling spark and the seal ring
    if t < T_SPARK[1]:
        k = ease(ramp(t, *T_SPARK))
        sy = 0.02 + (cy0 - 0.02) * k
        ys = sy - np.linspace(0, 0.16, 18)
        for off in (-0.008, 0, 0.008):
            rr, cc = g.to_cell(np.full(18, cx0 + off), ys)
            g.put_cells(rr, cc, CIDX["|"], GOLD[None]
                        * np.linspace(1.8, 0.2, 18)[:, None])
        dd = np.hypot(PX - cx0, (PY - sy) * ASPECT)
        under += (0.6 * np.exp(-dd / 0.04))[..., None] * GOLD
    if 0 < seal < 1:
        for rf in (1.0, 0.93, 0.86):
            x, z = ring_pts(0, ZC, 1.4 * seal * rf, 0, 2 * np.pi, 200)
            X, Y, _ = proj(x, 0, z)
            draw_line(g, X, Y, GOLD * 1.4, 1.2 * (1 - seal) * rf)
        # sparks thrown from the impact
        a = SP_A[0][:80]
        rad = 1.6 * seal * (0.5 + 0.5 * SP_PH[0][:80])
        X, Y, _ = proj(rad * np.cos(a), 0.4 * seal * (1 - seal)
                       * 4 * SP_PH[1][:80], ZC + rad * np.sin(a))
        rr, cc = g.to_cell(X, Y)
        g.put_cells(rr, cc, CIDX["*"], GOLD[None] * 1.5 * (1 - seal))
    faint = smooth(ramp(t, 0.8, 1.4)) * (1 - ku) * 0.3
    if faint > 0:
        x, z = ring_pts(0, ZC, GREAT_R, 0, 2 * np.pi, 140)
        X, Y, _ = proj(x, 0, z)
        draw_line(g, X, Y, GOLD, faint * fade)

    n_runes = 0
    for e in range(4):
        c = cast[e]
        if c <= 0:
            continue
        mx, mz = MAGE[e]
        spin = 0.3 * (t - T_CAST[e]) * (1 + 2 * ku)
        lum = (0.9 + 0.3 * np.sin(6 * t + e)) * fade
        # outer and inner ring traced by the staff light
        pr = smooth(np.clip(c / 0.4, 0, 1))
        for rf in (1.0, 0.78):
            x, z = ring_pts(mx, mz, CIRCLE_R * rf, spin,
                            spin + 2 * np.pi * pr, 90)
            X, Y, _ = proj(x, 0, z)
            draw_line(g, X, Y, ELEM[e] * 1.2, lum)
            if pr < 1:
                rr, cc = g.to_cell(X[-1:], Y[-1:])
                g.put_cells(rr, cc, CIDX["@"], (WHITE * 1.6)[None])
        ps = smooth(np.clip((c - 0.3) / 0.3, 0, 1))
        for x, z in sigil(e, mx, mz, CIRCLE_R * 0.7, ps):
            xr = mx + (x - mx) * np.cos(spin) - (z - mz) * np.sin(spin)
            zr = mz + (x - mx) * np.sin(spin) + (z - mz) * np.cos(spin)
            X, Y, _ = proj(xr, 0, zr)
            draw_line(g, X, Y, ELEM[e] * 1.1, lum)
        nr = int(18 * np.clip((c - 0.4) / 0.3, 0, 1))
        n_runes += nr
        if nr:
            a = spin + np.arange(nr) / 18 * 2 * np.pi
            X, Y, s = proj(mx + CIRCLE_R * 0.89 * np.cos(a), 0,
                           mz + CIRCLE_R * 0.89 * np.sin(a))
            rr, cc = g.to_cell(X, Y)
            ch = np.array([CIDX[RUNES[(i + e * 5) % 18]]
                           for i in range(nr)])
            g.put_cells(rr, cc, ch, (GOLD * 1.3 * lum)[None])
        # the spell rising from the circle
        sp = np.clip((c - 0.5) / 0.2, 0, 1) * (1 - 0.55 * (c >= 1)) \
            * (1 - smooth(ramp(t, 12.0, 13.0))) * fade
        if sp > 0:
            spell(g, e, mx, mz, t, sp)

    # ================= unite: beams and the great circle ==========
    if ku > 0:
        for e in range(4):
            s = np.linspace(0, 1, 60)
            mx, mz = MAGE[e]
            X, Y, _ = proj(mx * (1 - s), 0, mz + (ZC - mz) * s)
            pulse = 0.4 + 0.8 * (np.sin(30 * s - 18 * t) > 0.6)
            draw_line(g, X[s <= ku * 1.3], Y[s <= ku * 1.3],
                      ELEM[e] * 1.3, (pulse * fade)[s <= ku * 1.3])
        pg = smooth(ramp(t, 11.3, 12.5))
        spin = 0.6 * (t - 11.0) + 2.0 * pk
        for rf in (1.0, 0.86):
            x, z = ring_pts(0, ZC, GREAT_R * rf, spin,
                            spin + 2 * np.pi * pg, 160)
            X, Y, _ = proj(x, 0, z)
            draw_line(g, X, Y, GOLD * 1.3, fade)
        hx = smooth(ramp(t, 11.8, 12.5))
        for k in range(6):                   # hexagram
            a0 = spin + k * np.pi / 3
            a1 = a0 + 2 * np.pi / 3
            s = np.linspace(0, hx, 40)
            x = GREAT_R * 0.86 * ((1 - s) * np.cos(a0) + s * np.cos(a1))
            z = ZC + GREAT_R * 0.86 * ((1 - s) * np.sin(a0)
                                       + s * np.sin(a1))
            X, Y, _ = proj(x, 0, z)
            draw_line(g, X, Y, GOLD * 1.2, fade)
    # pillar letters
    if pil > 0:
        top = cy0 - (cy0 + 0.05) * pil
        ys = np.arange(cy0, max(top, 0), -0.012)
        for off in (-0.012, 0, 0.012):
            rr, cc = g.to_cell(np.full(len(ys), cx0 + off), ys)
            g.put_cells(rr, cc, CIDX["|"],
                        (WHITE * 1.6 * pil * fade)[None])

    # rims of the mages go on top (lit by their own element)
    for edge, k, e in rims:
        if k > 0:
            g.put(edge, CIDX["#"], ELEM[e] * k)

    # ================= phoenix (its own 3D splat) ==================
    n_lit = 0
    if pk > 0:
        P, C, L, CH = phoenix_points(t, spread)
        keep = np.ones(len(P), bool)
        if fade < 1:                       # dissolve into embers
            keep = (np.arange(len(P)) * 0.618 % 1) < fade
        n_lit = splat(g, P[keep], C[keep] * fade, np.clip(L[keep], 0,
                                                          1),
                      CH[keep], cy=ph_y, scale=ph_s)
        # embers from the wings, drifting up
        age = t - EM_T
        al = (age > 0) & (age < 1.6)
        if al.any():
            wx, wy = wing_point(EM_U[al], EM_S[al], EM_T[al], 1.0)
            ex = wx * ph_s + EM_V[al, 0] * age[al]
            ey = ph_y + (wy * ph_s * YU) - 0.08 * age[al] \
                + EM_V[al, 1] * age[al] * 0.3
            el = (1 - age[al] / 1.6) * 1.3
            rr, cc = g.to_cell(ex, ey)
            g.put_cells(rr, cc, np.where(np.arange(al.sum()) % 3,
                                         CIDX["."], CIDX["*"]),
                        FIRE[1][None] * 1.3 * el[:, None])
    if 0 < burst < 1.6:                    # shockwave + ember burst
        rad = burst * 1.6
        ring = np.abs(np.hypot(g.X - cx0, (g.Y - ph_y) * ASPECT)
                      - rad) < 0.03
        g.put(ring, np.where((g.c + g.r) % 2, CIDX["o"], CIDX["."])
              [ring], (FIRE[0] * 1.3) * (1 - burst / 1.6) * fade)
        bx = cx0 + np.cos(BU_A) * BU_S * rad
        by = ph_y + (np.sin(BU_A) * BU_S * rad + 0.25 * burst ** 2) \
            / ASPECT
        rr, cc = g.to_cell(bx, by)
        g.put_cells(rr, cc, CIDX["'"],
                    FIRE[1][None] * (1.4 * (1 - burst / 1.6) * fade))

    n_lit = int((g.col.max(-1) > 0.05).sum())
    elements = sum(c >= 0.6 for c in cast)
    mana = 17.5 * sum(min(c, 1) for c in cast) + 30 * ku
    return {"under": np.clip(under, 0, 1), "camera": camera(t),
            "hud": [HANDLE,
                    f"runes {n_runes:2d}   elements {elements}   "
                    f"mana {mana:3.0f}%",
                    f"letters {n_lit:,}"]}


def spell(g, e, mx, mz, t, k):
    """one element's magic rising above its circle."""
    ph = SP_PH[e]
    if e == 0:            # fire whirl
        h = (ph + 1.2 * t) % 1.0 * 1.9
        r = 0.30 * (1 - h / 2.2)
        a = SP_A[e] + 5 * t + 3 * h
        col = np.where((h < 0.4)[:, None], FIRE[0],
                       np.where((h < 0.9)[:, None], FIRE[1], FIRE[2]))
        ch = np.where(ph > 0.6, CIDX["^"], np.where(ph > 0.3, CIDX["*"],
                                                     CIDX["'"]))
        lum = (1.3 - 0.45 * h) * k
    elif e == 1:          # water spiral column
        h = (ph + 0.8 * t) % 1.0 * 2.0
        r = 0.22 + 0.05 * np.sin(6 * h)
        a = SP_A[e] * 0 + ph * 12 + 3 * t
        col = np.where((ph > 0.5)[:, None], WATER[0], WATER[1])
        ch = np.where(ph > 0.66, CIDX["~"],
                      np.where(ph > 0.33, CIDX["o"], CIDX["."]))
        lum = 1.1 * k * np.ones_like(h)
    elif e == 2:          # wind tornado
        h = (ph + 0.9 * t) % 1.0 * 1.9
        r = 0.10 + 0.28 * h
        a = SP_A[e] + 6 * t - 2 * h
        col = np.where((ph > 0.5)[:, None], WIND[0], WIND[1])
        ch = np.where(np.sin(a) > 0, CIDX[")"], CIDX["("])
        ch = np.where(ph > 0.9, CIDX["*"], ch)
        lum = (1.2 - 0.35 * h) * k
    else:                 # earth crystals bursting up
        rise = np.clip((t - T_CAST[3] - 1.0 - CR_T) / 0.35, 0, 1)
        for i in range(12):
            if rise[i] <= 0:
                continue
            hh = CR_H[i] * np.clip(pop(rise[i]), 0, 1.2) * (k / 0.45
                                                             if k < 0.45
                                                             else 1)
            hs = np.linspace(0, hh, 12)
            X, Y, _ = proj(mx + CR_R[i] * np.cos(CR_A[i]) + 0 * hs, hs,
                           mz + CR_R[i] * np.sin(CR_A[i]))
            ch = np.where(hs > hh * 0.8, CIDX["A"], CIDX["#"])
            rr, cc = g.to_cell(X, Y)
            g.put_cells(rr, cc, ch, (EARTH[0] * 1.3 * k)[None])
        h = (ph + 0.6 * t) % 1.0 * 0.8           # floating debris
        r = 0.1 + 0.25 * ph
        a = SP_A[e] + 1.5 * t
        col = np.broadcast_to(EARTH[1] * 1.6, (len(h), 3))
        ch = np.full(len(h), CIDX["."])
        lum = (0.9 - 0.5 * h) * k
    X, Y, _ = proj(mx + r * np.cos(a), h, mz + r * np.sin(a))
    rr, cc = g.to_cell(X, Y)
    g.put_cells(rr, cc, ch, np.asarray(col) * 1.3 * lum[:, None])
