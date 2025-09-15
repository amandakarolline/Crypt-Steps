import math
import random
from pygame import Rect

TITLE = "Crypt Steps"
WIDTH = 800
HEIGHT = 600


STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_GAME_OVER = "game_over"


MUSIC_TRACK = "mystic_loop"
SND_STEP = "step"
SND_HURT = "hurt"
SND_WIN = "win"

TILE = 40
GRID_W = WIDTH // TILE
GRID_H = HEIGHT // TILE

C_BG = (18, 20, 30)
C_WALL = (58, 62, 80)
C_FLOOR = (32, 36, 48)
C_TEXT = (230, 235, 245)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def play_sound_safe(name):
    try:
        if audio_enabled:
            sounds.__getattr__(name).play()
    except Exception:
        pass


def ensure_music():
    try:
        if music_enabled:
            if not music.is_playing(MUSIC_TRACK):
                music.set_volume(0.5)
                music.play(MUSIC_TRACK)
        else:
            music.stop()
    except Exception:
        pass


T_WALL = 1
T_FLOOR = 0


def make_map():
    grid = [[T_WALL for _ in range(GRID_W)] for _ in range(GRID_H)]

    def carve_room(cx, cy, rw, rh):
        for y in range(cy - rh, cy + rh + 1):
            for x in range(cx - rw, cx + rw + 1):
                if 1 <= x < GRID_W - 1 and 1 <= y < GRID_H - 1:
                    grid[y][x] = T_FLOOR

    carve_room(GRID_W // 2, GRID_H // 2, 4, 3)
    for _ in range(8):
        cx = random.randint(2, GRID_W - 3)
        cy = random.randint(2, GRID_H - 3)
        carve_room(cx, cy, random.randint(2, 4), random.randint(2, 3))

    for _ in range(30):
        x = random.randint(2, GRID_W - 3)
        y = random.randint(2, GRID_H - 3)
        length = random.randint(3, 8)
        horizontal = random.choice([True, False])
        for i in range(length):
            xi = clamp(x + (i if horizontal else 0), 1, GRID_W - 2)
            yi = clamp(y + (0 if horizontal else i), 1, GRID_H - 2)
            grid[yi][xi] = T_FLOOR

    return grid


class AnimatedSprite:
    def __init__(self, gx, gy, base_color, idle_frames, move_frames,
                 idle_fps=5, move_fps=10):
        self.gx = gx
        self.gy = gy
        self.base_color = base_color
        self.idle_frames = idle_frames
        self.move_frames = move_frames
        self.idle_fps = idle_fps
        self.move_fps = move_fps
        self.frame_time = 0.0
        self.frame_index = 0
        self.state = "idle"
        self.facing = (1, 0)
        self.hit_flash = 0.0

    @property
    def rect(self):
        return Rect(self.gx * TILE, self.gy * TILE, TILE, TILE)

    def set_state(self, s):
        if self.state != s:
            self.state = s
            self.frame_time = 0.0
            self.frame_index = 0

    def current_frames(self):
        return self.move_frames if self.state == "move" else self.idle_frames

    def current_fps(self):
        return self.move_fps if self.state == "move" else self.idle_fps

    def update_anim(self, dt):
        frames = self.current_frames()
        if not frames:
            return
        self.frame_time += dt
        if self.frame_time >= 1.0 / self.current_fps():
            self.frame_time = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)
        if self.hit_flash > 0.0:
            self.hit_flash -= dt

    def draw(self):
        x = self.gx * TILE
        y = self.gy * TILE
        frames = self.current_frames()
        if frames:
            w, h, nudge = frames[self.frame_index]
        else:
            w, h, nudge = (TILE - 8, TILE - 8, 0)
        w = clamp(w, 10, TILE - 4)
        h = clamp(h, 10, TILE - 4)
        cx = x + (TILE - w) // 2
        cy = y + (TILE - h) // 2 + nudge
        col = self.base_color
        if self.hit_flash > 0.0 and int(self.hit_flash * 20) % 2 == 0:
            col = (255, 255, 255)
        body = Rect(cx, cy, w, h)
        screen.draw.filled_rect(body, col)
        screen.draw.rect(body, (15, 15, 18))
        ex = body.centerx + (6 if self.facing[0] >= 0 else -6)
        ey = body.centery - 6
        screen.draw.filled_rect(Rect(ex, ey, 4, 4), (10, 10, 10))


class Hero(AnimatedSprite):
    def __init__(self, gx, gy):
        idle = [(TILE - 10, TILE - 12, 0), (TILE - 12, TILE - 10, -1)]
        move = [(TILE - 14, TILE - 14, 0), (TILE - 16, TILE - 12, 1),
                (TILE - 14, TILE - 14, 0), (TILE - 12, TILE - 16, -1)]
        super().__init__(gx, gy, (90, 180, 255), idle, move,
                         idle_fps=3, move_fps=8)
        self.hp = 3

    def try_move(self, dx, dy, grid, enemies):
        nx, ny = self.gx + dx, self.gy + dy
        self.facing = (dx, dy)
        if not is_blocked(grid, nx, ny) and
        not any(e.gx == nx ande.gy == ny for e in enemies):
            self.gx, self.gy = nx, ny
            self.set_state("move")
            play_sound_safe(SND_STEP)
            return True
        self.set_state("idle")
        return False

    def hurt(self):
        self.hp -= 1
        self.hit_flash = 0.6
        play_sound_safe(SND_HURT)


class Enemy(AnimatedSprite):
    def __init__(self, gx, gy, patrol_cells, palette=(235, 100, 120)):
        idle = [(TILE - 12, TILE - 12, 0), (TILE - 14, TILE - 10, -1)]
        move = [(TILE - 16, TILE - 16, 0), (TILE - 18, TILE - 14, 1),
                (TILE - 16, TILE - 16, 0), (TILE - 14, TILE - 18, -1)]
        super().__init__(gx, gy, palette, idle, move, idle_fps=3, move_fps=6)
        self.patrol = patrol_cells[:]
        self.patrol_i = 0

    def ai_step(self, grid, hero_pos, occupied):
        tx, ty = self.patrol[self.patrol_i]
        dx = clamp(tx - self.gx, -1, 1)
        dy = clamp(ty - self.gy, -1, 1)
        if dx == 0 and dy == 0:
            self.patrol_i = (self.patrol_i + 1) % len(self.patrol)
            tx, ty = self.patrol[self.patrol_i]
            dx = clamp(tx - self.gx, -1, 1)
            dy = clamp(ty - self.gy, -1, 1)
        nx, ny = self.gx + dx, self.gy + dy
        self.facing = (dx, dy)
        self.set_state("move" if (dx or dy) else "idle")
        if not is_blocked(grid, nx, ny) and (nx, ny) not in occupied:
            self.gx, self.gy = nx, ny


def is_blocked(grid, gx, gy):
    if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
        return True
    return grid[gy][gx] == T_WALL


def draw_map(grid):
    for y in range(GRID_H):
        for x in range(GRID_W):
            r = Rect(x * TILE, y * TILE, TILE, TILE)
            if grid[y][x] == T_WALL:
                screen.draw.filled_rect(r, C_WALL)
            else:
                screen.draw.filled_rect(r, C_FLOOR)


state = STATE_MENU
music_enabled = True
audio_enabled = True

grid = make_map()
hero = Hero(GRID_W // 2, GRID_H // 2)


def random_floor_cell(g):
    while True:
        x = random.randint(1, GRID_W - 2)
        y = random.randint(1, GRID_H - 2)
        if g[y][x] == T_FLOOR:
            return x, y


def make_patrol_area(cx, cy, w=4, h=3):
    cells = []
    for y in range(cy - h, cy + h + 1):
        for x in range(cx - w, cx + w + 1):
            if 0 < x < GRID_W - 1 and 0 < y < GRID_H - 1:
                cells.append((x, y))
    random.shuffle(cells)
    return cells[:8] if len(cells) >= 8 else cells


def spawn_enemies(g, n=5):
    es = []
    for _ in range(n):
        x, y = random_floor_cell(g)
        patrol = make_patrol_area(x, y, w=random.randint(2, 4),
                                  h=random.randint(1, 3))
        es.append(Enemy(x, y, patrol,
                  palette=(230, random.randint(80, 160), 110)))
    return es


enemies = spawn_enemies(grid, n=6)
turn_locked = False


goal_gx, goal_gy = random_floor_cell(grid)


class UIButton:
    def __init__(self, rect, label, on_click):
        self.rect = Rect(rect)
        self.label = label
        self.on_click = on_click
        self.hovered = False

    def draw(self):
        col = (245, 245, 245) if self.hovered else (220, 220, 220)
        screen.draw.filled_rect(self.rect, col)
        screen.draw.rect(self.rect, (24, 24, 28))
        screen.draw.text(self.label, center=self.rect.center,
                         fontsize=36, color=(20, 20, 24))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.on_click()


menu_buttons = []


def build_menu():
    menu_buttons.clear()
    cx = WIDTH // 2
    top = 240
    gap = 70
    menu_buttons.append(
                        UIButton(
                                 Rect(cx - 160, top, 320, 56),
                                      "Start Game", start_game))
    menu_buttons.append(UIButton(Rect(cx - 160, top + gap, 320, 56),
                                      "Music & SFX On/Off", toggle_audio))
    menu_buttons.append(UIButton(Rect(cx - 160, top + 2 * gap, 320, 56), "Exit", exit_game))


def start_game():
    global state, grid, hero, enemies, goal_gx, goal_gy
    grid = make_map()
    hero = Hero(*random_floor_cell(grid))
    enemies = spawn_enemies(grid, n=6)
    goal_gx, goal_gy = random_floor_cell(grid)
    state = STATE_PLAY
    ensure_music()


def toggle_audio():
    global music_enabled, audio_enabled
    music_enabled = not music_enabled
    audio_enabled = music_enabled
    ensure_music()


def exit_game():
    raise SystemExit


build_menu()


def on_mouse_move(pos):
    if state == STATE_MENU:
        for b in menu_buttons:
            b.update_hover(pos)


def on_mouse_down(pos, button):
    if state == STATE_MENU:
        for b in menu_buttons:
            b.click(pos)


def on_key_down(key):
    global turn_locked, state
    if state == STATE_MENU:
        return
    if state == STATE_GAME_OVER:
        if key == keys.ESCAPE:
            state = STATE_MENU
        return
    if turn_locked:
        return

    dx, dy = 0, 0
    if key in (keys.LEFT, keys.A):
        dx = -1
    elif key in (keys.RIGHT, keys.D):
        dx = 1
    elif key in (keys.UP, keys.W):
        dy = -1
    elif key in (keys.DOWN, keys.S):
        dy = 1
    elif key == keys.ESCAPE:
        state = STATE_MENU
        ensure_music()
        return

    if dx or dy:
        if hero.try_move(dx, dy, grid, enemies):
            enemy_turn()
            check_end_states()
            turn_locked = True


def on_key_up(key):
    global turn_locked
    turn_locked = False


def enemy_turn():
    occupied = {(e.gx, e.gy) for e in enemies}
    occupied.add((hero.gx, hero.gy))
    for e in enemies:
        occupied.discard((e.gx, e.gy))
        e.ai_step(grid, (hero.gx, hero.gy), occupied)
        occupied.add((e.gx, e.gy))
    for e in enemies:
        if e.gx == hero.gx and e.gy == hero.gy:
            hero.hurt()


def check_end_states():
    global state
    if hero.hp <= 0:
        state = STATE_GAME_OVER
    if hero.gx == goal_gx and hero.gy == goal_gy:
        play_sound_safe(SND_WIN)
        state = STATE_GAME_OVER


def update(dt):
    if state == STATE_PLAY:
        hero.update_anim(dt)
        for e in enemies:
            e.update_anim(dt)


def draw_grid_overlay():
    for x in range(GRID_W + 1):
        screen.draw.line((x * TILE, 0), (x * TILE, HEIGHT), (22, 24, 30))
    for y in range(GRID_H + 1):
        screen.draw.line((0, y * TILE), (WIDTH, y * TILE), (22, 24, 30))


def draw_menu():
    screen.fill(C_BG)
    screen.draw.text("CRYPТ STEPS", center=(WIDTH // 2, 120), fontsize=72, color=C_TEXT)
    for b in menu_buttons:
        b.draw()
    hint = f"Audio: {'ON' if music_enabled else 'OFF'}"
    screen.draw.text(hint, (20, HEIGHT - 40), fontsize=28, color=C_TEXT)


def draw_play():
    screen.fill(C_BG)
    draw_map(grid)
    g_rect = Rect(goal_gx * TILE + 8, goal_gy * TILE + 8, TILE - 16, TILE - 16)
    screen.draw.filled_rect(g_rect, (220, 210, 80))
    screen.draw.rect(g_rect, (40, 40, 20))

    for e in enemies:
        e.draw()
    hero.draw()

    screen.draw.text(f"HP: {hero.hp}", (12, 10), fontsize=32, color=C_TEXT)
    screen.draw.text("Arrows/WASD to move, ESC for menu", (12, 48), fontsize=24, color=C_TEXT)

    draw_grid_overlay()


def draw_game_over():
    draw_play()
    screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0))
    screen.surface.set_alpha(None)
    msg = "YOU WIN!" if (hero.gx == goal_gx and hero.gy == goal_gy and hero.hp > 0) else "GAME OVER"
    screen.draw.text(msg, center=(WIDTH // 2, HEIGHT // 2 - 20), fontsize=72, color=(250, 240, 240))
    screen.draw.text("Press ESC to return to Menu", center=(WIDTH // 2, HEIGHT // 2 + 40), fontsize=36, color=C_TEXT)


def draw():
    if state == STATE_MENU:
        draw_menu()
    elif state == STATE_PLAY:
        draw_play()
    elif state == STATE_GAME_OVER:
        draw_game_over()


music_enabled = True
audio_enabled = True
ensure_music()
