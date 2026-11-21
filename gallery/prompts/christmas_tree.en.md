## Storyboard: Christmas Tree (15 s, file `christmas_tree.py`)

Concept: a tree made of letters grows from the ground up, gets lights, ornaments, a star and gifts, and ends with a typed greeting.

Objects
- Background: dim blue letter rain (A-Z, slowly falling per column) plus falling snow (`. + *`); 30 % of the snow passes in front of the tree.
- Ground: a thin band of `_ ~` just below the tree, soft blue.
- Trunk: `| #` in brown, rising from the ground.
- Tree: 3 stacked tiers, tip at the top, widest tier at the bottom (about 0.8 of half the screen width). Each tier's skirt overlaps the next and casts a shadow band. Filled with the word `MERRYCHRISTMASJOYPEACE`, letters wrapped around a slowly spinning cone (front brighter, edges darker).
- Lights: about 240 bulbs on a 6.5-turn spiral around the cone, `* +`, gold / red / sky / pink, twinkling; only the front half is visible.
- Ornaments: 46 random points on the cone, `@ o 0`, red / gold / blue / silver, each popping in with a small overshoot.
- Star: a pulsing gold `@` on the tip with 8 rays (`| - \ /`) growing out.
- Gifts: 4 boxes (`#` with `+` ribbons and an `&&` bow) on both sides of the trunk, rising out of the ground with a bounce.
- Greeting: `MERRY CHRISTMAS 2026` in big letter-spaced gold type under the tree, typed one letter at a time with a blinking cursor.

Palette: letter rain (0.09, 0.11, 0.20); tree green (0.20, 1.00, 0.36) x brightness; bulbs gold (1.0, 0.85, 0.4), red, sky, pink; greeting and star gold (1.0, 0.78, 0.35).

Key layout values
- Tree spans Y 0.11-0.73; trunk down to Y 0.79; ground band Y 0.80-0.82; greeting at Y 0.84.
- Tiers along the tree height h (0 top .. 1 bottom): spans (0.00-0.40), (0.27-0.71), (0.56-1.00); radius grows from (0.02 -> 0.40), (0.16 -> 0.60), (0.26 -> 0.80) as `r0 + (r1 - r0) * u^0.9`. The top 34 % of each lower tier is darkened (x0.25 -> 1) as the shadow of the tier above.
- Fake spin: for a cell inside the tree, `phi = asin(X / R)`, facing `z = cos(phi)`, brightness `(0.35 + 0.85 z^1.3) x shade`, letter index `floor((phi + 0.55 t) * R / 0.0185) + row * 5` over the word.
- Gifts: centres at X -0.66, -0.47, 0.55, 0.72; widths 14, 9, 12, 8 cells; heights 6, 4, 7, 4 rows; colours blue/gold ribbon, red/white, pink/white, green/red.

Scenes
| # | time (s) | what happens | dynamic point | counters |
|---|---|---|---|---|
| 1 | 0.0-1.0 | ground fades in, trunk rises | snow and letter rain move from frame 0 | rotation starts |
| 2 | 0.9-4.6 | tree grows bottom -> top | the growth front sparkles white | letters climb |
| 3 | 4.5-7.8 | garland spirals upward, ornaments pop in one by one | | lights climb |
| 4 | 7.6-9.6 | star and rays, gifts pop up | star pulses | |
| 5 | 9.4-11.6 | greeting types out | **climax** | |
| 6 | 11.6-13.2 | finished tree keeps spinning | | |
| 7 | 13.2-14.6 | everything fades, only background remains | loop seam | |

Status block: `@your.handle` / `rotation 123.45°   lights 128` / `letters N`.
