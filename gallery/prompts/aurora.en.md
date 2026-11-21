## Storyboard: Aurora (18 s, file `aurora.py`)

Concept: pitch-black night. A shooting star lights the first stars, a pine forest and a lake appear, aurora curtains grow one by one, the sky holds its breath, then a pulse of light runs along the curtains and a substorm erupts: curtains fold into S-curls, rays shoot to the top of the sky and the lower hems burn pink, all mirrored in the lake. No text on screen.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.5 | darkness; a shooting star crosses, stars pop on along its path | the hook | stars 0 -> 60 |
| 2 | 1.0-4.0 | stars fill the sky, Milky Way, forest silhouette and lake appear; each star also appears in the lake | | stars -> 400 |
| 3 | 4.0-7.0 | a faint green band rises above the horizon and undulates | first green on the lake | bands 1, kp 1 -> 3 |
| 4 | 7.0-11.0 | bands 2-5 join one per second, rays drift sideways, tops turn violet | the sky brightens with each band | bands -> 5, kp -> 6 |
| 5 | 11.0-12.0 | calm: curtains dim a little, stars twinkle faster | the pause before the storm | |
| 6 | 12.0-12.8 | a bright pulse runs left -> right and wakes the curtains behind it | climax starts | kp -> 8 |
| 7 | 12.8-15.0 | substorm: folds, fast undulation, rays to the top, pink hems; the lake mirrors it | **climax** | kp 9 |
| 8 | 15.0-16.5 | the storm slows and settles back into soft green | | |
| 9 | 16.5-18.0 | aurora, then land, then stars fade to black | loop seam | |

Status block: `@your.handle` / `stars 400   bands 5   kp 9` / `letters N`.

Palette: sky top (0.01, 0.02, 0.06), sky at horizon (0.04, 0.07, 0.16), water (0.05, 0.10, 0.18) -> (0.01, 0.02, 0.04), trees (0.008, 0.012, 0.025), stars (0.85, 0.90, 1.00), aurora hem green (0.35, 1.00, 0.60), body green (0.10, 0.80, 0.45), violet (0.60, 0.30, 0.95), pink (1.00, 0.40, 0.70), pulse white (0.90, 1.00, 0.95).

## Exact values (screen units: X -1..1, Y 0 top .. 1 bottom of the render)

Two layers: a picture layer (smooth image under the letters, computed at 270 x 274 and upscaled, no bloom) and the letter grid (bloom). Horizon / tree line at Y 0.60, the lake mirrors about Y 0.612 and ends at Y 0.86.

Fades: `f_aur = 1 - ease(ramp(t, 16.5, 17.3))`, `f_land = 1 - ease(ramp(t, 17.0, 17.6))`, `f_star = 1 - ease(ramp(t, 17.3, 18.0))`; `reveal = smoothstep(ramp(t, 1.0, 4.0))`.

Aurora field `aurora(X, Y, t)` -> intensity A and colour C (used on both layers):
- Five bands b = 0..4, born at 4, 7, 8, 9, 10 s, `a = smoothstep(ramp(t, born, born + 1.5))`. Base heights 0.50, 0.42, 0.35, 0.28, 0.21 (band 0 starts 0.08 lower and rises over 4-7 s); amplitudes 0.030, 0.040, 0.045, 0.050, 0.040; frequencies 2.2, 1.7, 2.6, 1.9, 2.4; random phase each; curtain heights H 0.10, 0.13, 0.15, 0.16, 0.14.
- Storm level `G(t) = smoothstep(clip((t - 12.5)/0.7, 0, 1)) (1 - smoothstep(clip((t - 15)/1.5, 0, 1)))` and its running integral `GI(t)` (integrate numerically). `phase = 0.7 t + 2.2 GI`, `drift = 0.03 t + 0.12 GI` (motion speeds up during the storm without jumps).
- Calm: everything x `1 - 0.3 smoothstep(ramp(t, 11, 11.5)) (1 - smoothstep(ramp(t, 12, 12.8)))`.
- Light wave: front `xw = -1.3 + 2.8 ramp(t, 12.0, 12.8)`; `pulse = exp(-((X - xw)/0.12)^2)` only while the wave runs; `awake = smoothstep(clip((xw - X)/0.4, 0, 1))` for t >= 12 (fading out over 15-16.5 s); storm where awake `S = awake * smoothstep(ramp(t, 12.3, 13.3))`.
- Lower edge `y0 = base + amp sin(freq X + phase + ph) + 0.012 sin(5.3 X - 1.6 phase + b) + S 0.045 sin(4.2 X + 2.4 phase + 1.7 b)` (the last term is the substorm S-fold). `hgt = y0 - Y`.
- Rays: 1D noise along X: `u = (0.35 X + drift (1 + b % 2) + 0.2 b) mod 1`, value r in 0..1, `ray = 0.35 + 0.65 clip((r - 0.25)/0.6, 0, 1)^1.5`.
- Curtain: `exp(-hgt / (H (1 + 1.8 S)))` above the edge, `exp(hgt / 0.006)` below (sharp hem). Fade toward the sides `clip(1.15 - 0.5 |X|, 0, 1)`.
- `I = a * curtain * ray * side * (0.55 + 0.1 b) * calm * (1 + 0.7 S + 1.2 pulse)`.
- Colour: `edge = exp(-max(hgt, 0)/0.035)`, `top = (1 - edge)(0.35 + 0.65 smoothstep(ramp(t, 7, 11)))`, `col = hem_green edge + body_green (1 - edge)(1 - top) + violet top`, then toward pink by `0.85 S edge` and toward white by `0.6 pulse`. A = sum I, C = sum col I.

Picture layer
- Sky: vertical gradient sky top -> sky at horizon (Y 0.60), then water (0.05, 0.10, 0.18) -> (0.01, 0.02, 0.04) at Y 1; whole thing x reveal x f_land. Milky Way: smooth noise, `band = exp(-((0.5 X + Y - 0.32)/0.12)^2)`, add `clip(noise - 0.5, 0, 1) band 0.12 reveal f_star` x star colour.
- Aurora glow: add `0.55 f_aur C` above the horizon.
- Meteor glow until 1.4 s: `0.7 exp(-d/0.07)` around its head.
- Forest: 70 pine triangles, centre X uniform -1.05..1.05, height 0.025-0.085, half width = height x uniform(0.35, 0.5), sitting on Y 0.60; colour trees x `(0.5 + 0.5 reveal)`.
- Lake (Y > 0.612): the sky picture flipped about 0.612, each pixel shifted sideways by `(ripple_noise - 0.5) x 60 (Y - 0.612)` pixels (more ripple further down), added at x 0.45 on top of the water gradient.

Letter grid
- Stars: 400. The first 60 lie along the meteor path from (-0.95, 0.20) to (0.85, 0.48) (+ normal(0, 0.06) in X, normal(0, 0.03) in Y) and light at `1.2 s x` their position along it; the other 340 are uniform in X, Y 0..0.54 and light at uniform 1.4-3.6 s. Twinkle `tw = 0.35 + 0.65 clip(sin((2 + 3 smoothstep(ramp(t, 11, 12))) t + phase), 0, 1)^2`; pop when lit `1 + 1.5 exp(-age/0.15)`; brightness `clip(age/0.1, 0, 1) tw f_star pop`; glyph `*` > 0.85, `+` > 0.55, else `.`.
- Meteor (0-1.2 s, progress `ease(ramp(t, 0, 1.2))`): 30 samples over the last 0.35 of the path, brightness `linspace(0.1, 1)^2 x 1.2`, direction glyphs, drawn on 3 rows (offsets -0.017, 0, +0.017, side rows x 0.6), colour star x 1.6, head `@` star x 2.4.
- Aurora rays on sky cells (Y < 0.59) with A > 0.12: `|` if A > 0.55, `:` if > 0.28, else `.`; colour `C / A * min(A, 1.3) * f_aur`.
- Lake reflection on cells 0.622 < Y < 0.86: evaluate the aurora at `Y' = 2 x 0.612 - Y`; where A > 0.2 draw `-` or `~` (by `sin(0.9 col + 2.3 row + 2t) > 0`), colour `C / A * min(A, 1) * 0.5 f_aur f_land`.
- Star reflections: each lit star whose mirrored Y `2 x 0.612 - Y` falls in the lake, X jittered by `0.006 sin(3t + 4 phase)`, brightness x 0.5 f_land, drawn at that row and once more one row lower at x 0.45 (stretched by the ripples); `+` if brightness > 0.4 else `.`.

Camera (whole render area; keyframes time, zoom, focus X, focus Y, smoothstep between): (0, 1.25, 0, 0.68), (1, 1.25, 0, 0.68), (4, 1.0, 0, 0.60), (11, 1.08, 0, 0.30), (12, 1.08, -0.25, 0.32), (12.8, 1.08, 0.25, 0.32), (14.2, 1.0, 0, 0.30), (15, 1.0, 0, 0.30), (16.5, 1.05, 0, 0.30), (18, 1.25, 0, 0.68). No shake. Status block, clock and code panel do not move.

Counters: `stars` = stars already lit; `bands` = bands born more than 0.75 s ago; `kp = 1 + 2 ramp(4, 7) + 3 ramp(7, 11) + 2 ramp(12, 12.8) + ramp(12.8, 13.3)` shown without decimals; `letters` = grid cells with colour > 0.05.

Intended, keep it: during the substorm violet and pink fill most of the sky and the green body thins out; the light wave reads as a bright vertical column sweeping left to right; the first and last frames are black.
