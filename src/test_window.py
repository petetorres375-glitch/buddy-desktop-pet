"""
Minimal test: transparent, always-on-top, borderless GTK3 window showing Buddy.

GTK3 is used instead of Tkinter because Tkinter on Linux only supports
whole-window alpha (makes Buddy translucent too), while GTK3 with an RGBA
visual gives us true per-pixel transparency — background invisible, Buddy solid.

Click anywhere on the window to close it.
"""

import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

from pathlib import Path
from PIL import Image
import io

SPRITE_PATH = Path(__file__).parent.parent / "assets" / "buddy_idle_cartoon.png"
SPRITE_HEIGHT = 160   # display height in pixels; original is 622px


def load_pixbuf(path: Path, height: int) -> GdkPixbuf.Pixbuf:
    """Load and resize the sprite PNG into a GdkPixbuf (GTK's image format)."""
    img = Image.open(path).convert("RGBA")
    ratio = height / img.height
    new_size = (int(img.width * ratio), height)
    img = img.resize(new_size, Image.LANCZOS)

    # Convert PIL image → bytes → GdkPixbuf
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(buf.read())
    loader.close()
    return loader.get_pixbuf()


class BuddyWindow(Gtk.Window):
    def __init__(self, pixbuf):
        super().__init__()
        self.pixbuf = pixbuf

        # --- Request RGBA visual (enables per-pixel transparency) ---
        screen = self.get_screen()
        rgba_visual = screen.get_rgba_visual()
        if rgba_visual:
            self.set_visual(rgba_visual)
            print("RGBA visual: YES — compositor transparency available")
        else:
            print("RGBA visual: NO — transparency may not work")

        # set_app_paintable tells GTK we'll draw the window ourselves
        # (otherwise GTK fills it with the theme background color)
        self.set_app_paintable(True)

        # --- Window flags ---
        self.set_decorated(False)      # no title bar or borders
        self.set_keep_above(True)      # always on top
        self.set_resizable(False)

        # Size the window exactly to the sprite
        w, h = pixbuf.get_width(), pixbuf.get_height()
        self.set_default_size(w, h)

        # Position: top-right corner with small margin
        screen_w = screen.get_width()
        self.move(screen_w - w - 20, 40)

        # --- Drawing ---
        # We use a DrawingArea so we control exactly what gets painted
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(w, h)
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)

        # --- Input ---
        self.connect("button-press-event", lambda *_: Gtk.main_quit())
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self.connect("destroy", Gtk.main_quit)

    def on_draw(self, widget, cr):
        """Cairo draw callback — called every time GTK needs to repaint."""
        # Clear to fully transparent (alpha=0) — this is what makes the
        # background invisible instead of a solid color.
        cr.set_operator(0)  # cairo.OPERATOR_CLEAR
        cr.paint()

        # Draw the sprite with its own alpha channel intact
        cr.set_operator(2)  # cairo.OPERATOR_OVER (normal compositing)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()


pixbuf = load_pixbuf(SPRITE_PATH, SPRITE_HEIGHT)
print(f"Sprite loaded: {pixbuf.get_width()}x{pixbuf.get_height()}px")
print("Buddy should appear in the top-right corner.")
print("Click him to close.")
print("RESULT: if background is see-through (not black), transparency works!")

win = BuddyWindow(pixbuf)
win.show_all()
Gtk.main()
