import pygame  # type: ignore
import math
import os

# ==============================
# BACKGROUND CACHE
# ==============================
_background_cache = {}

def load_background(path):
    """
    Loads and caches a background image.
    """
    if not path:
        return None

    if path in _background_cache:
        return _background_cache[path]

    try:
        img = pygame.image.load(path).convert()
        _background_cache[path] = img
        return img
    except Exception as e:
        print(f"[draw.py] Failed to load background '{path}': {e}")
        return None


# ==============================
# TEXT DRAWING
# ==============================
def draw_text(screen, text, x, y, font, color=(255,255,255)):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


# ==============================
# CAMERA / WORLD HELPERS
# ==============================
def world_to_screen(wx, wy, cam_x, cam_y, screen_w, screen_h):
    """
    Converts world coordinates into screen coordinates
    with ego-centered camera.
    """
    sx = wx - cam_x + screen_w // 2
    sy = wy - cam_y + screen_h // 2
    return sx, sy


# ==============================
# MAIN DRAW FUNCTION
# ==============================
def draw(
    screen,
    entities,
    ego,
    roads=None,
    collision_log=None,
    background_image=None,
    mode="manual",
    font=None,
    episode_time=0.0,
    max_time=10.0,
    scenario_index=0,
    show_legend=True
):
    """
    Main renderer.
    """

    screen_w = screen.get_width()
    screen_h = screen.get_height()

    # ==============================
    # CAMERA POSITION
    # ==============================
    cam_x = ego.x if ego else 0
    cam_y = ego.y if ego else 0

    # ==============================
    # BACKGROUND
    # ==============================
    screen.fill((20, 20, 30))

    bg = load_background(background_image)

    if bg is not None:
        bg_w = bg.get_width()
        bg_h = bg.get_height()

        # center background on ego
        bg_x = screen_w // 2 - cam_x
        bg_y = screen_h // 2 - cam_y

        # tiled drawing
        start_x = int(bg_x // bg_w) * bg_w - bg_w
        start_y = int(bg_y // bg_h) * bg_h - bg_h

        for x in range(start_x, screen_w + bg_w, bg_w):
            for y in range(start_y, screen_h + bg_h, bg_h):
                screen.blit(bg, (x + bg_x % bg_w, y + bg_y % bg_h))

    # ==============================
    # ROADS
    # ==============================
    if roads:
        for road in roads:

            x = road.get("x", 0)
            y = road.get("y", 0)
            width = road.get("width", 100)
            height = road.get("height", 40)
            heading = road.get("heading", 0)

            sx, sy = world_to_screen(
                x, y,
                cam_x, cam_y,
                screen_w, screen_h
            )

            road_surface = pygame.Surface((width, height), pygame.SRCALPHA)

            # asphalt
            pygame.draw.rect(
                road_surface,
                (70, 70, 70),
                (0, 0, width, height)
            )

            # center dashed line
            for i in range(0, width, 40):
                pygame.draw.line(
                    road_surface,
                    (220, 220, 100),
                    (i, height // 2),
                    (i + 20, height // 2),
                    2
                )

            rotated = pygame.transform.rotate(
                road_surface,
                -math.degrees(heading)
            )

            rect = rotated.get_rect(center=(sx, sy))
            screen.blit(rotated, rect)

    # ==============================
    # ENTITIES
    # ==============================
    for e in entities:

        ex, ey = world_to_screen(
            e.x, e.y,
            cam_x, cam_y,
            screen_w, screen_h
        )

        # ==========================
        # PEDESTRIANS
        # ==========================
        if e.type == "pedestrian":

            pygame.draw.circle(
                screen,
                (0, 255, 0),
                (int(ex), int(ey)),
                8
            )

        # ==========================
        # CARS
        # ==========================
        elif e.type == "car":

            color = (80, 180, 255) if e == ego else (200, 50, 50)

            # collision circles
            for cx, cy, r in e.circles():

                scx, scy = world_to_screen(
                    cx, cy,
                    cam_x, cam_y,
                    screen_w, screen_h
                )

                pygame.draw.circle(
                    screen,
                    (255, 255, 0),
                    (int(scx), int(scy)),
                    int(r),
                    1
                )

            # body
            rect_length = 2 * e.front_offset
            rect_width = 2 * e.radius

            rect_surf = pygame.Surface(
                (rect_length, rect_width),
                pygame.SRCALPHA
            )

            pygame.draw.rect(
                rect_surf,
                color,
                (0, 0, rect_length, rect_width),
                4
            )

            rotated = pygame.transform.rotate(
                rect_surf,
                -math.degrees(e.heading)
            )

            r = rotated.get_rect(center=(ex, ey))
            screen.blit(rotated, r)

            # heading arrow
            hx = ex + math.cos(
                e.heading + getattr(e, 'steer', 0) * 0.5
            ) * 60

            hy = ey + math.sin(
                e.heading + getattr(e, 'steer', 0) * 0.5
            ) * 60

            pygame.draw.line(
                screen,
                (255, 255, 0),
                (ex, ey),
                (hx, hy),
                2
            )

    # ==============================
    # TOP UI
    # ==============================
    if font is not None and show_legend:

        draw_text(screen, f"Mode: {mode}", 10, 10, font)

        draw_text(
            screen,
            f"Scenario: {scenario_index + 1}",
            10,
            30,
            font
        )

        draw_text(
            screen,
            f"Time: {episode_time:.1f}s / {max_time}s",
            10,
            50,
            font
        )

        draw_text(
            screen,
            "TAB=switch mode | R=reset | N=next scenario",
            10,
            70,
            font
        )

        if ego is not None:

            speed = getattr(ego, 'speed', 0)

            # undo multiplier
            real_speed = speed / 10
            kmh = real_speed * 3.6

            draw_text(
                screen,
                f"Ego Speed: {real_speed:.2f} m/s ({kmh:.1f} km/h)",
                10,
                90,
                font
            )

            draw_text(
                screen,
                f"Ego Position: ({ego.x:.1f}, {ego.y:.1f})",
                10,
                110,
                font
            )

    # ==============================
    # COLLISION TELEMETRY PANEL
    # ==============================
    if collision_log and font:

        panel_height = 160

        panel = pygame.Surface(
            (screen_w, panel_height),
            pygame.SRCALPHA
        )

        panel.fill((0, 0, 0, 180))

        screen.blit(panel, (0, screen_h - panel_height))

        draw_text(
            screen,
            "Recent Collisions",
            10,
            screen_h - panel_height + 10,
            font,
            (255, 120, 120)
        )

        max_lines = 6

        recent = collision_log[-max_lines:]

        for i, c in enumerate(recent):

            a = c.get("a", "unknown")
            b = c.get("b", "unknown")

            impulse = c.get("impulse", 0)
            energy = c.get("energy", 0)

            rel_speed = c.get("relative_speed", 0)

            line = (
                f"{a} hit {b} | "
                f"Δv={rel_speed:.2f} m/s | "
                f"Impulse={impulse:.1f} Ns | "
                f"Energy={energy:.1f} J"
            )

            draw_text(
                screen,
                line,
                10,
                screen_h - panel_height + 40 + i * 18,
                font
            )