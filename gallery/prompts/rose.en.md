## Storyboard: Rose (15 s, file `rose.py`)

Concept: sparks swirl into one point of the soil, a stem shoots up and unfolds two leaves, a bud forms, and a big crimson rose opens petal by petal, then bursts with golden light and pollen. No text on screen.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.2 | 420 sparks swirl down into one point of the soil; from 0.6 s soil kicks up and the stem tip breaks through | the hook | |
| 2 | 0.6-4.0 | stem grows bottom -> top in a gentle S, thorns appear; leaves unfold from 2.4 s | growing tip glows | |
| 3 | 4.0-5.5 | a bud wrapped in green sepals forms on the tip and swells | | |
| 4 | 5.5-6.5 | the five sepals fold back and down, crimson shows | | |
| 5 | 6.5-10.0 | 34 petals in 5 layers open, outer layer first, each petal at a slightly different moment; the flower slowly turns | each petal's rim flares as it opens | petals 0 -> 34, layers 0 -> 5, bloom 0 -> 100% |
| 6 | 10.0-12.0 | full bloom: golden rays burst from the heart, pollen sprays out and drifts up | **climax** | |
| 7 | 12.0-13.5 | the open rose keeps turning, pollen floats | | |
| 8 | 13.5-15.0 | everything fades, only the drifting motes and the soil line remain | loop seam | |

Status block: `@your.handle` / `petals 34   layers 5   bloom 100%` / `letters N`.

Palette: crimson (0.78, 0.05, 0.15), scarlet (1.00, 0.25, 0.35), pink (1.00, 0.60, 0.70), petal rim (1.00, 0.45, 0.55), stem/leaf green (0.18, 0.65, 0.28), sepal green (0.20, 0.55, 0.25), gold (1.00, 0.82, 0.40), motes (0.60, 0.30, 0.30), soil (0.35, 0.22, 0.15), thorns (0.35, 0.40, 0.15), sparks (1.0, 0.55, 0.45).

## Exact values (model units unless said otherwise)

The whole plant (stem, thorns, leaves, sepals, petals, petal outlines, pollen) is ONE `splat` call with `cy = 0.44`, `scale = 1.0` (model y = 0 is the stem tip, screen Y 0.44). The light rays are a second splat drawn afterwards (brighter wins). Shared key light for everything: `L = normalize(-0.45, -0.75, 0.55)` (replaces the default). All lighting below uses the default formulas with the weights given (ambient + key x diff + rim x rimterm + spec x specterm), no glints.

Background (never faded, it is the loop frame)
- Motes: 170 points, screen X uniform -1..1, Y uniform 0..0.83, each rises at `k * 0.83 / 15` per second (k = 1 or 2 at random, so they loop exactly), wrapping within 0..0.83. Twinkle `tw = 0.25 + 0.75 * clip(sin(4 t + phase), 0, 1)^2`; glyph `+` if tw > 0.8 else `.`; colour motes x tw.
- Soil: grid cells with screen Y 0.83..0.848, glyph `.` where `(col * 7 + row) % 3 == 0` else `_`, colour soil x 0.6.

Hook (screen space, grid cells, before the plant)
- Sparks: 420, radius r0 uniform 0.25-0.8, angle a0 uniform, delay uniform 0-0.35 s. Progress `k = clip((t - delay) / 0.85, 0, 1)`; drawn while t < 1.2 and k < 1. Radius `r0 (1 - smoothstep(k))`, angle `a0 + 3.5 k`, screen `X = r cos a`, `Y = 0.81 - 0.55 r |sin a|`. Brightness `(0.5 + 0.8 k) * clip(t / 0.15, 0, 1)`, glyph `*` if k > 0.7, `+` if > 0.35, else `.`, colour sparks x brightness.
- Soil burst for `d = ramp(t, 0.6, 1.9)` while 0 < d < 1, with `tt = 1.35 d` and fading `fl = 0.9 (1 - d)`: 70 grains, X = `dirx * speed * tt` (dirx ~ normal(0, 0.6), speed uniform 0.15-0.4), Y = `0.83 - up * speed * tt * 0.5 + 0.25 tt^2` (up uniform 0.4-1.0), glyph `.` or `,`, colour soil x 1.8 x fl. A row of 21 `~` from X -0.1 to 0.1 at Y 0.835, colour soil x 2.2 x fl. A halo: grid cells with `hypot(X/0.12, (Y-0.83)/0.05) < 1` and Y < 0.85 get `.` in (1.0, 0.6, 0.35) x 0.8 fl.

Stem
- Axis for s = 0 (soil) .. 1 (tip): `x = 0.045 sin(1.5 pi s) + 0.010 sin(1.2 t + 2 s) s`, `y = 0.79 (1 - s)`, `z = 0.030 cos(1.2 pi s)`.
- A tube of radius 0.022: 150 samples along s x 10 around. Visible where `s <= grow` and grow > 0, `grow = ease_out_cubic(ramp(t, 0.6, 4.0))`.
- Light: ambient 0.15, key 0.6, rim 0.3, spec 0.1. Growing tip: add `0.7 exp(-((s - grow)/0.03)^2)` while grow < 1 and lighten the colour by the same amount x 0.5.
- Thorns: at s = 0.20, 0.30, 0.45, 0.60, 0.70, 0.82, alternating right/left, one point offset 0.034 in x; glyph `>` on the right, `<` on the left; brightness 0.55 once the stem has passed.

Leaves (2): at s = 0.36 pointing to (-1, 0, 0.35) and s = 0.55 pointing to (1, 0, 0.25), normalized. `kl = smoothstep(ramp(t, 2.4, 4.0))`. Grid u 0..1 (22) x v -1..1 (9). Length `0.17 (0.3 + 0.7 kl)`; spine `base + len (u dir + 0.25 u^2 (0, 1, 0))` (droops); width `0.055 sin(pi u)^0.8 (1 + 0.08 sin(30 u))`; the two halves fold along the midrib by `fold = 1.3 - 1.05 kl`: point = spine + `perp * v w cos(fold) + (0, -1, 0) |v| w sin(fold)` with `perp = normalize(dir x (0, -1, 0))`. Two-sided normals (flip toward the camera). Light: ambient 0.15, key 0.65, rim 0.3, spec 0.15; midrib `|v| < 0.15` adds 0.25.

Flower head frame: build petals around the head axis (0, -1, 0), then `head_view(P) = rot_x(rot_y(P, 0.25 t), -0.85) + stem_axis(1, t)` (spin around its own axis, lean 0.85 rad toward the camera so we look into it). Normals go through the same rotations (no translation) and are flipped toward the camera (two-sided).

Petals: 34 in 5 layers k = 0 (inner) .. 4 (outer) with 3, 5, 7, 9, 10 petals
- Per layer: length 0.20, 0.28, 0.36, 0.44, 0.50; base radius r0 0.014, 0.036, 0.058, 0.080, 0.098; width factor 0.78, 0.72, 0.68, 0.64, 0.62 (narrower outside, so gaps show between petals); bud angle 0.08, 0.14, 0.20, 0.26, 0.32 rad; open angle 0.20, 0.42, 0.65, 0.88, 1.05; tip curl 0.15, 0.30, 0.45, 0.60, 0.75.
- Petal i of layer k sits at angle `phi = 2 pi i / n_k + 2.4 k`. Each petal gets its own small randomness: length x (1 + normal(0, 0.07)), open angle + normal(0, 0.06), curl + normal(0, 0.10), and opens at `6.5 + (4 - k) 0.6 + 0.05 i + uniform(0, 0.08)` s over 1.1 s with smoothstep (`po`).
- Head size `size = (0.75 kb + 0.25 mean(po))` with `kb = smoothstep(ramp(t, 4.0, 5.5))`; nothing of the head is drawn before 4.0 s. Length and r0 are multiplied by size.
- Petal surface, u = 0.02..1 (18 samples), v = -1..1 (13): `rad = (cos phi, 0, sin phi)`, `tan = (-sin phi, 0, cos phi)`. Angle along the spine `th(u) = theta + curl u^2` with `theta = bud + (open - bud) po`, `curl = curl_k po`. Spine = `r0 rad + cumsum(sin th rad + cos th (0, -1, 0)) / 18 * length`. Half width `w = widthfactor * length * u^0.55 (1 - 0.3 u^5)`. Point = spine + `tan v w` - `rad (cup v^2 w)` with `cup = 0.5 - 0.25 po` + `rad (0.5 po ((max(|v| - 0.55, 0)/0.45)^2) w u)` (open petal edges roll outward).
- Normals from the grid: `cross(d/du, d/dv)`.
- Colour: `crimson + (scarlet - crimson) (1 - k/4) 0.8`, times `0.55 + 0.45 min(u/0.25, 1)` (darker base).
- Brightness: light with ambient 0.12, key 0.6, rim 0.35, spec 0.2, times `(0.5 + 0.5 u)` times veins `0.85 + 0.15 cos(9 v) * (1 if u > 0.15 else 0)`. Edge factor `E = max(|v|^4, u^6)`; while a petal opens add `0.6 * 0.5 sin(pi po) E`.
- Climax `kc = smoothstep(ramp(t, 10.0, 10.6)) (1 - 0.5 smoothstep(ramp(t, 10.8, 12.0)))`: add `0.3 kc E` and a golden heart `core = 0.45 kc (1 - k/4)(1 - u)`; colour blends toward pink by `E (0.2 po + 0.3 kc)` and toward gold by `core`.
- Petal outlines (this is what makes every petal readable; do not drop them): for every petal, sample both long edges (u = 0.05..1, 36 samples, v = -1 and 1) and the tip (u = 1, v = -1..1, 20 samples) with the same surface formula. Glyph = direction glyph of the outline's screen tangent (`| / \ -`). Move each outline point 0.004 toward the camera (after head_view) so a front petal's rim wins over its own face. Brightness `(0.85 + 0.15 sin(pi po)) (1 + 0.4 kc)`, colour rim (1.00, 0.45, 0.55) blended toward pink by `0.5 kc`.

Sepals: 5 green blades at angles `2 pi j / 5 + 0.3`, same surface formula with width factor 0.35, length `0.20 size + 0.02`, r0 `0.05 size`, cup 0.3, angle `0.12 + 2.2 ks`, curl `0.3 ks`, `ks = smoothstep(ramp(t, 5.5, 6.5))`. Light: ambient 0.15, key 0.6, rim 0.3, spec 0.1.

Pollen: 320 grains, each starting at `10.0 + uniform(0, 1.2)` s, alive for 3.5 s, from the heart `head_view((0, -0.06, 0))`. Direction: normal(0, 1) in 3D with `y = -0.6 |y| - 0.1`, normalized; speed uniform 0.15-0.45. Position `heart + dir speed age^0.6 + (0, -0.04, 0) age`. Brightness `1.2 exp(-age / 1.6)`; glyph `*` for every 5th, then alternating `.` and `+`; colour gold x 1.3.

Light rays (second splat, model units around the heart, in the screen plane): `kr = smoothstep(ramp(t, 10.0, 10.5)) (1 - 0.6 smoothstep(ramp(t, 10.6, 12.0)))`. 16 rays at angles `2 pi m / 16`, length `0.12 + 0.48 kr (1 + 0.35 cos 4a)`, 16 samples from 0.06 to the length, placed at `heart + (cos a s, sin a s, 0.3)`, brightness `(1 - 0.85 s/len) kr`, direction glyphs, colour gold x 2.4.

Counters: `petals = round(sum(po))`; `layers` = number of layers whose petals are all fully open (po > 0.99); `bloom = mean(po) * 100` with no decimals; `letters` = cells drawn by the plant splat.

Fade: the colour of the plant, pollen and rays is multiplied by `1 - ease_out_cubic(ramp(t, 13.5, 15.0))`; motes and soil are not faded.

Intended, keep it: at full bloom the outer petals hang down over the top of the stem; the back petals overlap so densely that they read as texture while the front petals show clear outlines.
