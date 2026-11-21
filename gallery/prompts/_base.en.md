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

## How to work
1. First show me the storyboard below as a table (scenes, times, motion, colours, climax) and wait for my OK or changes.
2. Write the script. Render still frames at the middle of every scene and look at them yourself: check that nothing is cut off, nothing overlaps the status block, the climax is the brightest moment and the loop seam is clean. Fix and repeat.
3. Render the full mp4 and tell me the file path and how long it took.
