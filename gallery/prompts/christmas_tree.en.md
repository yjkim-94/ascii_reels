## Storyboard: Christmas Tree (15 s, file `christmas_tree.py`)

Concept: a ribbon of light spirals up and draws the tree, 480 bulbs light up in a chain, a big star charges and ignites with a flash and a shockwave, fireworks burst behind the tree and `MERRY CHRISTMAS` types out. Effects first: it should feel lavish.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.0 | night sky, stars, falling snow; a white-gold light head starts circling the base, throwing sparks | the hook | |
| 2 | 0.0-4.5 | the head spirals 5 turns up the cone; the tree grows in behind it; its path stays as a golden garland | flash when the head reaches the tip | |
| 3 | 4.5-7.5 | 480 bulbs light up bottom to top, 60 ornaments pop in with a ring of light | wave of lights | lights 0 -> 480, ornaments 0 -> 60 |
| 4 | 7.5-9.0 | bulb colours chase upward, tree turns | form complete | |
| 5 | 9.0-9.6 | sparks rush from the whole tree to the tip, a big star fills from the bottom | tension | |
| 6 | 9.6-12.5 | star ignites: flash, rotating rays, long cross flare, halo, orbiting sparkles; a shockwave ring crosses the screen; 7 fireworks behind the tree; `MERRY CHRISTMAS` types out | **climax** | fireworks 0 -> 7 |
| 7 | 12.5-13.5 | last embers fall, everything twinkles | | |
| 8 | 13.5-15.0 | everything fades, only sky, stars, snow and the ground line remain | loop seam | |

Status block: `@your.handle` / `lights 480   ornaments 60   fireworks 7` / `letters N`.

Palette: sky top (0.01, 0.02, 0.08), sky at the horizon (0.04, 0.07, 0.22), ground (0.10, 0.13, 0.25) -> (0.05, 0.06, 0.12); emerald (0.10, 0.75, 0.35); gold (1.00, 0.82, 0.35); white (1.00, 0.95, 0.85); red (1.00, 0.20, 0.20); snow (0.85, 0.90, 1.00); trunk (0.55, 0.32, 0.15); ornaments red (1.0, 0.18, 0.18), gold (1.0, 0.80, 0.30), silver (0.85, 0.88, 0.95), blue (0.30, 0.50, 1.00); fireworks red (1.0, 0.25, 0.25), gold, green (0.30, 1.00, 0.45), sky (0.40, 0.80, 1.00), pink (1.0, 0.45, 0.80), violet (0.70, 0.45, 1.00), white (1, 1, 1).

## Exact values (model units unless said otherwise)

This reel uses three layers: a picture layer under the letters (smooth image, no bloom), the letter grid (bloom), and a few big glyph sprites. Composite: `picture + bloom(max(grid, sprites))`.

Layout: one `splat` with `cy = 0.47`, `scale = 1` for tree, trunk, garland, ribbon, bulbs, sparks, charge sparks and fireworks (one z-buffer, so the tree hides fireworks behind it). Tree tip y = -0.59 (screen Y 0.18), base y = 0.59 (Y 0.76), trunk to y = 0.67, ground line at screen Y 0.80. `view(P) = rot_x(rot_y(P, 0.35 t), -0.15)`. Key light `normalize(-0.4, -0.7, 0.6)` (replaces the default).

Tree: height h = 0 (tip) .. 1 (base), `y = -0.59 + 1.18 h`. Radius = max over 4 tiers (h from-to, radius from-to): (0-0.32, 0.02-0.17), (0.22-0.55, 0.08-0.26), (0.45-0.80, 0.12-0.35), (0.70-1.00, 0.18-0.42), radius `r0 + (r1 - r0) u^0.9`; in tiers 2-4 the top 30 % is shadowed by `0.35 + 0.65 clip(3.5 u, 0, 1)`. 9,000 surface points: `h = uniform^0.8`, angle uniform, radius x `uniform(0.92, 1.04)` (needles). Normal `(cos a, -0.35, sin a)`. Light: ambient 0.15, key 0.6, rim 0.3, spec 0.1, times shadow, times `0.8 + 0.4 lit` with `lit = smoothstep(ramp(t, 4.5, 7.5))`. Colour emerald blended toward gold by `0.15 lit + 0.6 grow`. Trunk: 500 points on a radius-0.05 cylinder from y 0.59 to 0.67, brightness 0.45.

Ribbon and reveal: `qh = smoothstep(ramp(t, 0, 4.5))`. Spiral point for q in 0..1: on the cone at `h = 1 - q`, angle `pi/2 + 10 pi q`, radius x 1.06 (starts at the front of the base). Tree points are drawn only where `h > 1 - qh` (and qh > 0, so nothing at t = 0). The band just behind the head glows: `grow = exp(-((h - (1 - qh))/0.03)^2)` (only while qh < 1), added x 0.8 to brightness.
- Garland: 900 samples of the spiral with q <= qh, direction glyphs from the screen tangent, brightness `0.5 + 0.2 sin(6t - 30q)`, gold.
- Comet: the same samples with `clip(1 - (qh - q)/0.05, 0, 1)` brightness in gold x 1.6.
- Head: a white `@` (x 1.8) in the splat, plus a 34 px white `@` sprite (x 1.6) and a gold glow `0.5 exp(-d/0.05)` in the picture layer, all faded in over the first 0.2 s.
- Sparks: 260, each tied to a random q; it is born when the head passes q (invert the smoothstep), at the spiral point rotated by the spin at that moment, moves with velocity normal(0, 0.25) per axis plus fall `(0, 0.6, 0) age^2`, lives 0.7 s, brightness `1.1 (1 - age/0.7)`, glyph `*` every third else `+`, gold x 1.4.
- Tip flash when the head arrives: `tip = exp(-((t - 4.5)/0.15)^2)` (used on the star outline).

Bulbs: 3 strands x 160, strand s, index i: `q = (i + 0.5)/160`, `h = 1 - 0.96 q`, angle `pi/2 + 8 pi q + 2.094 s`, radius x 1.03. Each lights at `4.5 + 3.0 (1 - h)` (bottom first). Twinkle `0.7 + 0.3 sin(5t + phase)`, a fresh bulb is brighter for 0.25 s (`x (1 + 0.8 (1 - k))`) and shows `*`, later `*` when twinkle > 0.9 else `+`. Colour index: before 7.5 s `n % 3`; after, `(n + int(4t) - int(6 (1 - h))) % 3` over gold, red, white; colour x 1.5.

Ornaments: 60 on the cone (h uniform 0.12-0.95, angle uniform, radius x 1.05), popping at sorted uniform times in 5.0-7.5 s over 0.35 s. Drawn as sprites only when their view-space z > 0.02 (front half): an `O` of size `26 pop(k) + 4` px in its colour x `(1 + 0.4 lit)`, and a small white `'` highlight (size `14 pop(k) + 4`) offset (-0.008, -0.006). While popping, 10 `.` in a ring of radius `0.015 + 0.05 k` around it.

Star (grid cells, screen space): centre X 0, `Y = 0.47 + (-0.59 - 0.09) x 540/1098 ≈ 0.136`. Distances use X units: `dx = X`, `dy = (Y - Ystar) x 1098/540`. Five-point star: `f = ((atan2(dy, dx) + pi/2 - 0.08 sin(0.7t)) / (2 pi/5)) mod 1`, edge radius `0.045 + (0.11 - 0.045) |1 - 2f|`.
- From 4.5 s: outline cells `|d - edge| < 0.012` as `*` in gold x `(0.45 + 0.8 tip)`.
- Charge 9.0-9.6 (`kc = ramp`) and ignite `ign = smoothstep(ramp(t, 9.6, 9.95))`: the body fills from the bottom, cells with `d < edge` and `dy > 0.11 - 0.22 smoothstep(max(kc, ign))`. Core `d < 0.5 edge` is `@` in white x 1.2 + body colour x 0.3; the rest `#` in `gold (0.9 + 0.7 ign)(1 + 0.25 sin 8t) + white x flash` with `flash = exp(-((t - 9.6)/0.12)^2)`. After ignition the outline turns white x 1.5.
- Charge sparks: 220 random tree points (rotated with the tree) fly to `(0, -0.68, 0.1)` with delay uniform 0-0.3 of the charge, smoothstep over 0.7 of it, `*`, gold x 1.5, brightness `0.9 (1 - k^4)`.
- After ignition (all x ign): 16 rays at angles `2 pi m/16 + 0.3 (t - 9.6)`, alternating length 0.24 / 0.14 x pulse, 10 samples from 1.05 R; a cross flare left/right 0.55 and up 0.30, down 0.22, x `(0.85 + 0.15 sin 6t)`, 40 samples with brightness 1.6 -> 0.1; 12 orbiting `*` at radius 1.5 R, angle `+1.5t`, brightness `0.8 + 0.6 clip(sin(9t + 3 angle), 0, 1)`. Colour `white x 0.5 + gold x 0.9`. Direction glyphs for rays and flares.
- Picture layer: halo `(ign (0.35 + 0.1 sin 8t) + 0.6 flash) exp(-d/0.16)` in gold, plus a whole-screen white `0.16 flash`.
- Shockwave: for 0.9 s after 9.6, cells with `|d - 1.9 age| < 0.03` (d from the star centre in X units) get `o`/`.` alternating, colour `(0.6 white + 0.6 gold)(1 - age/0.9)`.

Fireworks: bursts at 9.9, 10.3, 10.7, 11.0, 11.4, 11.8, 12.2 s at screen (X, Y) = (-0.62, 0.20), (0.55, 0.16), (-0.25, 0.10), (0.70, 0.30), (-0.70, 0.34), (0.20, 0.08), (-0.05, 0.24). They live at depth z = -1.4 (convert screen -> model with `k = 3.2 / (3.2 + 1.4)`), so the tree hides them.
- Rocket: 0.45 s before the burst a white `|` trail of 8 samples rises from Y 0.80 to the burst point (ease-out), brightness 1 -> 0.2.
- Burst: 120 particles, angle uniform, speed uniform 0.25-0.50. Radius `speed (1 - exp(-2.5 a)) / 2.5 x 2.2`, `X = X0 + r cos`, `Y = Y0 + (r sin + 0.09 a^2) x 540/1098`. Draw each particle at ages a, a - 0.05, a - 0.10 with weights 1, 0.6, 0.35; the head uses `*` every 4th else `+`, the two trail samples use direction glyphs of `(cos, sin + 0.3 a)`. Brightness `w 1.6 exp(-age/1.0)(0.7 + 0.3 sin(20 age + 5 angle))`, alive for 1.8 s. Two colours per burst (alternating particles), colour x 1.4.
- Sky tint: from each burst, `0.10 exp(-age/0.35)` x its first colour added to the picture layer above the ground.

Background
- Picture layer: vertical gradient sky top -> horizon colour at Y 0.80, then ground (0.10, 0.13, 0.25) -> (0.05, 0.06, 0.12). Warm ground glow `0.12 lit exp(-hypot(X/0.6, 5 (Y - 0.80)))` in gold.
- Stars: 150, X uniform, Y uniform 0-0.62, twinkle `0.3 + 0.7 clip(sin(2.4t + phase), 0, 1)^3`, glyph `*` > 0.8, `+` > 0.5, else `.`, snow colour x 0.6 x twinkle.
- Snow: 280 flakes falling (y = (y0 + v t) mod 1, v uniform 0.025-0.08 per s at half speed, sway 0.005-0.02), glyph by size `*`, `+`, `.`; 28 % of them are drawn after everything else (in front of the tree) at brightness 0.9, the rest first at 0.55.
- Ground line: grid cells Y 0.80-0.816, `~` where `(col + row) % 4 == 0` else `_`, snow colour x 0.35.

Caption: `MERRY CHRISTMAS`, bold monospace 46 px, letter spacing +35 %, centred at Y 0.835, gold x 1.1, typed over 10.0-11.4 s with a blinking cursor; sparkles: cells within |Y - 0.835| < 0.03 and |X| < 0.75 x progress where `sin(13t + 1.7 col + 3.1 row) > 0.93` get a gold `*`.

Counters: `lights` = bulbs already lit; `ornaments` = ornaments popped (all 60, front or back); `fireworks` = bursts so far; `letters` = cells drawn by the main splat.

Fade: everything except sky, stars, snow and ground line is multiplied by `1 - ease_out_cubic(ramp(t, 13.5, 15.0))` (colours of points, sprites, star, caption and the picture-layer glows).

Intended, keep it: in the first second the ribbon circles low around the base, so it reads as a glowing ring before it climbs; fireworks appear only around the tree (hidden behind it); the ignition flash whitens the screen for a moment.
