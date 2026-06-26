"""
Buddy desktop pet — autonomous roaming cat.
Wanders, sits, stretches, meows, and sleeps in his bed.
Left-click: meow (or wake) | Right-click: quit
"""

import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import pygame.mixer
import math
import io
import random
from pathlib import Path
from PIL import Image

ASSETS     = Path(__file__).parent.parent / "assets"
FRAMES_DIR = ASSETS / "frames"

SPRITE_SIZE   = 150
BED_SIZE      = 130
BOWL_SIZE     = 80
SPEED         = 1.8          # slower walk → more cartoon-like
TICK_MS       = 30
ANIM_IDLE_MS  = 320          # idle breathing is lazier
ANIM_WALK_MS  = 130          # walk cycle slowed down
ANIM_SLOW_MS  = 500          # sleep/sit even more relaxed
ANIM_EAT_MS   = 220          # eat head-bob speed
BED_MARGIN_X  = 120   # from right edge
BED_MARGIN_Y  = 20    # from bottom edge
BOWL_MARGIN_Y = 20    # from bottom edge
EDGE_MARGIN   = 60
HOME_RADIUS   = 150   # Buddy stays within this many px of his bed
PURR_RADIUS   = 200   # mouse within this many px → Buddy purrs

DUR = {
    "idle":      (3000, 6000),
    "sit":       (2000, 5000),
    "sit_left":  (2000, 5000),
    "stretch":   (1500, 3000),
    "meow":      (700,  700),
    "jump":      (800,  800),
    "wander":    (1200, 2500),
    "play":      (2000, 4000),
    "nap":       (20000, 45000),
    "sleeping":  (30000, 60000),
    "eat":       (12000, 25000),
}

NEXT = {
    "idle":     ["idle", "sit", "sit_left", "stretch", "jump", "wander", "play", "nap", "to_bed", "to_bowl", "to_bowl"],
    "sit":      ["idle", "idle", "sit_left", "stretch", "wander", "play", "nap", "to_bowl"],
    "sit_left": ["idle", "idle", "sit", "stretch", "wander", "play", "nap", "to_bowl"],
    "stretch":  ["idle", "sit", "wander", "nap"],
    "meow":     ["idle"],
    "jump":     ["idle", "play"],
    "wander":   ["idle", "sit", "sit_left", "to_bowl"],
    "play":     ["idle", "sit", "jump"],
    "nap":      ["idle", "sit", "stretch"],
    "sleeping": ["idle"],
    "to_bed":   ["sleeping"],
    "to_bowl":  ["eat"],
    "eat":      ["idle", "wander", "sit"],
}


def load_pixbuf(path: Path, max_px: int) -> GdkPixbuf.Pixbuf:
    img = Image.open(path).convert("RGBA")
    ratio = max_px / max(img.width, img.height)
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(buf.read())
    loader.close()
    return loader.get_pixbuf()

def load_anim(name: str, n: int) -> list:
    return [load_pixbuf(FRAMES_DIR / f"{name}_{i}.png", SPRITE_SIZE) for i in range(n)]

ANIMS = {
    "idle":    load_anim("idle",    4),
    "walk":    load_anim("walk",    6),
    "sleep":   load_anim("sleep",   4),
    "sit":     load_anim("sit",     4),
    "meow":    load_anim("meow",    2),
    "stretch": load_anim("stretch", 3),
    "jump":    load_anim("jump",    4),
    "play":    load_anim("play",    3),
    "eat":     load_anim("eat",     4),   # dedicated eating frames
}
ANIMS["walk_left"] = [pb.flip(True) for pb in ANIMS["walk"]]
ANIMS["sit_left"]  = [pb.flip(True) for pb in ANIMS["sit"]]
ANIMS["play_left"] = [pb.flip(True) for pb in ANIMS["play"]]
ANIMS["eat_left"]  = [pb.flip(True) for pb in ANIMS["eat"]]

pygame.mixer.init()
purr_sound = meow_sound = None
try:
    purr_sound = pygame.mixer.Sound(str(ASSETS / "purr.mp3"))
    purr_sound.set_volume(0.35)
except Exception: pass
try:
    meow_sound = pygame.mixer.Sound(str(ASSETS / "meow.mp3"))
    meow_sound.set_volume(0.7)
except Exception: pass

def start_purr():
    if purr_sound and not pygame.mixer.get_busy():
        purr_sound.play(loops=-1)

def stop_purr():
    if purr_sound: purr_sound.stop()

def purr_for(ms: int):
    """Play purr for ms milliseconds then stop."""
    start_purr()
    GLib.timeout_add(ms, lambda: (stop_purr(), False)[1])

def play_meow():
    stop_purr()
    if meow_sound: meow_sound.play()
    GLib.timeout_add(1200, lambda: (stop_purr(), False)[1])


class BedWindow(Gtk.Window):
    def __init__(self, mon_x: int, mon_y: int, mon_w: int, mon_h: int):
        super().__init__()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual: self.set_visual(visual)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_resizable(False)
        pb = load_pixbuf(ASSETS / "bed.png", BED_SIZE)
        w, h = pb.get_width(), pb.get_height()
        bx = mon_x + mon_w - BED_MARGIN_X - w
        by = mon_y + mon_h - BED_MARGIN_Y - h
        self.bed_cx = float(bx + w // 2)
        self.bed_cy = float(by + h // 2)
        self.set_default_size(w, h)
        self.move(bx, by)
        self._pb = pb
        da = Gtk.DrawingArea()
        da.set_size_request(w, h)
        da.connect("draw", self._draw)
        self.add(da)

    def _draw(self, widget, cr):
        cr.set_operator(0); cr.paint()
        cr.set_operator(2)
        Gdk.cairo_set_source_pixbuf(cr, self._pb, 0, 0)
        cr.paint()


class BowlWindow(Gtk.Window):
    def __init__(self, mon_x: int, mon_y: int, mon_w: int, mon_h: int):
        super().__init__()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual: self.set_visual(visual)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_resizable(False)
        pb = load_pixbuf(ASSETS / "bowl.png", BOWL_SIZE)
        w, h = pb.get_width(), pb.get_height()
        # Bowl sits in front of (left of) the bed, aligned to same bottom edge
        bx = mon_x + mon_w - BED_MARGIN_X - w - 10
        by = mon_y + mon_h - BOWL_MARGIN_Y - h
        self.bowl_cx = float(bx + w // 2)
        self.bowl_cy = float(by + h // 2)
        self.set_default_size(w, h)
        self.move(bx, by)
        self._pb = pb
        da = Gtk.DrawingArea()
        da.set_size_request(w, h)
        da.connect("draw", self._draw)
        self.add(da)

    def _draw(self, widget, cr):
        cr.set_operator(0); cr.paint()
        cr.set_operator(2)
        Gdk.cairo_set_source_pixbuf(cr, self._pb, 0, 0)
        cr.paint()


class BuddyWindow(Gtk.Window):
    def __init__(self, bed: BedWindow, bowl: BowlWindow, mon_x: int, mon_y: int, mon_w: int, mon_h: int):
        super().__init__()
        self.bed      = bed
        self.bowl     = bowl
        self.mon_x    = mon_x
        self.mon_y    = mon_y
        self.screen_w = mon_w
        self.screen_h = mon_h

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual: self.set_visual(visual)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_resizable(False)

        # start near the bed
        self.cat_x = float(bed.bed_cx - 60)
        self.cat_y = float(bed.bed_cy - 60)

        self.anim_frame   = 0
        self.anim_ms      = 0
        self.facing_right = True

        self.state        = "idle"
        self.state_ms     = 0
        self.state_dur    = self._random_dur("idle")
        self.walk_angle   = 0.0
        self.wander_tx    = self.cat_x
        self.wander_ty    = self.cat_y
        self.eat_bob_px   = 0

        self.win_w = SPRITE_SIZE + 20
        self.win_h = SPRITE_SIZE + 20
        self.set_default_size(self.win_w, self.win_h)
        self._reposition()

        da = Gtk.DrawingArea()
        da.set_size_request(self.win_w, self.win_h)
        da.connect("draw", self.on_draw)
        self.add(da)
        self.drawing_area = da

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._on_click)
        self.connect("destroy", Gtk.main_quit)

        start_purr()
        GLib.timeout_add(TICK_MS, self._tick)

    def _reposition(self):
        self.move(int(self.cat_x - self.win_w / 2),
                  int(self.cat_y - self.win_h / 2))

    @staticmethod
    def _random_dur(state: str) -> int:
        lo, hi = DUR.get(state, (2000, 4000))
        return random.randint(lo, hi)

    def _pick_next(self) -> str:
        return random.choice(NEXT.get(self.state, ["idle"]))

    def _enter(self, new_state: str):
        self.state      = new_state
        self.state_ms   = 0
        self.state_dur  = self._random_dur(new_state)
        self.anim_frame = 0
        self.anim_ms    = 0
        if new_state != "eat":
            self.eat_bob_px = 0

        if new_state in ("to_bed", "to_bowl"):
            self.state_dur = 999999
        elif new_state == "meow":
            play_meow()
        elif new_state == "wander":
            angle = random.uniform(0, 2 * math.pi)
            dist  = random.uniform(40, HOME_RADIUS)
            self.wander_tx = self.bed.bed_cx + math.cos(angle) * dist
            self.wander_ty = self.bed.bed_cy + math.sin(angle) * dist
        elif new_state == "play":
            self.facing_right = random.choice([True, False])

        elif new_state == "eat":
            self.facing_right = self.cat_x < self.bowl.bowl_cx

    def _walk_toward(self, tx: float, ty: float) -> float:
        dx, dy = tx - self.cat_x, ty - self.cat_y
        dist = math.hypot(dx, dy)
        if dist > 1:
            step = min(SPEED, dist)
            self.cat_x += (dx / dist) * step
            self.cat_y += (dy / dist) * step
            self.facing_right = dx > 0
            self._reposition()
        return dist

    def _bounce_angle(self):
        x_min = self.mon_x + EDGE_MARGIN
        x_max = self.mon_x + self.screen_w - EDGE_MARGIN
        y_min = self.mon_y + EDGE_MARGIN
        y_max = self.mon_y + self.screen_h - EDGE_MARGIN
        if self.cat_x < x_min or self.cat_x > x_max:
            self.walk_angle = math.pi - self.walk_angle
        if self.cat_y < y_min or self.cat_y > y_max:
            self.walk_angle = -self.walk_angle
        self.cat_x = max(x_min, min(x_max, self.cat_x))
        self.cat_y = max(y_min, min(y_max, self.cat_y))

    def _tick(self):
        self.state_ms += TICK_MS

        if self.state == "wander":
            if self._walk_toward(self.wander_tx, self.wander_ty) < 10:
                self._enter(self._pick_next())

        elif self.state == "to_bed":
            if self._walk_toward(self.bed.bed_cx, self.bed.bed_cy) < 45:
                self._enter("sleeping")

        elif self.state == "to_bowl":
            eat_x = self.bowl.bowl_cx
            eat_y = self.bowl.bowl_cy - 70

            if self._walk_toward(eat_x, eat_y) < 15:
                self._enter("eat")

        if self.state == "eat":
            # Slower, deeper bob — head dips down toward bowl every ~700ms
            phase = (self.state_ms % 700) / 700.0
            self.eat_bob_px = int(14 * max(0, math.sin(phase * math.pi)))

        if self.state_ms >= self.state_dur and self.state not in ("to_bed", "to_bowl"):
            self._enter(self._pick_next())

        ms_per_frame = {
            "wander":   ANIM_WALK_MS,
            "to_bed":   ANIM_WALK_MS,
            "to_bowl":  ANIM_WALK_MS,
            "jump":     150,
            "sleeping": ANIM_SLOW_MS,
            "nap":      ANIM_SLOW_MS,
            "sit":      ANIM_SLOW_MS,
            "sit_left": ANIM_SLOW_MS,
            "stretch":  ANIM_SLOW_MS,
            "play":     500,
            "eat":      ANIM_EAT_MS,
        }.get(self.state, ANIM_IDLE_MS)

        self.anim_ms += TICK_MS
        if self.anim_ms >= ms_per_frame:
            self.anim_ms = 0
            frames = self._current_frames()
            self.anim_frame = (self.anim_frame + 1) % len(frames)

        # purr when mouse is nearby (but not during meow/sleeping/nap)
        if self.state not in ("meow", "sleeping", "nap"):
            _win, mx, my, _ = Gdk.get_default_root_window().get_pointer()
            dist_to_mouse = math.hypot(mx - self.cat_x, my - self.cat_y)
            if dist_to_mouse < PURR_RADIUS:
                start_purr()
            else:
                stop_purr()

        self.drawing_area.queue_draw()
        if self.get_window():
            self.get_window().raise_()
        return True

    def _current_frames(self):
        if self.state in ("sleeping", "nap"): return ANIMS["sleep"]
        if self.state == "meow":     return ANIMS["meow"]
        if self.state == "sit":      return ANIMS["sit"]
        if self.state == "sit_left": return ANIMS["sit_left"]
        if self.state == "stretch":  return ANIMS["stretch"]
        if self.state == "jump":     return ANIMS["jump"]
        if self.state == "eat":
            return ANIMS["eat"] if self.facing_right else ANIMS["eat_left"]
        if self.state == "play":
            return ANIMS["play"]
        if self.state in ("wander", "to_bed", "to_bowl"):
            return ANIMS["walk"] if self.facing_right else ANIMS["walk_left"]
        return ANIMS["idle"]

    def on_draw(self, widget, cr):
        cr.set_operator(0); cr.paint()
        cr.set_operator(2)
        frames = self._current_frames()
        pb = frames[min(self.anim_frame, len(frames) - 1)]
        ox = (self.win_w - pb.get_width())  // 2
        oy = (self.win_h - pb.get_height()) // 2 + self.eat_bob_px
        Gdk.cairo_set_source_pixbuf(cr, pb, ox, oy)
        cr.paint()

    def _on_click(self, widget, event):
        if event.button == 1:
            if self.state in ("sleeping", "nap"):
                self._enter("idle")
            else:
                self._enter("meow")
        elif event.button == 3:
            Gtk.main_quit()


# Use primary monitor geometry so Buddy stays on one screen
display  = Gdk.Display.get_default()
monitor  = display.get_primary_monitor()
geom     = monitor.get_geometry()
mx, my   = geom.x, geom.y          # monitor top-left offset
mw, mh   = geom.width, geom.height  # monitor dimensions

bed   = BedWindow(mx, my, mw, mh)
bowl  = BowlWindow(mx, my, mw, mh)
buddy = BuddyWindow(bed, bowl, mx, my, mw, mh)

bed.show_all()
bowl.show_all()
buddy.show_all()

Gtk.main()
