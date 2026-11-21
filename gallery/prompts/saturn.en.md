## Storyboard: Saturn (15 s, file `saturn.py`)

Concept: scattered dust spirals in and becomes a planet, then particles spread out from its equator into rings. No text on screen.

Objects
- Stars: ~180 fixed points over the whole screen, each twinkling on its own beat (`. + *`).
- Dust: 4,812 points on a wide thin spiral disk (radius 0.40-0.88 of half the screen width), tilted ~55 degrees so the swirl is seen face-on, not edge-on. Each grain lands on its own point of the planet surface after a random delay.
- Planet: a Fibonacci-sphere point cloud, radius 0.28, poles squashed by 10 %, centred a bit above the middle of the render. Latitude cloud bands (cream / amber / deep amber) and one small storm oval so the spin is visible. Rotates 0.35 rad/s.
- Rings: 12,000 particles in the equatorial plane at 1.24-2.27 planet radii, split into C, B (densest) and A rings with a Cassini gap. Inner particles orbit faster (speed ~ r^-1.5). The planet casts a soft shadow on the rings.
- Sun: a bright point plus 12 short rays made of direction glyphs, placed behind the planet so the z-buffer hides it until it rises past the limb.

Palette
- Stars (0.60, 0.65, 0.80), dim.
- Planet: cream (1.00, 0.88, 0.65), amber (0.95, 0.62, 0.28), deep (0.70, 0.45, 0.25).
- Rings: beige (0.90, 0.82, 0.65).
- Climax: gold (1.00, 0.85, 0.45) and white.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.0 | stars; dust fades in and starts to swirl inward | the hook | dust 0 |
| 2 | 1.0-4.5 | dust spirals into a sphere | the surface flashes bright when the last grain lands (~4.5 s) | dust -> 4,812 |
| 3 | 4.5-6.0 | planet spins, cloud bands fade in | | |
| 4 | 6.0-9.5 | particles fly out from the equator to their orbits, inner rings first; the system tilts to 26.73 degrees | Cassini gap opens | ring -> 12,000, tilt 0 -> 26.73 |
| 5 | 9.5-12.0 | the sun rises from behind the planet to the upper left; the key light swings from front to behind | **climax**: rings glow gold by forward scattering, the planet becomes a bright crescent rim, rays appear | |
| 6 | 12.0-13.5 | back-lit planet keeps turning | | |
| 7 | 13.5-15.0 | everything fades, only stars remain | loop seam | |

Status block: `@your.handle` / `dust 4,812   ring 12,000   tilt 26.73°` / `letters N`.
