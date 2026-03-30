import pygame  # type: ignore
import json
import math
import os
from datetime import datetime

from sim.draw import draw
from sim.entities import Car, Pedestrian

pygame.init()

# ----------------------------
# Constants / Globals
# ----------------------------
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)

entities = []
current_speed = 0
current_heading = 0
mode = "car"  # "car" or "pedestrian"


# ----------------------------
# Scenario Saving
# ----------------------------
def save_scenario():
    """Save the current entities into a JSON scenario file."""
    os.makedirs("scenarios", exist_ok=True)

    name = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"scenarios/scenario_{name}.json"

    # Convert objects to dicts for saving
    out = []
    for e in entities:
        data = {
            "type": e.type,
            "x": e.x,
            "y": e.y,
            "vx": getattr(e, "vx", e.get_velocity()[0]),
            "vy": getattr(e, "vy", e.get_velocity()[1]),
            "heading": getattr(e, "heading", 0),
            "mass": getattr(e, "mass", 1),
        }
        out.append(data)

    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved:", path)


# ----------------------------
# Text Rendering
# ----------------------------
def draw_text(text, x, y):
    """Render text on the screen at (x,y)."""
    img = font.render(text, True, (255, 255, 255))
    screen.blit(img, (x, y))


# ----------------------------
# Entity Creation
# ----------------------------
def create_car(x, y):
    """Create a Car object at position (x, y) with current speed and heading."""
    data = {
        "type": "car",
        "x": x,
        "y": y,
        "vx": math.cos(current_heading) * current_speed,
        "vy": math.sin(current_heading) * current_speed,
        "heading": current_heading,
        "mass": 1500,
    }
    return Car(data)


def create_ped(x, y):
    """Create a Pedestrian object at position (x, y) with current speed and heading."""
    data = {
        "type": "pedestrian",
        "x": x,
        "y": y,
        "vx": math.cos(current_heading) * current_speed,
        "vy": math.sin(current_heading) * current_speed,
        "mass": 80,
    }
    return Pedestrian(data)


# ----------------------------
# Input Handling
# ----------------------------
def handle_events():
    """Process user inputs (keyboard/mouse)."""
    global running, mode, current_speed, current_heading

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_TAB:
                mode = "pedestrian" if mode == "car" else "car"
            elif event.key == pygame.K_BACKQUOTE:
                save_scenario()
            elif event.key == pygame.K_c:
                entities.clear()
            elif event.key == pygame.K_DELETE and entities:
                entities.pop()
            elif event.key == pygame.K_r:
                current_speed = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if mode == "car":
                entities.append(create_car(x, y))
            else:
                entities.append(create_ped(x, y))

    # Continuous key press handling for speed/heading
    keys = pygame.key.get_pressed()
    if keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS] or keys[pygame.K_EQUALS]: current_speed += 1
    if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]: current_speed -= 1
    if keys[pygame.K_w]: current_speed += 0.1
    if keys[pygame.K_s]: current_speed -= 0.1
    if keys[pygame.K_q]: current_heading -= 0.05
    if keys[pygame.K_e]: current_heading += 0.05
    if keys[pygame.K_a]: current_heading -= 0.01
    if keys[pygame.K_d]: current_heading += 0.01


# ----------------------------
# Preview / UI
# ----------------------------
def draw_preview():
    """Draw the mouse preview arrow for entity placement."""
    mx, my = pygame.mouse.get_pos()
    px = mx + math.cos(current_heading) * 40
    py = my + math.sin(current_heading) * 40
    pygame.draw.line(screen, (100, 200, 255), (mx, my), (px, py), 3)


def draw_ui():
    """Draw the editor-specific text overlay."""
    font_texts = [
        f"Mode: {mode}",
        f"Speed: {current_speed:.2f}m/s, ({current_speed*3.6:.1f} km/h)",
        f"Heading: {math.degrees(current_heading):.1f}",
        "Left click = place",
        "TAB = switch mode",
        "+/- = +/- 1 m/s (3.6 km/h) speed",
        "W/S = +/- 0.1 m/s (0.36 km/h) speed",
        "Q/E = 5 degree rotate",
        "A/D = 1 degree fine rotate",
        "` (Backquote) = save",
    ]
    for i, text in enumerate(font_texts):
        draw_text(text, 10, 10 + i*20)


# ----------------------------
# Main Loop
# ----------------------------
running = True
while running:
    handle_events()

    screen.fill((20, 20, 30))  # background

    # draw entities using centralized draw function
    draw(
        screen,
        entities,
        ego=None,
        mode="manual",
        font=font,
        episode_time=0.0,
        max_time=0.0,
        scenario_index=0,
        show_legend=False
    )

    draw_preview()
    draw_ui()

    pygame.display.flip()
    clock.tick(60)