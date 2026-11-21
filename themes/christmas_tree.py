"""christmas_tree: a tree that grows out of letters."""
import numpy as np
from engine import (CIDX, LetterRain, Snow, ease, idx,
                    pop, ramp, smooth)

HANDLE = "@ascii.reels"
WORD = "MERRYCHRISTMASJOYPEACE"
GREETING = "MERRY CHRISTMAS 2026"
DURATION = 15.0
GLOW = 0.95
rng = np.random.default_rng(7)

# ---------- timeline (seconds) ----------
T_GROUND = (0.0, 0.8)     # ground fades in
T_TRUNK = (0.4, 1.0)      # trunk rises
T_TREE = (0.9, 4.6)       # tree grows bottom -> top
T_LIGHTS = (4.5, 7.5)     # garland wraps upward
T_ORN = (4.9, 7.8)        # ornaments pop in
T_STAR = (7.6, 8.4)       # star + rays
T_GIFT = (8.0, 9.6)       # gift boxes pop in
T_TEXT = (9.4, 11.6)      # greeting types out
T_FADE = (13.2, 14.6)     # fade out, then loop
SPIN = 0.55               # rad / s

# ---------- layout (Y: 0 top .. 1 bottom) ----------
TREE_TOP, TREE_BOT = 0.11, 0.73
TRUNK_BOT, GROUND = 0.79, 0.80
TEXT_Y = 0.84

# ---------- tree geometry (h: 0 top .. 1 bottom) ----------
# 3 tiers; each skirt overlaps the next tier -> shadow band
TIER_SPANS = [(0.00, 0.40), (0.27, 0.71), (0.56, 1.00)]
TIER_R = [(0.02, 0.40), (0.16, 0.60), (0.26, 0.80)]


def tree_radius(h):
    h = np.asarray(h, float)
    out = np.zeros_like(h)
    shade = np.ones_like(h)
    for k, (a, b) in enumerate(TIER_SPANS):
        u = (h - a) / (b - a)
        m = (u >= 0) & (u <= 1)
        r0, r1 = TIER_R[k]
        r = r0 + (r1 - r0) * np.clip(u, 0, 1) ** 0.9
        out = np.where(m, np.maximum(out, r), out)
        if k > 0:  # shadow under the upper skirt
            dark = 0.25 + 0.75 * np.clip(u * 3.0, 0, 1)
            shade = np.where(m & (u < 0.34), dark, shade)
    return out, shade


def to_h(Y):
    return (Y - TREE_TOP) / (TREE_BOT - TREE_TOP)


def to_Y(h):
    return TREE_TOP + h * (TREE_BOT - TREE_TOP)


# ---------- fixed random decorations ----------
N_BULB, TURNS = 240, 6.5
ORN = dict(h=rng.uniform(0.08, 0.96, 46),
           ang=rng.uniform(0, 2 * np.pi, 46),
           kind=rng.integers(0, 4, 46))
ORN_COL = np.array([[1.0, 0.18, 0.15], [1.0, 0.78, 0.25],
                    [0.3, 0.55, 1.0], [0.95, 0.95, 1.0]])
BULB_COL = np.array([[1.0, 0.85, 0.4], [1.0, 0.35, 0.3],
                     [0.5, 0.8, 1.0], [1.0, 0.6, 0.9]])
GIFTS = [  # (center x, width, height rows, box, ribbon)
    (-0.66, 14, 6, (0.25, 0.4, 1.0), (1.0, 0.85, 0.3)),
    (-0.47, 9, 4, (1.0, 0.3, 0.35), (1.0, 1.0, 1.0)),
    (0.55, 12, 7, (0.95, 0.4, 0.75), (0.95, 0.95, 1.0)),
    (0.72, 8, 4, (0.3, 0.85, 0.5), (1.0, 0.3, 0.3)),
]
rain = LetterRain(rng, density=0.5)
snow = Snow(rng, n=240)
front = rng.random(240) < 0.3


def cone_point(h, ang, rot):
    """point on the cone -> screen x, facing z."""
    r, _ = tree_radius(h)
    return r * np.sin(ang + rot), np.cos(ang + rot)


def draw(g, t):
    fade = 1.0 - ease(ramp(t, *T_FADE))
    rot = SPIN * t

    # 1) background: letter rain + far snow
    rain.draw(g, t, (0.09, 0.11, 0.2))
    snow.draw(g, t, 0.75, ~front)

    # 2) ground
    a = ease(ramp(t, *T_GROUND)) * fade
    gm = (g.Y > GROUND) & (g.Y < GROUND + 0.022)
    wave = np.sin(g.c * 0.7 + g.r * 1.3)
    g.put(gm, np.where(wave > 0.3, CIDX["~"], CIDX["_"])[gm],
          (0.45, 0.55, 0.8), 0.55 * a)

    # 3) trunk rises
    p = ease(ramp(t, *T_TRUNK))
    top = TRUNK_BOT - p * (TRUNK_BOT - TREE_BOT + 0.01)
    tm = (np.abs(g.X) < 0.045) & (g.Y > top) & (g.Y < TRUNK_BOT)
    g.put(tm, np.where(g.c % 2 == 0, CIDX["|"], CIDX["#"])[tm],
          (0.62, 0.36, 0.18), fade)

    # 4) tree: letters wrapped on a spinning cone
    h = to_h(g.Y)
    R, shade = tree_radius(h)
    inside = (h >= 0) & (h <= 1) & (np.abs(g.X) < R)
    grow = smooth(ramp(t, *T_TREE))
    shown = inside & (h >= 1.0 - grow * 1.02)
    s = np.clip(g.X / np.maximum(R, 1e-6), -1, 1)
    phi = np.arcsin(s)                       # surface angle
    z = np.cos(phi)                          # 1 = facing us
    arc = (phi + rot) * R / 0.0185     # one letter per cell
    li = (np.floor(arc) + g.r * 5) % len(WORD)
    letters = idx(WORD)[li.astype(int)]
    lvl = (0.35 + 0.85 * z ** 1.3) * shade
    lvl *= 0.85 + 0.15 * np.sin(t * 3 + g.r * 0.9 + g.c * 0.4)
    col = np.stack([0.2 * lvl, 1.0 * lvl, 0.36 * lvl], -1)
    g.put(shown, letters[shown], col[shown], fade)
    # growth front sparkles
    edge = inside & (np.abs(h - (1.0 - grow * 1.02)) < 0.025)
    if 0 < grow < 1:
        g.put(edge, letters[edge], (0.85, 1.0, 0.85), 1.3 * fade)
    n_letters = int(shown.sum())

    # 5) garland spirals upward
    pl = ease(ramp(t, *T_LIGHTS))
    u = np.linspace(0, 1, N_BULB)            # 0 bottom -> 1 top
    hb = 1.0 - u
    x, zb = cone_point(hb, u * TURNS * 2 * np.pi, rot)
    on = (u < pl) & (zb > -0.15) & (hb > 0.02)
    tw = 0.55 + 0.45 * np.sin(t * 7 + np.arange(N_BULB) * 1.7)
    bc = BULB_COL[np.arange(N_BULB) % 4] * (tw * 1.5)[:, None]
    rr, cc = g.to_cell(x[on], to_Y(hb[on]))
    star = np.where(tw[on] > 0.75, CIDX["*"], CIDX["+"])
    g.put_cells(rr, cc, star, bc[on] * fade)
    n_lights = int(on.sum())

    # 6) ornaments pop in one by one
    n = len(ORN["h"])
    t0 = T_ORN[0] + np.arange(n) / n * (T_ORN[1] - T_ORN[0] - 0.4)
    k = np.clip((t - t0) / 0.4, 0, 1)
    x, zo = cone_point(ORN["h"], ORN["ang"], rot)
    vis = (k > 0) & (zo > 0.05)
    big = np.array([pop(v) for v in k])
    ch = np.where(big > 1.05, CIDX["0"],
                  np.where(ORN["kind"] % 2 == 0, CIDX["@"], CIDX["o"]))
    oc = ORN_COL[ORN["kind"]] * (0.5 + 0.8 * zo)[:, None]
    oc = oc * np.clip(big, 0, 1.4)[:, None]
    rr, cc = g.to_cell(x[vis], to_Y(ORN["h"][vis]))
    g.put_cells(rr, cc, ch[vis], oc[vis] * fade)

    # 7) star + rays
    ps = ease(ramp(t, *T_STAR))
    if ps > 0:
        r0, c0 = g.to_cell(0.0, TREE_TOP - 0.012)
        pulse = 1.2 + 0.4 * np.sin(t * 5)
        gold = np.array([1.0, 0.85, 0.3]) * pulse * fade
        g.put_cells([r0], [c0], [CIDX["@"]], gold[None])
        rays = [(-1, 0, "|"), (1, 0, "|"), (0, -1, "-"),
                (0, 1, "-"), (-1, -1, "\\"), (1, 1, "\\"),
                (-1, 1, "/"), (1, -1, "/")]
        L = int(round(ps * 4))
        for dr, dc, c in rays:
            for i in range(1, L + 1):
                w = (1 - i / 5) * gold
                g.put_cells([r0 + dr * i], [c0 + dc * i * 2],
                            [CIDX[c]], w[None])

    # 8) gift boxes rise from the ground
    for j, (cx, wd, ht, box, rib) in enumerate(GIFTS):
        gt0 = T_GIFT[0] + j * 0.33
        k = pop(np.clip((t - gt0) / 0.5, 0, 1))
        rows = int(round(ht * np.clip(k, 0, 1.2)))
        if rows <= 0:
            continue
        rb, cl = g.to_cell(cx, GROUND)
        cl -= wd // 2
        for i in range(rows):
            r = rb - 1 - i
            for dc in range(wd):
                mid = dc == wd // 2 or i == ht // 2
                cch = CIDX["+"] if mid else CIDX["#"]
                cc_ = np.array(rib if mid else box) * fade
                g.put_cells([r], [cl + dc], [cch], cc_[None])
        if rows >= ht:  # bow
            r = rb - 1 - ht
            g.text(r, cl + wd // 2 - 1, "&&", np.array(rib) * fade)

    # 9) greeting types out
    pt = ramp(t, *T_TEXT)
    n_typed = int(round(pt * len(GREETING)))
    blink = pt < 1 and int(t * 4) % 2 == 0
    warm = np.array([1.0, 0.78, 0.35]) * fade
    caption = (GREETING, n_typed, TEXT_Y, warm, 46, 0.35, blink)

    # 10) near snow
    snow.draw(g, t, 1.0, front)

    deg = np.degrees(rot) % 360
    hud = [HANDLE,
           f"rotation {deg:6.2f}°   lights {n_lights}",
           f"letters {n_letters:,}"]
    return {"hud": hud, "caption": caption}
