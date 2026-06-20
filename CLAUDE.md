# Buddy Desktop Pet Project

A Windows-95-Neko-style desktop pet of Pedro's cat Buddy: chases the mouse
cursor around the screen in a transparent always-on-top window.

## Status (as of handoff from claude.ai chat)

DONE:
- `assets/buddy_original.jpg` - source photo of Buddy
- `assets/buddy_cropped.png` - background removed (GrabCut), tightly cropped, transparent PNG
- `assets/buddy_idle.png` - cropped + resized to 120px tall, real-photo style (not cartoon)
- `assets/buddy_idle_cartoon.png` - cartoon-stylized version (flat chibi style, bold edges,
  hue-classified colors: white fur / orange patches / dark brown shadow). THIS is the
  sprite to use for the actual pet - it's the final agreed style.
- `assets/meow.wav` - synthetic meow sound (numpy waveform synthesis, placeholder - may
  sound rough/kazoo-like, Pedro may want to swap for a real clip later)
- `assets/purr.wav` - synthetic purr sound (low rumble + 27Hz amplitude pulse, placeholder)
- `src/remove_background.py` - GrabCut-based background removal. NOTE: this needed a lot
  of manual region tuning specific to buddy_original.jpg's exact composition (door frame,
  hinge, wall, cabinet, floor all hardcoded by pixel coordinate at 600x800 working res).
  Won't generalize to a new photo without recalibrating those bg_region() calls.
- `src/crop_and_resize.py` - crops to content bounding box + resizes to sprite height
- `src/cartoonize_sprite.py` - cartoon stylization: edge detection (adaptiveThreshold) +
  direct hue/saturation classification into 3 known colors (white/orange/dark), NOT
  generic K-means (K-means and auto white-balance were tried and both produced wrong
  colors - muddy brown or cold blue - because the source photo has warm indoor lighting
  with white and orange fur sharing very similar hue, differing mainly in saturation).
- `src/cartoonize.py` - earlier/superseded full-photo cartoonizer (kept for reference,
  not used in final pipeline - cartoonize_sprite.py is the one that matters)
- `src/make_sounds.py` - generates meow.wav and purr.wav from scratch via numpy

NOT STARTED:
- Walk animation. We only have ONE pose (sitting/idle) since there's only one source
  photo. Decision pending: fake a walk cycle via code (squash/stretch/bob/tilt on the
  single sprite) vs. some other approach. Pedro chose code-only/automated asset pipeline
  throughout (no AI image generation available in the sandbox this was built in), so
  squash-stretch faking is the likely path - but Claude Code may have image-gen
  abilities/MCP tools that the original sandbox didn't, worth checking.
- Transparent always-on-top Tkinter window. UNTESTED on Pedro's actual Lenovo
  (Ubuntu 24.04, GNOME most likely). Real risk: GNOME/X11 transparency in Tkinter can
  render as solid black instead of see-through. Test this in isolation FIRST with a
  minimal window before building anything else on top of it.
- Global mouse position tracking (works even when window doesn't have focus) +
  movement-toward-cursor logic
- Animation state machine (idle / walk-N/S/E/W / scratch) swapping sprite frames
- Sound triggers: meow.wav on catching the cursor, purr.wav looping while walking
- Idle timeout, edge-of-screen "stuck" scratch behavior, stop-distance so the cat
  doesn't sit exactly on top of the cursor

## Key facts about Pedro / working style
- Self-directed Python learner, prefers one-step-at-a-time with explanation of new
  concepts (this project used OpenCV/Tkinter/audio synthesis, all newer territory
  for him vs. his Python fundamentals).
- Prefers complete file rewrites over surgical patches generally, but this project
  used iterative str_replace tuning out of necessity (image coordinate calibration).
- Cat's name: Buddy (real cat, one of Pedro's four: Rambo, Buddy, Teddy, Minnie).
- EPCC workflow (Explore, Plan, Code, Commit) is his standard approach for dev tasks.
- Main dev machine: Lenovo Ubuntu 24.04, user `lenovo-home`.

## Suggested next step
Test the transparent-window question on real hardware FIRST (cheap, 10-line script)
before investing more time in animation/sound wiring, since it's the biggest
unknown/risk in the whole project.
