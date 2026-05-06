import pygame  # type: ignore
import json
import math
import os
import configparser
from datetime import datetime

from sim.draw import draw
from sim.entities import Car, Pedestrian

# Initialize pygame and load configuration
pygame.init()
config = configparser.ConfigParser()
config.read("config.ini")

# Width and height of the simulation window in pixels
WIDTH = config.getint("window", "width")
HEIGHT = config.getint("window", "height")

# Creation the main pygame window surface using WIDTH x HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Clock object used to control game frames
clock = pygame.time.Clock()

# Frames per second target (how smooth / fast simulation runs)
FPS = config.getint("window", "fps")

# Font used for UI rendering
# None means default system font
FONT_SIZE = config.getint("ui", "font_size")
uiFont = pygame.font.SysFont(None, FONT_SIZE)

# Global state variables
entities = []
selected_entity = None
dragging = False

# Current speed is measured in m/s (conversion to km/h = *3.6)
current_speed = 0
# Current heading is in radians, where 0 is to the right and increases counter-clockwise
current_heading = 0
# Mode set by default is a safe "car" mode for placing
mode = "car"

input_mode = None
input_buffer = ""

scenario_name = ""
scenario_description = ""

overwrite_prompt = False
pending_save_path = None
current_file = None

def main():
    # Main loop
    global running
    running = True
    while running:
        handle_events()

        draw(
            screen,
            entities,
            ego=None,
            mode="manual",
            font=uiFont,
            episode_time=0,
            max_time=0,
            scenario_index=0,
            show_legend=False
        )

        draw_selection()
        draw_preview()
        draw_ui()

        pygame.display.flip()
        clock.tick(60)

# ----------------------------
# Saving / Loading
# ----------------------------
def save_scenario():
    """Save scenario, with confirmation required if overwriting."""
    global overwrite_prompt, scenario_name

    os.makedirs("scenarios", exist_ok=True)

    if not scenario_name.strip():
        scenario_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"scenario_{scenario_name}.json"
    path = os.path.join("scenarios", filename)

    # Ask before overwrite
    if os.path.exists(path) and not overwrite_prompt:
        overwrite_prompt = True
        print("File exists. Press Y to overwrite or N to cancel.")
        return

    # Serialize entities
    out = []
    for e in entities:
        out.append({
            "type": e.type,
            "x": e.x,
            "y": e.y,
            "vx": getattr(e, "vx", e.get_velocity()[0]),
            "vy": getattr(e, "vy", e.get_velocity()[1]),
            "heading": getattr(e, "heading", 0),
            "mass": getattr(e, "mass", 1),
        })

    data = {
        "name": scenario_name,
        "description": scenario_description,
        "entities": out
    }

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
        json.dump(data, f, indent=2)

    overwrite_prompt = False
    print("Saved:", path)


def load_scenario_file(path):
    """Load scenario from file."""
    global entities, scenario_name, scenario_description

    with open(path) as f:
        data = json.load(f)

    entities.clear()

    if isinstance(data, dict):
        scenario_name = data.get("name", "")
        scenario_description = data.get("description", "")
        entities_data = data.get("entities", [])
    else:
        scenario_name = ""
        scenario_description = ""
        entities_data = data

    for e in entities_data:
        if e["type"] == "car":
            entities.append(Car(e))
        elif e["type"] == "pedestrian":
            entities.append(Pedestrian(e))

    print("Loaded:", path)


def load_latest_scenario():
    """Load most recent scenario."""
    if not os.path.exists("scenarios"):
        return

    files = [os.path.join("scenarios", f) for f in os.listdir("scenarios") if f.endswith(".json")]
    if not files:
        return

    latest = max(files, key=os.path.getmtime)
    load_scenario_file(latest)


# ----------------------------
# Entity helpers
# ----------------------------
def create_car(x, y):
    return Car({
        "type": "car",
        "x": x,
        "y": y,
        "vx": math.cos(current_heading) * current_speed,
        "vy": math.sin(current_heading) * current_speed,
        "heading": current_heading,
        "mass": 1500,
    })


def create_ped(x, y):
    return Pedestrian({
        "type": "pedestrian",
        "x": x,
        "y": y,
        "vx": math.cos(current_heading) * current_speed,
        "vy": math.sin(current_heading) * current_speed,
        "mass": 80,
    })


def find_nearest(x, y, radius=30):
    closest = None
    best = float("inf")

    for e in entities:
        d = math.hypot(e.x - x, e.y - y)
        if d < best and d < radius:
            best = d
            closest = e

    return closest


# ----------------------------
# Input
# ----------------------------
def handle_events():
    global running, mode, current_speed, current_heading
    global input_mode, input_buffer, scenario_name, scenario_description
    global selected_entity, dragging, overwrite_prompt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # KEYBOARD
        if event.type == pygame.KEYDOWN:
            # INPUT MODE
            if input_mode:

                if event.key == pygame.K_RETURN:
                    if input_mode == "name":
                        scenario_name = input_buffer.strip()
                    elif input_mode == "description":
                        scenario_description = input_buffer.strip()
                    input_mode = None

                elif event.key == pygame.K_BACKSPACE:
                    input_buffer = input_buffer[:-1]

                elif event.key == pygame.K_ESCAPE:
                    input_mode = None

                else:
                    if event.unicode:
                        input_buffer += event.unicode

                continue
                # prevents leaking into normal controls

            # NORMAL MODE
            match event.key:
                case pygame.K_ESCAPE:
                    running = False

                case pygame.K_TAB:
                    mode = "pedestrian" if mode == "car" else "car"

                case pygame.K_BACKQUOTE:
                    save_scenario()

                case pygame.K_l:
                    load_latest_scenario()

                case pygame.K_DELETE:
                    if selected_entity:
                        entities.remove(selected_entity)
                        selected_entity = None

                case pygame.K_c:
                    entities.clear()
                    selected_entity = None

                case pygame.K_r:
                    current_speed = 0

                case pygame.K_y:
                    if overwrite_prompt:
                        overwrite_prompt = False
                        save_scenario()

                case pygame.K_n:
                    if overwrite_prompt:
                        overwrite_prompt = False
                    input_mode = "name"
                    input_buffer = scenario_name

                case pygame.K_t:
                    input_mode = "description"
                    input_buffer = scenario_description

                case _:
                    pass

        # MOUSE
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_mode:
                # ignore clicks while typing
                continue  
            x, y = pygame.mouse.get_pos()

            # LEFT CLICK
            if event.button == 1:  
                clicked = find_nearest(x, y)

                if clicked:
                    selected_entity = clicked
                    dragging = True
                else:
                    if mode == "car":
                        entities.append(create_car(x, y))
                    else:
                        entities.append(create_ped(x, y))

            # RIGHT CLICK
            elif event.button == 3:
                e = find_nearest(x, y)
                if e:
                    entities.remove(e)
                    if e == selected_entity:
                        selected_entity = None

        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False

    # Dragging logic
    if dragging and selected_entity:
        mx, my = pygame.mouse.get_pos()
        selected_entity.x = mx
        selected_entity.y = my
        # change velocity and angle in future?

    # Continuous input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]: current_speed += 1
    if keys[pygame.K_MINUS]: current_speed -= 1

    if keys[pygame.K_w]: current_speed += 0.1
    if keys[pygame.K_s]: current_speed -= 0.1

    if keys[pygame.K_q]: current_heading -= 0.05
    if keys[pygame.K_e]: current_heading += 0.05

    if keys[pygame.K_a]: current_heading -= 0.01
    if keys[pygame.K_d]: current_heading += 0.01


# DRAWING HELPERS
def draw_text(text, x, y):
    """Draw text on screen."""
    screen.blit(uiFont.render(text, True, (255, 255, 255)), (x, y))


def draw_preview():
    """Draws a line from mouse cursor in the direction of current heading, to preview new entity placement."""
    mx, my = pygame.mouse.get_pos()
    px = mx + math.cos(current_heading) * 40
    py = my + math.sin(current_heading) * 40
    pygame.draw.line(screen, (100, 200, 255), (mx, my), (px, py), 3)

    speed = current_speed
    direction = 1 if speed >= 0 else -1
    abs_speed = abs(speed)

    if abs_speed < 5:
        length = 20
    elif abs_speed < 10:
        length = abs_speed * 5
    else:
        length = 50

    dx = math.cos(current_heading) * length * direction
    dy = math.sin(current_heading) * length * direction

    px = mx + dx
    py = my + dy

    color = (0, 0, 255) if speed >= 0 else (255, 0, 0)
    pygame.draw.line(screen, color, (mx, my), (px, py), 3)


def draw_selection():
    """Highlights selected entity."""
    if selected_entity:
        pygame.draw.circle(screen, (255, 255, 0),
                           (int(selected_entity.x), int(selected_entity.y)), 20, 2)


def draw_ui():
    """Draws UI text and instructions."""
    lines = [
        f"Mode: {mode}",
        f"Speed: {current_speed:.2f}",
        f"Heading: {math.degrees(current_heading):.1f}",
        f"Name: {scenario_name or '[not set]'}",
        f"Description: {scenario_description or '[not set]'}",
        "",
        "LMB = place/select",
        "Drag = move entity",
        "RMB = delete",
        "DEL = delete selected",
        "TAB = switch mode",
        "N = name | T = description",
        "` = save | L = load latest",
    ]

    for i, t in enumerate(lines):
        draw_text(t, 10, 10 + i * 20)

    if overwrite_prompt:
        draw_text("Overwrite? Y/N", 10, HEIGHT - 60)

    if input_mode:
        draw_text("INPUT MODE (ENTER = confirm, ESC = cancel)", 10, HEIGHT - 70)
        pygame.draw.rect(screen, (50, 50, 70), (10, HEIGHT - 40, 500, 30))
        draw_text(f"{input_mode}: {input_buffer}", 15, HEIGHT - 35)


if __name__ == "__main__":
    main() 