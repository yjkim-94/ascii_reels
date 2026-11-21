"""jellyfish_sample: 3 s render test (point cloud, pulse, colour wave)."""
import numpy as np
from engine import (Snow, dir_chars, ramp, rot_x, rot_y,
                    smooth, splat)

HANDLE = "@ascii.reels"
DURATION = 3.0
GLOW = 1.0
rng = np.random.default_rng(3)

PERIOD = 1.5          # one swim beat (s)
RIM_LAG = 0.25        # squeeze reaches the rim this much later
SPIN = 0.45           # rad / s around the vertical axis
TILT = 0.32           # lean toward camera so we see the dome
T_LIGHT = 0.6         # colour wave starts
WAVE_SPEED = 0.9      # body lengths / s
N_TENT = 14

PALETTES = [  # (stripe, between stripes, arms)
    ((0.20, 0.32, 1.00), (0.55, 0.72, 1.00), (0.55, 0.45, 1.0)),
    ((1.00, 0.35, 0.75), (0.35, 0.95, 1.00), (1.00, 0.45, 0.6)),
]
WHITE = np.array([1.0, 1.0, 1.0])


def squeeze(t):
    """0 relaxed .. 1 fully contracted; quick pull, slow release."""
    ph = (t / PERIOD) % 1.0
    return np.where(ph < 0.3, smooth(ph / 0.3),
                    1 - smooth(np.clip((ph - 0.3) / 0.7, 0, 1)))


# ---------- bell: u 0 crown .. 1 rim, th around ----------
U, TH = np.meshgrid(np.linspace(0, 1, 70),
                    np.linspace(0, 2 * np.pi, 220, endpoint=False))
U, TH = U.ravel(), TH.ravel()


def bell(t, u=U, th=TH):
    c = squeeze(t - RIM_LAG * u)
    r = 0.50 * np.sin(u * np.pi * 0.52) ** 0.75 * (1 - 0.2 * c * u)
    r = r * (1 + 0.06 * u ** 6)                 # flared rim
    y = -0.42 * np.cos(u * np.pi * 0.5) * (1 + 0.14 * c)
    P = np.stack([r * np.cos(th), y, r * np.sin(th)], -1)
    # normal of a dome ~ direction from a point below the crown
    n = P - np.array([0, 0.25, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return P, n, c


# ---------- tentacles hang from the rim and trail the beat ----------
S = np.linspace(0, 1, 110)
T_ANG = np.linspace(0, 2 * np.pi, N_TENT, endpoint=False) + 0.2
T_LEN = rng.uniform(0.55, 0.85, N_TENT)


def tentacles(t):
    pts = []
    for k in range(N_TENT):
        Pr, _, _ = bell(t, np.array([1.0]), np.array([T_ANG[k]]))
        x0, y0, z0 = Pr[0]
        lag = 2 * np.pi * (t / PERIOD - S * 1.3) + k
        sw = 0.07 * S * np.sin(lag)
        x = x0 * (1 - 0.35 * S) + sw * np.cos(T_ANG[k] + 1.5)
        z = z0 * (1 - 0.35 * S) + sw * np.sin(T_ANG[k] + 1.5)
        y = y0 + S * T_LEN[k]
        pts.append(np.stack([x, y, z], -1))
    return np.concatenate(pts)


# ---------- oral arms: four ruffled ribbons under the bell ----------
SA = np.linspace(0, 1, 90)
RUF = np.linspace(0, 2 * np.pi, 10, endpoint=False)


def arms(t):
    pts = []
    for k in range(4):
        a = k * np.pi / 2 + 0.4
        sway = 0.05 * np.sin(2 * np.pi * (t / PERIOD - SA) + k)
        cx = 0.07 * np.cos(a) * (1 + SA) + sway
        cz = 0.07 * np.sin(a) * (1 + SA)
        cy = -0.02 + SA * 0.62
        rad = 0.035 * (1 + 0.8 * np.sin(SA * 22 + k)) * (1 - 0.5 * SA)
        for q in RUF:
            pts.append(np.stack([cx + rad * np.cos(q), cy,
                                 cz + rad * np.sin(q)], -1))
    return np.concatenate(pts)


def colour_wave(t, way, inks):
    """palette 0 -> 1 as a white-hot front runs down the body."""
    wave = (t - T_LIGHT) * WAVE_SPEED
    on = smooth(np.clip((wave - way) / 0.15, 0, 1))[:, None]
    band = np.exp(-((wave - way) / 0.07) ** 2)[:, None]
    rgb = inks(0) + (inks(1) - inks(0)) * on
    return rgb + (WHITE - rgb) * band * 0.85, band[:, 0]


def view(P, t):
    return rot_x(rot_y(P, SPIN * t), TILT)


snow = Snow(rng, n=160)


def draw(g, t):
    snow.draw(g, t * 0.4, 0.35)

    # a far, dim copy reuses the same model (drawn first = behind)
    Pf = view(bell(t + 0.7)[0], t + 2.0) * 0.22
    Pf[:, 0] -= 0.78
    splat(g, Pf, np.broadcast_to(PALETTES[0][0], Pf.shape) * 0.3,
          np.full(len(Pf), 0.35), cy=0.12, scale=1.0, f=50)
    L = np.array([0.3, -0.8, 0.5])
    L = L / np.linalg.norm(L)

    # bell: radial stripes, lambert + translucent rim light
    P, n, c = bell(t)
    stripe = (np.cos(8 * TH) > 0.35)[:, None]
    inks = lambda i: np.where(stripe, PALETTES[i][0], PALETTES[i][1])
    rgb, band = colour_wave(t, U * 0.35, inks)
    Pv, nv = view(P, t), view(n, t)
    lam = np.clip(nv @ L, 0, 1)
    rim = (1 - np.abs(nv[:, 2])) ** 2
    grain = 0.12 * np.sin(TH * 23 + U * 41) * np.sin(U * 17 - t)
    lum = 0.25 + 0.55 * lam + 0.35 * rim + 0.5 * band + grain

    # oral arms
    A = arms(t)
    wa = 0.35 + 0.3 * (A[:, 1] / 0.62)
    ainks = lambda i: np.broadcast_to(PALETTES[i][2], A.shape)
    argb, aband = colour_wave(t, wa, ainks)
    alum = 0.45 + 0.25 * np.sin(A[:, 1] * 30) + 0.5 * aband

    # tentacles: thin lines drawn with direction glyphs
    T = tentacles(t)
    Tv = view(T, t)
    d = np.gradient(Tv[:, :2], axis=0)
    tch = dir_chars(d[:, 0], d[:, 1])
    tch[::len(S)] = -1                          # roots use the ramp
    way = 0.35 + 0.65 * np.tile(S, N_TENT)
    tinks = lambda i: np.broadcast_to(PALETTES[i][1], T.shape)
    trgb, tband = colour_wave(t, way, tinks)
    tlum = 0.5 - 0.25 * np.tile(S, N_TENT) + 0.5 * tband

    # one z-buffer for the whole animal
    allP = np.concatenate([Pv, view(A, t), Tv])
    allC = np.concatenate([rgb, argb, trgb])
    allL = np.concatenate([lum, alum, tlum])
    chars = np.concatenate([np.full(len(Pv) + len(A), -1), tch])
    n_lit = splat(g, allP, allC, allL, chars, cy=0.36, scale=1.25)


    beats = int(t // PERIOD) + 1
    colours = int(t > T_LIGHT + 1.0 / WAVE_SPEED)
    return [HANDLE,
            f"beats {beats}   tentacles {N_TENT}   colours {colours}",
            f"letters {n_lit:,}   squeeze {float(c.mean()):.2f}"]
