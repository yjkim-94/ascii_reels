## Storyboard: Saturn (15 s, file `saturn.py`)

Concept: scattered dust spirals in and becomes a planet, then particles spread out from its equator into rings. No text on screen.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.0 | stars; dust fades in and starts to swirl inward | the hook | dust climbs from 0 |
| 2 | 1.0-4.5 | dust spirals into a sphere | short flash when the grains land (~4.55 s) | dust -> 4,812 |
| 3 | 4.5-6.0 | planet spins, cloud bands fade in | | |
| 4 | 6.0-9.5 | particles fly out from the equator to their orbits, inner rings first; the system tilts 0 -> 26.73 deg | Cassini gap opens | ring -> 12,000, tilt -> 26.73 |
| 5 | 9.5-12.0 | sun rises from behind the planet to the upper left; key light swings from front to behind | **climax**: rings glow gold, the planet's limb glows, rays appear | |
| 6 | 12.0-13.5 | back-lit planet keeps turning | | |
| 7 | 13.5-15.0 | everything fades, only stars remain | loop seam | |

Status block: `@your.handle` / `dust 4,812   ring 12,000   tilt 26.73°` / `letters N`.

Palette
- Stars (0.60, 0.65, 0.80). Loose dust: cream.
- Planet: cream (1.00, 0.88, 0.65), amber (0.95, 0.62, 0.28), deep (0.70, 0.45, 0.25).
- Rings: beige (0.90, 0.82, 0.65).
- Climax: gold (1.00, 0.85, 0.45) and white (1, 1, 1).

## Exact values (model units unless said otherwise; R = planet radius)

All of the following are in model units. One `splat` call for planet + dust + rings + sun with `cy = 0.42`, `scale = 1.15`, so 1 model unit = 1.15 x half the screen width.

Frames
- `view(P) = roll(rot_x(P, -radians(tilt)), -0.22)`, where `rot_x` is the usual x-axis rotation with y down and z toward the viewer, and `roll` rotates in the screen plane (x, y). Planet, dust and rings use `view`. The sun and its rays do NOT: they are given directly in view space.
- `tilt = 26.73 * smoothstep(ramp(t, 6.0, 9.5))` degrees.

Stars: 180 points, screen X uniform -1..1, Y uniform 0..0.86. Twinkle `tw = 0.35 + 0.65 * clip(sin(2.2 t + phase), 0, 1)^3`; glyph `*` if tw > 0.8, `+` if > 0.5, else `.`; colour star x tw x 0.8.

Planet = the dust after it lands (no extra points)
- Surface: 4,812 points on a Fibonacci sphere `u`, scaled by (R, 0.9 R, R) with R = 0.28. Normals: `u * (1, 1/0.9, 1)`. Spin: `rot_y(.., 0.35 t)`.
- Bands on latitude `lat = u.y`: `b = sin(19 lat) + 0.45 sin(47 lat + 1.3)`; b > 0.6 cream, b > -0.4 amber, else deep. Bands blend in from plain cream with `smoothstep(ramp(t, 4.5, 6.0))`.
- Storm: darken by 35 % x `exp(-((lat - 0.35)/0.07)^2 - ((lon - 1.0)/0.25)^2)`, lon = atan2(u.z, u.x).

Dust
- Start: radius uniform 0.40-0.88, angle a0 uniform 0..2pi (no spiral arms), height normal(0, 0.03). The disk is turned by `rot_x(-0.95)` (about 54 deg from edge-on) so the swirl is seen at an angle. At the start the outermost grains run slightly past the screen edges; that is fine.
- Each grain: delay uniform 0-1.4 s, progress `k = smoothstep(clip((t - delay) / 3.1, 0, 1))`. Disk angle `a0 + 0.9 t + 3.0 (1 - k)`. Position = `start * (1 - k) + spinning_surface_point * k` (straight blend in 3D).
- Loose-dust brightness: uniform 0.15-0.5, times a fade-in `smoothstep(ramp(t, 0, 0.6))`.

Lighting (planet)
- `sun = (-0.10 - 0.30 ks, -0.05 - 0.22 ks, -1.2)` with `ks = smoothstep(ramp(t, 9.5, 12.0))`. Key light `L = normalize(front * (1 - ks) + normalize(sun) * ks)` with `front = normalize(-0.5, -0.6, 0.65)`. This replaces the default key light.
- `diff = max(0, n.L)`, `edge = (1 - |n.z|)^1.5`, rim light `r = normalize(cos 0.9t, -0.4, sin 0.9t)`, `rim = max(0, n.r) * edge`, `spec = max(0, n.normalize(L + (0,0,1)))^12`.
- `lum = 0.10 + 0.75 diff + (0.35 + 0.9 ks) rim + 0.15 spec`. No glints on the planet.
- Then `lum = lum * k + dust_brightness * (1 - k)`, plus the limb glow `0.8 ks (1 - |n.z|)^2 k` (it lights the whole limb evenly, a thin halo around the dark disk; do not reshape it into a one-sided crescent), plus the landing flash `0.9 exp(-((t - 4.55)/0.18)^2) k`. Clip to 0..1. The flash is brief; the climax wins by lasting longer and covering the rings too.
- Planet colour: band colour, then blended 60 % toward gold by `ks`.

Rings: 12,000 particles in the equatorial plane
- C ring 2,500 at 1.25-1.50 R (depth 0.55), B ring 6,000 at 1.50-1.86 R (depth 1.0), Cassini gap 1.86-1.93 R (empty), A ring 3,500 at 1.93-2.29 R (depth 0.75). Depth is multiplied by `0.8 + 0.2 sin(180 r)` for ringlets. Radius r uniform inside each ring, angle uniform.
- Spread: a particle starts at `6.0 + (r - 0.35) * 6` s (r in model units) and moves from 1.03 R out to r over 1.2 s with smoothstep. Orbit angle `a0 + 0.55 (r/0.35)^-1.5 t`.
- Brightness: `depth * (0.25 + 0.55 |up . L|) + 0.9 * ks * max(0, -L.z) * depth`, where `up` is the ring-plane normal `view((0, -1, 0))`. Shadow: in view space, if `p . L < 0` and the distance from p to the line through the planet centre along L is < R, multiply by 0.35 (hard edge).
- Colour: beige blended to `0.6 gold + 0.4 white` by `ks`.

Sun (view space, hidden by the planet through the shared z-buffer)
- Core: one `@` at `sun`. 12 rays at angles a = 0, 30, ... 330 deg; ray length `0.06 + 0.22 ks (1 + 0.5 cos 3a)`; 14 samples along each ray from 0.02 to its length; ray glyph from its direction (`| / \ -`); brightness `(1 - 0.8 s/len) * ks`; colour gold x 1.6. Rays do not rotate.

Counters
- `dust = int(4812 * mean(k))` (climbs smoothly from the first frame).
- `ring = int(12000 * mean(spread progress))`, `tilt` as above with 2 decimals, `letters` = cells drawn by the planet/ring/sun splat.

Fade: everything except the stars is multiplied by `1 - ease_out_cubic(ramp(t, 13.5, 15.0))`.
