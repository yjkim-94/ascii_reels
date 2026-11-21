"""footage_sample: 3 s test of live footage -> letters."""
import numpy as np
from engine import Footage, Snow, draw_footage, ramp, smooth

TITLE = "Footage (render test)"
HANDLE = "@justmade.lab"
DURATION = 3.0
GLOW = 1.2
SOURCE = "sources/test_fractal.mp4"   # ffmpeg mandelbrot test clip
SCENES = [("reveal", 0.0, 1.6), ("hold", 1.6, 3.0)]
POSTER_T = 2.4
T_REVEAL = (0.1, 1.6)     # letters open from the centre
rng = np.random.default_rng(2)

clip = Footage(SOURCE, start=0.5, length=DURATION)
snow = Snow(rng, n=120)


def draw(g, t):
    snow.draw(g, t * 0.3, 0.3)
    p = smooth(ramp(t, *T_REVEAL))
    d = np.hypot(g.X, (g.Y - 0.5) * 2)          # distance from centre
    mask = d < p * 1.5
    rim = np.abs(d - p * 1.5) < 0.05             # bright opening edge
    img = clip.at(t)
    n = draw_footage(g, img, gain=1.1, mask=mask)
    if 0 < p < 1:
        draw_footage(g, img, gain=2.2, mask=mask & rim)
    return [HANDLE,
            f"frame {int(t * 30):03d}   reveal {p * 100:5.1f}%",
            f"letters {n:,}"]
