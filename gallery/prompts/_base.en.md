You are going to make a short vertical ASCII-art reel with a single Python script.

## Output
- One file `<slug>.py` that renders `<slug>.mp4`: 1080x1920, 30 fps, H.264, yuv420p, no audio, at most 15 seconds.
- Use only Python 3, numpy, Pillow and ffmpeg (pipe raw RGB frames into ffmpeg). Install what is missing.
- Every frame must be a pure function of the time `t` (no state carried between frames), so any single frame can be rendered on its own for checking.

## Screen layout
- Top 1098 px: the render. A grid of 108 x 61 character cells, each cell 10 x 18 px. Black background.
- Bottom-left of the render: a status block in a monospace font, 3 lines. Line 1 is the handle (use `@your.handle` unless I give one), lines 2-3 are 2-4 counters that climb as the story progresses, plus `letters N` (cells drawn this frame).
- Top-right of the render: a pink dot and the clock, e.g. `● t 3.27s`.
- Below the render: a code panel that shows this very script. A header bar with the file name on the left and a green dot `running · 30 fps` on the right. Syntax-coloured code (dark theme) with line numbers, scrolling down smoothly at no more than 6 lines per second, one highlighted line with a blinking pink block cursor at its end, as if it is being typed right now.

## How the render works
- Glyph atlas: draw every glyph you use (space, `.,:;*+'|-/\_~=#@%&o0O`, A-Z, a-z, 0-9, `$!?<>{}[]()^`) once into a 10 x 18 bitmap with a bold monospace font (e.g. DejaVu Sans Mono Bold, size 15).
- Brightness ramp: sort glyphs by ink coverage and pick about 28 evenly spaced ones. A cell's brightness (0-1) picks its glyph from this ramp.
- Each cell holds one glyph index and one RGB colour (may exceed 1 for highlights). Composite: glyph bitmap x colour, then a bloom pass (downscale 4x, Gaussian blur, upscale, add ~0.9x) for a soft glow.
- Brighter wins: a cell is only overwritten by something brighter. Fading objects reveal the background instead of leaving black holes.
- 3D objects are point clouds: sample thousands of surface points (with normals), rotate them, perspective-project to cells, keep the nearest point per cell (z-buffer), and shade with a key light, a moving rim light and occasional specular glints.
- Thin lines (rays, tentacles, stems) use direction glyphs `| / \ -` matching the screen direction of the line.
- Background layers: faint twinkling stars or a dim letter rain, so the screen is never dead.

## Story rules
- Something moves in the first second (the hook). The full form is revealed at 55-70 % of the length. One climax, clearly stronger than everything before it. The last 1.5 s fades back to the opening frame so the reel loops seamlessly.
- Put all scene times as `T_*` constants at the top of the script: that block reads as a timeline in the code panel.
- Comments in English, lines under 72 characters (they are on screen).

## Reference numbers (aim for a similar look, not pixel-exact)
- Coordinates: screen `X` runs -1..1 across the width (0 = centre), `Y` runs 0 (top) .. 1 (bottom of the render). 3D model units: 1 = half the screen width, y points down, z points toward the viewer.
- Projection: `k = f / (f - z)` with `f = 3.2`; screen `X = x*k*scale`, `Y = cy + y*k*scale*540/1098` (so x and y share one unit).
- Point colour = `rgb * (0.35 + 0.9 * brightness)`. Lighting: key light from upper front `(0, -0.8, 0.6)`, rim light circling at 0.9 rad/s weighted by `(1 - |n.z|)^1.5`, specular exponent 12.
- Bloom: downscale to 1/4, Gaussian blur radius 3, upscale bilinear, add x0.9-1.1.
- Status block: regular monospace 30 px, colour #e8eaee, 40 px line spacing, 22 px from the left, bottom line 22 px above the code panel. Clock: same font, pink #ff6b9e, top-right, about 37 px from the top.
- Code panel: header bar 62 px, #1e2026, file name 26 px. Code: regular monospace 24 px, line height 36 px, line numbers 20 px #4e5460 in a 64 px gutter, background #16181d. Colours: keywords #c678dd, functions #61afef, strings #98c379, numbers #d19a66, comments #6a737d, UPPER_CASE constants #56b6c2, other text #dcdfe4. The highlighted line sits 6 lines below the top of the panel, background lifted by about +0.06; the cursor is a 13 px pink block blinking at 2.5 Hz.
- Big caption (only if the storyboard has text): bold monospace 46 px, letter spacing +35 %, centred.
- Encoding: `ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart`.

## How to work
1. First show me the storyboard below as a table (scenes, times, motion, colours, climax) and wait for my OK or changes.
2. Write the script. Render still frames at the middle of every scene and look at them yourself: check that nothing is cut off, nothing overlaps the status block, the climax is the brightest moment and the loop seam is clean. Fix and repeat.
3. Render the full mp4 and tell me the file path and how long it took.
