"""lake_sample: 3 s test of picture layer, perspective, sprites."""
import numpy as np
from engine import (RAMP, ground, noise2d, pic_coords, ramp, sample,
                    smooth, vgradient)

TITLE = "Night Lake (render test)"
HANDLE = "@justmade.lab"
DURATION = 3.0
GLOW = 1.0
SCENES = [("clouds part", 0.0, 1.5), ("lanterns", 1.5, 3.0)]
POSTER_T = 2.4

T_MOON = (0.2, 1.4)       # moon comes out from behind the clouds
T_LANTERN = (1.2, 2.6)    # lanterns light up one by one
HORIZON = 0.56            # screen Y of the horizon
CAM = 0.22                # camera height above the water
MOON = (0.42, 0.17, 0.055)  # screen x, y, radius
rng = np.random.default_rng(4)

# ---------- fixed fields ----------
CLOUD = noise2d(256, beta=2.3, seed=1)
RIPPLE = noise2d(128, beta=1.2, seed=2)
HILL = noise2d(256, beta=3.2, seed=3)   # read along one row = ridge
PX, PY = pic_coords()
SKY = vgradient([(0.0, (0.01, 0.02, 0.08)),
                 (0.45, (0.06, 0.10, 0.34)),
                 (HORIZON, (0.12, 0.18, 0.48)),     # sky at horizon
                 (HORIZON, (0.02, 0.05, 0.13)),     # water at horizon
                 (1.0, (0.01, 0.02, 0.06))])

N_WAVE = 700
W_X = rng.uniform(-3.5, 3.5, N_WAVE)
W_Z = rng.uniform(0.3, 9.0, N_WAVE)
N_LAMP = 26
L_X = rng.uniform(-1.6, 1.6, N_LAMP)
L_Z = rng.uniform(0.5, 5.0, N_LAMP)
L_T = np.sort(rng.uniform(*T_LANTERN, N_LAMP))
L_PH = rng.uniform(0, 2 * np.pi, N_LAMP)


def sky(t):
    """sky gradient, drifting clouds, moon glow, hills and water."""
    img = SKY.copy()
    up = PY < HORIZON
    c = sample(CLOUD, PX * 0.45 + 0.025 * t, PY * 0.9)
    cloud = np.clip((c - 0.55) / 0.3, 0, 1) * up
    # moon: hidden at first, clouds slide off it
    mx, my, mr = MOON
    d = np.hypot((PX - mx) * 1.0, (PY - my) * 2.03)
    out = smooth(ramp(t, *T_MOON))
    disc = np.clip((mr - d) / 0.01, 0, 1)
    glow = np.exp(-d / 0.09) * 0.45
    veil = 1 - cloud * (1 - 0.8 * out)
    moon = (disc * 0.95 + glow) * (0.25 + 0.75 * out) * veil
    img += moon[..., None] * np.array([0.95, 0.95, 0.85])
    tint = np.array([0.10, 0.13, 0.30]) * (0.6 + 0.6 * glow[..., None])
    img += cloud[..., None] * tint
    # far hills: a dark ridge sitting on the horizon
    ridge = HORIZON - 0.012 - 0.05 * sample(HILL, PX * 0.4, 0)
    hill = (PY > ridge) & up
    img[hill] = np.array([0.015, 0.02, 0.05])
    # water: moon path shimmering toward us
    down = PY >= HORIZON
    path = np.exp(-((PX - mx) / (0.04 + 0.5 * (PY - HORIZON))) ** 2)
    rip = sample(RIPPLE, PX * 2.0, PY * 6.0 - 0.15 * t)
    shine = path * np.clip(rip * 1.6 - 0.6, 0, 1) * out * down
    img += shine[..., None] * np.array([0.55, 0.6, 0.7])
    return img, cloud, out


def draw(g, t):
    under, cloud, moon_out = sky(t)

    # letters inside the brightest clouds (grid layer over the picture)
    h, w = cloud.shape
    cl = cloud[(g.Y * h).astype(int).clip(0, h - 1),
               ((g.X + 1) / 2 * w).astype(int).clip(0, w - 1)]
    m = cl > 0.6
    k = ((cl[m] - 0.6) / 0.4 * (len(RAMP) - 1)).astype(int)
    g.put(m, RAMP[k], (0.45, 0.55, 0.95), 0.4)

    # waves: '~' on the water, bigger when closer, drifting toward us
    z = 0.3 + (W_Z - 0.9 * t - 0.3) % 8.7
    X, Y, s = ground(W_X, z, HORIZON, CAM)
    lit = np.exp(-((X - MOON[0]) / (0.06 + 0.4 * s)) ** 2) * moon_out
    near = 0.35 + 0.65 * np.clip(s, 0, 1)
    rgb = np.array([0.25, 0.4, 0.8]) * near[:, None]
    rgb = rgb + lit[:, None] * np.array([0.6, 0.6, 0.5])
    size = np.clip(10 + 26 * s, 8, 44)
    sprites = dict(x=list(X), y=list(Y), ch=["~"] * N_WAVE,
                   size=list(size), rgb=list(rgb))

    # lanterns: warm '@' that light up one by one and bob
    on = smooth(np.clip((t - L_T) / 0.35, 0, 1))
    LX, LY, ls = ground(L_X, L_Z, HORIZON, CAM)
    LY = LY - 0.012 * ls - 0.004 * np.sin(t * 3 + L_PH)
    warm = np.array([1.0, 0.62, 0.25]) * (0.4 + 1.1 * on)[:, None]
    for i in np.nonzero(on > 0)[0]:
        sprites["x"].append(LX[i])
        sprites["y"].append(LY[i])
        sprites["ch"].append("@")
        sprites["size"].append(np.clip(14 + 40 * ls[i], 12, 64))
        sprites["rgb"].append(warm[i])

    n_lamp = int((on > 0).sum())
    return {"under": under, "sprites": sprites,
            "hud": [HANDLE,
                    f"moon {moon_out * 100:3.0f}%   lanterns {n_lamp}",
                    f"waves {N_WAVE}   letters {int(m.sum()):,}"]}
