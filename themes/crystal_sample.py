"""crystal_sample: 3 s test of lights, glints and floor reflection."""
import numpy as np
from engine import (CIDX, Snow, light, rot_x, rot_y, splat,
                    splat_reflection)

TITLE = "Crystal (render test)"
HANDLE = "@justmade.lab"
DURATION = 3.0
GLOW = 1.1
SCENES = [("spin", 0.0, 1.5), ("glints", 1.5, 3.0)]
POSTER_T = 2.2
SPIN = 0.9            # rad / s
TILT = 0.25
FLOOR = 0.42          # floor height in model units (y down)
rng = np.random.default_rng(5)

# ---------- geometry: hexagonal bipyramid ----------
TOP = np.array([0.0, -0.50, 0.0])
BOT = np.array([0.0, 0.34, 0.0])
RING = [np.array([0.30 * np.cos(a), -0.08, 0.30 * np.sin(a)])
        for a in np.linspace(0, 2 * np.pi, 6, endpoint=False)]


def faces():
    """sample points on every face; normal = face normal."""
    P, N = [], []
    for i in range(6):
        a, b = RING[i], RING[(i + 1) % 6]
        for tip in (TOP, BOT):
            n = np.cross(a - tip, b - tip)
            c = (a + b + tip) / 3
            n = n if n @ c > 0 else -n
            uv = rng.random((1400, 2))
            uv = np.where(uv.sum(1, keepdims=True) > 1, 1 - uv, uv)
            pts = tip + uv[:, :1] * (a - tip) + uv[:, 1:] * (b - tip)
            P.append(pts)
            N.append(np.tile(n / np.linalg.norm(n), (len(pts), 1)))
    return np.concatenate(P), np.concatenate(N)


GEM_P, GEM_N = faces()
GEM_SEED = rng.random(len(GEM_P))
ICE = np.array([0.75, 0.88, 1.0])
snow = Snow(rng, n=120)


def view(P, t):
    return rot_x(rot_y(P, SPIN * t), TILT)


def draw(g, t):
    snow.draw(g, t * 0.3, 0.3)
    bob = 0.02 * np.sin(t * 2.0)
    P = view(GEM_P, t) + np.array([0, bob, 0])
    N = view(GEM_N, t)
    lum, glint = light(N, t, seed=GEM_SEED, glint_rate=4.0)
    rgb = np.where(glint[:, None], 1.6, 1.0) * ICE
    rgb = np.broadcast_to(rgb, P.shape)
    chars = np.where(glint, CIDX["*"], -1)

    kw = dict(cy=0.45, scale=1.3)
    splat_reflection(g, P, rgb, lum, FLOOR, **kw)
    n_lit = splat(g, P, rgb, np.clip(lum, 0, 1), chars, **kw)

    deg = np.degrees(SPIN * t) % 360
    return [HANDLE,
            f"rotation {deg:6.2f}°   glints {int(glint.sum())}",
            f"letters {n_lit:,}"]
