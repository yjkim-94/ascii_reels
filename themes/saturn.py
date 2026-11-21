"""saturn: dust gathers into a planet, then the rings spread out."""
import numpy as np
from engine import (CIDX, dir_chars, ease, light, ramp, rot_x,
                    rot_y, smooth, splat)

TITLE = "Saturn"
HANDLE = "@justmade.lab"
DURATION = 15.0
GLOW = 1.05
rng = np.random.default_rng(11)

# ---------- timeline (seconds) ----------
T_DUST_IN = (0.0, 0.6)    # dust fades in (loop seam)
T_GATHER = (0.0, 4.5)     # dust spirals in and becomes a sphere
T_FLASH = (4.2, 4.9)      # surface flashes when the last dust lands
T_BANDS = (4.5, 6.0)      # cloud bands appear
T_RING = (6.0, 9.5)       # particles spread out from the equator
T_SUN = (9.5, 12.0)       # sun rises behind: back-lit climax
T_FADE = (13.5, 15.0)     # fade to stars, then loop
SCENES = [("dust swirl", 0.0, 1.0), ("gather", 1.0, 4.5),
          ("bands", *T_BANDS), ("rings", *T_RING),
          ("back light", *T_SUN), ("hold", 12.0, 13.5),
          ("fade", *T_FADE)]
POSTER_T = 12.6

# ---------- shape (model units, y down, z toward us) ----------
R = 0.28                  # planet radius
FLAT = 0.90               # poles squashed by 10 %
TILT = 26.73              # ring tilt, degrees
ROLL = -0.22              # tip the whole system sideways (rad)
SPIN = 0.35               # planet rotation, rad / s
N_DUST = 4812
N_RING = 12000
CY, SCALE = 0.42, 1.15

AMBER = np.array([0.95, 0.62, 0.28])
CREAM = np.array([1.00, 0.88, 0.65])
DEEP = np.array([0.70, 0.45, 0.25])
BEIGE = np.array([0.90, 0.82, 0.65])
GOLD = np.array([1.00, 0.85, 0.45])
WHITE = np.array([1.0, 1.0, 1.0])
STAR = np.array([0.60, 0.65, 0.80])


def fib_sphere(n):
    """evenly spread points on a unit sphere."""
    i = np.arange(n) + 0.5
    y = 1 - 2 * i / n
    r = np.sqrt(1 - y * y)
    a = i * np.pi * (3 - np.sqrt(5))
    return np.stack([r * np.cos(a), y, r * np.sin(a)], -1)


# planet surface = where every dust grain lands
UNIT = fib_sphere(N_DUST)
SURF = UNIT * np.array([R, R * FLAT, R])
LAT = UNIT[:, 1]                                 # -1 north .. 1 south
LON = np.arctan2(UNIT[:, 2], UNIT[:, 0])
BAND = np.sin(LAT * 19) + 0.45 * np.sin(LAT * 47 + 1.3)
SPOT = np.exp(-((LAT - 0.35) / 0.07) ** 2
              - ((LON - 1.0) / 0.25) ** 2)       # one storm oval

# dust starts on a wide, thin spiral disk
D_R = rng.uniform(0.40, 0.88, N_DUST)
D_A = rng.uniform(0, 2 * np.pi, N_DUST)
D_Y = rng.normal(0, 0.03, N_DUST)
D_L = rng.uniform(0.15, 0.5, N_DUST)       # loose dust brightness
D_DELAY = rng.uniform(0, 1.4, N_DUST)

# ring particles: C, B, Cassini gap, A
RING_R = np.concatenate([rng.uniform(0.35, 0.42, 2500),
                         rng.uniform(0.42, 0.52, 6000),
                         rng.uniform(0.54, 0.64, 3500)])
RING_A = rng.uniform(0, 2 * np.pi, N_RING)
RING_D = np.concatenate([np.full(2500, 0.55), np.full(6000, 1.0),
                         np.full(3500, 0.75)])   # optical depth
RING_D = RING_D * (0.8 + 0.2 * np.sin(RING_R * 180))
RING_W = 0.55 * (RING_R / 0.35) ** -1.5          # inner = faster

# background stars (screen space)
S_X = rng.uniform(-1, 1, 180)
S_Y = rng.uniform(0, 0.86, 180)
S_PH = rng.uniform(0, 2 * np.pi, 180)


def roll(P, a):
    c, s = np.cos(a), np.sin(a)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return np.stack([c * x - s * y, s * x + c * y, z], -1)


def view(P, tilt):
    return roll(rot_x(P, -np.radians(tilt)), ROLL)


def unit(v):
    return v / np.linalg.norm(v)


def stars(g, t, a):
    tw = 0.35 + 0.65 * np.clip(np.sin(t * 2.2 + S_PH), 0, 1) ** 3
    rr, cc = g.to_cell(S_X, S_Y)
    ch = np.where(tw > 0.8, CIDX["*"],
                  np.where(tw > 0.5, CIDX["+"], CIDX["."]))
    g.put_cells(rr, cc, ch, STAR[None] * (tw * a)[:, None])


def draw(g, t):
    fade = 1 - ease(ramp(t, *T_FADE))
    stars(g, t, 0.8)

    k_ring = smooth(ramp(t, *T_RING))
    tilt = TILT * k_ring
    k_sun = smooth(ramp(t, *T_SUN))

    # sun: from behind the planet up to the upper left
    sun = np.array([-0.10 - 0.30 * k_sun, -0.05 - 0.22 * k_sun, -1.2])
    front = unit(np.array([-0.5, -0.6, 0.65]))
    key = unit(front * (1 - k_sun) + unit(sun) * k_sun)

    # ----- dust -> planet -----
    k = np.clip((t - T_GATHER[0] - D_DELAY)
                / (T_GATHER[1] - 1.4 - T_GATHER[0]), 0, 1)
    k = smooth(k)
    swirl = D_A + 0.9 * t + (1 - k) * 3.0       # spiral inwards
    start = np.stack([D_R * np.cos(swirl), D_Y,
                      D_R * np.sin(swirl)], -1)
    start = rot_x(start, -0.95)          # face the swirl, not its edge
    surf = rot_y(SURF, SPIN * t)
    P = start * (1 - k)[:, None] + surf * k[:, None]
    n = rot_y(UNIT * np.array([1, 1 / FLAT, 1]), SPIN * t)
    Pv, nv = view(P, tilt), view(n, tilt)

    lum, _ = light(nv, t, key=key, ambient=0.1, key_w=0.75,
                   rim_w=0.35 + 0.9 * k_sun, spec_w=0.15,
                   glint_cut=9.0)
    edge = (1 - np.abs(nv[:, 2])) ** 2
    a_in = smooth(ramp(t, *T_DUST_IN))
    lum = lum * k + D_L * a_in * (1 - k)         # loose dust is dim
    lum = lum + 0.8 * k_sun * edge * k           # crescent rim
    lum = lum + 0.9 * np.exp(-((t - 4.55) / 0.18) ** 2) * k

    kb = smooth(ramp(t, *T_BANDS))
    band = np.where(BAND > 0.6, 0, np.where(BAND > -0.4, 1, 2))
    pal = np.stack([CREAM, AMBER, DEEP])[band]
    pal = pal * (1 - 0.35 * SPOT)[:, None]
    col = CREAM * (1 - kb) + pal * kb
    col = col * (1 - k_sun * 0.6) + GOLD * (k_sun * 0.6)
    col = np.broadcast_to(col, P.shape)

    # ----- rings -----
    kr = np.clip((t - T_RING[0] - (RING_R - 0.35) * 6)
                 / 1.2, 0, 1)
    kr = smooth(kr)
    on = kr > 0
    rad = R * 1.03 + (RING_R - R * 1.03) * kr
    ang = RING_A + RING_W * t
    Q = np.stack([rad * np.cos(ang), np.zeros(N_RING),
                  rad * np.sin(ang)], -1)[on]
    Qv = view(Q, tilt)
    up = view(np.array([[0.0, -1.0, 0.0]]), tilt)[0]
    face = np.abs(up @ key)
    back = np.clip(-key[2], 0, 1) * k_sun       # forward scatter
    rl = RING_D[on] * (0.25 + 0.55 * face) + 0.9 * back * RING_D[on]
    # planet shadow on the rings
    along = Qv @ key
    perp = np.linalg.norm(Qv - along[:, None] * key, axis=1)
    shadow = (along < 0) & (perp < R)
    rl = np.where(shadow, rl * 0.35, rl)
    hot = GOLD * 0.6 + WHITE * 0.4
    rc = BEIGE * (1 - k_sun) + hot * k_sun
    rc = np.broadcast_to(rc, Qv.shape)

    # ----- sun + rays, behind the planet (z-buffer hides it) -----
    sp, sc, sl, sch = [], [], [], []
    if k_sun > 0:
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            ln = 0.06 + 0.22 * k_sun * (1 + 0.5 * np.cos(a * 3))
            s = np.linspace(0.02, ln, 14)
            pts = sun + np.stack([np.cos(a) * s, np.sin(a) * s,
                                  np.zeros_like(s)], -1)
            sp.append(pts)
            sl.append(1 - s / ln * 0.8)
            sch.append(dir_chars(np.full(len(s), np.cos(a)),
                                 np.full(len(s), np.sin(a))))
        sp.append(sun[None])
        sl.append(np.array([1.0]))
        sch.append(np.array([CIDX["@"]]))
        sp = np.concatenate(sp)
        sl = np.concatenate(sl) * k_sun
        sch = np.concatenate(sch)
        sc = np.broadcast_to(GOLD * 1.6, sp.shape)
    else:
        sp = np.zeros((0, 3))
        sl = np.zeros(0)
        sch = np.zeros(0, int)
        sc = np.zeros((0, 3))

    allP = np.concatenate([Pv, Qv, sp])
    allC = np.concatenate([col, rc, sc]) * fade
    allL = np.concatenate([lum, rl, sl])
    ch = np.concatenate([np.full(len(Pv) + len(Qv), -1), sch])
    n_lit = splat(g, allP, allC, np.clip(allL, 0, 1), ch,
                  cy=CY, scale=SCALE)

    dust = int(N_DUST * k.mean())
    n_ring = int(N_RING * kr.mean())
    return [HANDLE,
            f"dust {dust:,}   ring {n_ring:,}   tilt {tilt:5.2f}°",
            f"letters {n_lit:,}"]
