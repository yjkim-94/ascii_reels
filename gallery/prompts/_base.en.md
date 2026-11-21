You are going to make a short vertical ASCII-art reel with a single Python script.

## Output
- One file `<slug>.py` that renders `<slug>.mp4`: 1080x1920, 30 fps, H.264, yuv420p, no audio, at most 20 seconds (the storyboard states the exact length).
- Use only Python 3, numpy, Pillow and ffmpeg (pipe raw RGB frames into ffmpeg). Install what is missing.
- Every frame must be a pure function of the time `t` (no state carried between frames), so any single frame can be rendered on its own for checking.

## Screen layout
- Top 1098 px: the render. A grid of 108 x 61 character cells, each cell 10 x 18 px. Black background.
- Bottom-left of the render: a status block in a monospace font, 3 lines. Line 1 is the handle (use `@your.handle` unless I give one), lines 2-3 are 2-4 counters that climb as the story progresses, plus `letters N` (cells drawn this frame).
- Top-right of the render: a pink dot and the clock, e.g. `● t 3.27s`.
- Below the render: a code panel that shows this very script. A header bar with the file name on the left and a green dot `running · 30 fps` on the right. Syntax-coloured code (dark theme) with line numbers, scrolling down smoothly at no more than 6 lines per second, one highlighted line with a blinking pink block cursor at its end, as if it is being typed right now.

## How the render works
- Glyph atlas: draw every glyph you use (space, ``.,:;*+'`|-/\_~=#@%&o0O``, A-Z, a-z, 0-9, `$!?<>{}[]()^"`) once into a 10 x 18 bitmap with a bold monospace font (e.g. DejaVu Sans Mono Bold, size 15).
- Brightness ramp: sort all glyphs except space and `_` by ink coverage (mean of the bitmap) and take 28 evenly spaced entries. The ramp mixes letters, digits and symbols (e.g. `` ` - " ! c | > l C f 7 v e { x n E y 6 k m p d A & H @ M ``); that letter-soup texture is intended. A cell's brightness (0-1) picks `ramp[int(b * 27)]`.
- Each cell holds one glyph index and one RGB colour (may exceed 1 for highlights). Composite: glyph bitmap x colour, then a bloom pass (downscale 4x, Gaussian blur, upscale, add ~0.9x) for a soft glow.
- Brighter wins: a cell is only overwritten by something brighter (compare the max RGB channel). Fading objects reveal the background instead of leaving black holes.
- Inside one 3D draw call the nearest point per cell wins (z-buffer); between separate draw calls and layers (background, objects, text) brighter wins. Draw everything that should occlude each other (e.g. a planet hiding a sun) in the same call.
- 3D objects are point clouds: sample thousands of surface points (with normals), rotate them, perspective-project to cells, keep the nearest point per cell (z-buffer), and shade with a key light, a moving rim light and occasional specular glints.
- Thin lines (rays, tentacles, stems) use direction glyphs `| / \ -` matching the screen direction of the line.
- Background layers: faint twinkling stars or a dim letter rain, so the screen is never dead.

## Story rules
- Something moves in the first second (the hook). The full form is revealed at 55-70 % of the length. One climax that answers the question the reel raises; it stands out by contrast with what came before (size, speed, colour, stillness), not necessarily by being the brightest moment, and its elements are hinted at earlier. The last 1.5 s fades back to the opening frame so the reel loops seamlessly.
- Put all scene times as `T_*` constants at the top of the script: that block reads as a timeline in the code panel.
- Comments in English, lines of at most 68 characters (about 69 fit in the code panel).

## Reference numbers (aim for a similar look, not pixel-exact)
- Coordinates: screen `X` runs -1..1 across the width (0 = centre), `Y` runs 0 (top) .. 1 (bottom of the render). 3D model units: 1 = half the screen width, y points down, z points toward the viewer.
- Projection: `k = f / (f - z)` with `f = 3.2`; screen `X = x*k*scale`, `Y = cy + y*k*scale*540/1098` (so x and y share one unit).
- Point colour = `rgb * (0.35 + 0.9 * brightness)`. Points with brightness <= 0.02 are not drawn at all; this is how things are hidden (a fade-in, a sun that has not risen, a ring particle that has not started). A global fade-out multiplies the colour only, not the brightness used to pick the glyph.
- Rotations (y down, z toward the viewer): `rot_x(a)`: y' = y cos a - z sin a, z' = y sin a + z cos a. `rot_y(a)`: x' = x cos a + z sin a, z' = -x sin a + z cos a. Screen roll `roll(a)`: x' = x cos a - y sin a, y' = x sin a + y cos a.
- Default lighting (the storyboard overrides any of it): key light `L = normalize(0, -0.8, 0.6)`; rim light `r = normalize(cos 0.9t, -0.4, sin 0.9t)` weighted by `(1 - |n.z|)^1.5`; specular `max(0, n . normalize(L + (0,0,1)))^12`.
- Bloom: clip the render to 0..1, convert to 8-bit, resize to 270 x 274 (bilinear), Pillow `GaussianBlur(3)`, resize back (bilinear), add x0.9-1.1 on top of the unclipped render.
- Status block: regular monospace 30 px, colour #e8eaee, 40 px line spacing, 22 px from the left; the top of the first line is at `y = 1098 - 22 - 40 * lines`. Clock: same font, pink #ff6b9e, text `t  3.27s` right-aligned 24 px from the right edge with its vertical centre at y = 37, and a 14 px pink dot 12 px left of the text.
- Code panel: header bar 62 px, #1e2026, file name 26 px #cdd0d6, `running · 30 fps` 26 px #969ca6 after a 16 px green dot #3fb950. Code: regular monospace 24 px, line height 36 px, line numbers 20 px #4e5460 right-aligned in a 64 px gutter, background #16181d. Colours: keywords #c678dd, functions #61afef, strings #98c379, numbers #d19a66, comments #6a737d, UPPER_CASE constants #56b6c2, other text #dcdfe4. All lines are drawn in full (no per-character typing).
- Scrolling: `s(t) = S * ease_out_cubic(min(t / (0.92 * length), 1)^1.15)` lines, with `S = min(lines - visible + 4, 6 * length)` (6 lines/s on average; the start is faster, that is fine); draw with a pixel offset of `s * 36` so it moves smoothly. The highlighted line is the 0-based line index `int(s) + 6` (it moves with the text and steps down one line at a time), its background lifted by +0.05/0.06/0.09 RGB, with a pink block cursor 13 px wide and 26 px tall starting 4 px after its last character, blinking on for 0.4 s and off for 0.4 s.
- Big caption (only if the storyboard has text): bold monospace 46 px, letter spacing +35 %, centred.
- Encoding: `ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart`.

## Timing and looping
- All times and speeds in the storyboard are for its stated length. If you make a shorter or longer version, scale every time by the same factor and every speed (rad/s, units/s) by its inverse; keep the code scroll cap, cursor blink and star twinkle in real time.
- The loop seam applies to the render area only. At the loop point the counters, the clock and the code panel jump back to their start; that is expected.

## How to work
1. First show me the storyboard below as a table (scenes, times, motion, colours, climax) and wait for my OK or changes.
2. Write the script. Render still frames at the middle of every scene and look at them yourself: check that nothing important is cut off or hidden under the status block, the climax reads clearly against the scenes before it (by contrast, as the storyboard describes; a flash of 1-2 frames elsewhere may be brighter), and the loop seam is clean. If the storyboard says something is intended (e.g. dust running past the edge for a moment), keep it. Fix and repeat.
3. Render the full mp4 and tell me the file path and how long it took.
