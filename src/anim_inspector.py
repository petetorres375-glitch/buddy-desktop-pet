import pygame
import sys
import os

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

FRAME_WIDTH = 180   # must match slice_sprites.py CELL_SIZE
FRAME_HEIGHT = 180
SCALE_FACTOR = 1.5

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Buddy Pet Animation & Sound Inspector")
clock = pygame.time.Clock()


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            print(f"Unable to load spritesheet: {filename}", file=sys.stderr)
            raise SystemExit(e)

    def get_image(self, col, row, width, height, scale=1.0):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (col * width, row * height, width, height))
        if scale != 1.0:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        return image


ASSET_DIR = "/home/lenovo-home/buddy_pet/assets/"
IMAGE_PATH = os.path.join(ASSET_DIR, "cat_sheet.png")

# Row indices match slice_sprites.py ANIM_ORDER:
# idle=0, walk=1, sleep=2, jump=3, sit=4, play=5, meow=6, stretch=7
animations = {
    "idle":    [(0, 0), (1, 0), (2, 0), (3, 0)],
    "walk":    [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1)],
    "sleep":   [(0, 2), (1, 2), (2, 2), (3, 2)],
    "sit":     [(0, 4), (1, 4), (2, 4), (3, 4)],
    "meow":    [(0, 6), (1, 6)],
    "stretch": [(0, 7), (1, 7), (2, 7)],
}

purr_sound = None
meow_sound = None

try:
    purr_sound = pygame.mixer.Sound(os.path.join(ASSET_DIR, "purr.mp3"))
    purr_sound.set_volume(0.4)
except pygame.error:
    print("[WARNING] purr.mp3 not found — running silent.")

try:
    meow_sound = pygame.mixer.Sound(os.path.join(ASSET_DIR, "meow.mp3"))
    meow_sound.set_volume(0.6)
except pygame.error:
    print("[WARNING] meow.mp3 not found — running silent.")

try:
    cat_sheet = SpriteSheet(IMAGE_PATH)
except SystemExit:
    print("[WARNING] cat_sheet.png not found — using placeholder colors.")
    cat_sheet = None


def load_frames(action):
    if not cat_sheet:
        dummy = pygame.Surface((FRAME_WIDTH, FRAME_HEIGHT))
        dummy.fill((230, 126, 34))
        return [dummy]
    return [cat_sheet.get_image(col, row, FRAME_WIDTH, FRAME_HEIGHT, SCALE_FACTOR)
            for col, row in animations[action]]


def handle_sounds(action):
    pygame.mixer.stop()
    if action in ("idle", "sleep", "sit") and purr_sound:
        purr_sound.play(loops=-1)
    elif action == "meow" and meow_sound:
        meow_sound.play()


ANIM_KEYS = list(animations.keys())
current_idx = 0
current_action = ANIM_KEYS[current_idx]
frame_list = load_frames(current_action)
handle_sounds(current_action)

frame_index = 0
anim_timer = 0
ANIM_SPEED = 150  # ms per frame

running = True
while running:
    dt = clock.tick(FPS)
    anim_timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                current_idx = (current_idx + 1) % len(ANIM_KEYS)
            elif event.key == pygame.K_LEFT:
                current_idx = (current_idx - 1) % len(ANIM_KEYS)
            elif event.key == pygame.K_UP:
                ANIM_SPEED = max(50, ANIM_SPEED - 25)
            elif event.key == pygame.K_DOWN:
                ANIM_SPEED = min(500, ANIM_SPEED + 25)
            elif event.key == pygame.K_ESCAPE:
                running = False

            new_action = ANIM_KEYS[current_idx]
            if new_action != current_action:
                current_action = new_action
                frame_list = load_frames(current_action)
                frame_index = 0
                anim_timer = 0
                handle_sounds(current_action)

    if anim_timer >= ANIM_SPEED:
        anim_timer = 0
        frame_index = (frame_index + 1) % len(frame_list)

    screen.fill((40, 44, 52))

    font = pygame.font.SysFont(None, 26)
    screen.blit(font.render("← → cycle animations  |  ↑ ↓ speed  |  ESC quit", True, (200, 200, 200)), (20, 18))
    screen.blit(font.render(f"Animation: {current_action.upper()}  |  frame {frame_index+1}/{len(frame_list)}  |  {ANIM_SPEED}ms/frame", True, (46, 204, 113)), (20, 48))

    sprite = frame_list[frame_index]
    rect = sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(sprite, rect.topleft)

    pygame.display.flip()

pygame.quit()
