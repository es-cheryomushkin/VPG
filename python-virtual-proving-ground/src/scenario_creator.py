import pygame  # type: ignore
import json
import math
import os
import configparser
from datetime import datetime

from sim.draw import draw
from sim.entities import Car, Pedestrian

# =========================================================
# INITIALIZATION
# =========================================================
pygame.init()

config = configparser.ConfigParser()
config.read("config.ini")

WIDTH = config.getint("window", "width")
HEIGHT = config.getint("window", "height")
FPS = config.getint("window", "fps")
FONT_SIZE = config.getint("ui", "font_size")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
uiFont = pygame.font.SysFont(None, FONT_SIZE)

camera_x = 0
camera_y = 0

# =========================================================
# GLOBAL STATE
# =========================================================
entities = []
roads = []


selected_entity = None
dragging = False

current_speed = 0
current_heading = 0
current_throttle = 0.0
current_brake = 0.0
current_steer = 0.0

modes = ["car", "pedestrian", "road"]
mode_index = 0
mode = modes[mode_index]

input_mode = None
input_buffer = ""

scenario_name = ""
scenario_description = ""

overwrite_prompt = False

ROAD_WIDTH = 80

# =========================================================
# BACKGROUNDS
# =========================================================
background_images = []
background_index = 0
background_surface = None


def load_backgrounds():
    global background_images

    os.makedirs("backgrounds", exist_ok=True)

    background_images = [
        os.path.join("backgrounds", f)
        for f in os.listdir("backgrounds")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    background_images.sort()

    if background_images:
        set_background(0)


def set_background(index):
    global background_index, background_surface

    if not background_images:
        background_surface = None
        return

    background_index = index % len(background_images)

    img = pygame.image.load(
        background_images[background_index]
    ).convert()

    background_surface = pygame.transform.scale(
        img,
        (WIDTH, HEIGHT)
    )

def world_to_screen(x, y):
    return (
        x - camera_x + WIDTH // 2,
        y - camera_y + HEIGHT // 2
    )

def screen_to_world(x, y):
    return (
        x + camera_x - WIDTH // 2,
        y + camera_y - HEIGHT // 2
    )

# =========================================================
# MAIN LOOP
# =========================================================
def main():
    global running

    load_backgrounds()

    running = True

    while running:
        handle_events()

        # background
        if background_surface:
            screen.blit(background_surface, (0, 0))
        else:
            screen.fill((20, 20, 30))

        # roads first
        draw_roads()

        # entities
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
        clock.tick(FPS)

    pygame.quit()


# =========================================================
# ROAD CLASS
# =========================================================
class Road:
    def __init__(self, x, y, width, height, angle):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "angle": self.angle
        }


# =========================================================
# SAVE / LOAD
# =========================================================
def save_scenario():
    global overwrite_prompt, scenario_name

    os.makedirs("scenarios", exist_ok=True)

    if not scenario_name.strip():
        scenario_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"scenario_{scenario_name}.json"
    path = os.path.join("scenarios", filename)

    # overwrite protection
    if os.path.exists(path) and not overwrite_prompt:
        overwrite_prompt = True
        print("File exists. Press Y to overwrite or N to cancel.")
        return

    # ensure cars first
    cars = [e for e in entities if e.type == "car"]
    others = [e for e in entities if e.type != "car"]

    entities_sorted = cars + others

    entity_data = []

    for e in entities_sorted:

        entity_data.append({
            "type": e.type,

            "x": e.x,
            "y": e.y,

            "vx": getattr(e, "vx", e.get_velocity()[0]),
            "vy": getattr(e, "vy", e.get_velocity()[1]),

            "heading": getattr(e, "heading", 0),

            "mass": getattr(e, "mass", 1),

            # TRAFFIC CONTROL
            "throttle": getattr(e, "throttle", 0.0),
            "brake": getattr(e, "brake", 0.0),
            "steer": getattr(e, "steer", 0.0),
        })

    data = {
        "version": 1,
        "name": scenario_name,
        "description": scenario_description,

        "background":
            background_images[background_index]
            if background_images else None,

        "roads": [r.to_dict() for r in roads],

        "entities": entity_data
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    overwrite_prompt = False

    print("Saved:", path)


def load_scenario_file(path):
    global entities
    global roads
    global scenario_name
    global scenario_description
    global background_surface

    with open(path) as f:
        data = json.load(f)

    entities.clear()
    roads.clear()

    scenario_name = data.get("name", "")
    scenario_description = data.get("description", "")

    # background
    bg = data.get("background")

    if bg and os.path.exists(bg):
        img = pygame.image.load(bg).convert()

        background_surface = pygame.transform.scale(
            img,
            (WIDTH, HEIGHT)
        )

    # roads
    for r in data.get("roads", []):
        roads.append(
            Road(
                r["x"],
                r["y"],
                r["width"],
                r["height"],
                r["angle"]
            )
        )

    # entities
    for e in data.get("entities", []):
        if e["type"] == "car":
            entities.append(Car(e))

        elif e["type"] == "pedestrian":
            entities.append(Pedestrian(e))

    print("Loaded:", path)


def load_latest_scenario():
    if not os.path.exists("scenarios"):
        return

    files = [
        os.path.join("scenarios", f)
        for f in os.listdir("scenarios")
        if f.endswith(".json")
    ]

    if not files:
        return

    latest = max(files, key=os.path.getmtime)

    load_scenario_file(latest)


# =========================================================
# ENTITY HELPERS
# =========================================================
def create_car(x, y):
    return Car({
        "type": "car",

        "x": x,
        "y": y,

        "vx": math.cos(current_heading) * current_speed,
        "vy": math.sin(current_heading) * current_speed,

        "heading": current_heading,

        "mass": 1500,

        "throttle": current_throttle,
        "brake": current_brake,
        "steer": current_steer,
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


def create_road(x, y):
    length = max(100, abs(current_speed) * 20)

    return Road(
        x,
        y,
        length,
        ROAD_WIDTH,
        current_heading
    )


def find_nearest(x, y, radius=30):
    closest = None
    best = float("inf")

    for e in entities:
        d = math.hypot(e.x - x, e.y - y)

        if d < best and d < radius:
            best = d
            closest = e

    return closest


# =========================================================
# INPUT
# =========================================================
def handle_events():
    global running
    global mode
    global mode_index

    global current_speed
    global current_heading
    global current_throttle
    global current_brake
    global current_steer

    global input_mode
    global input_buffer
    global scenario_name
    global scenario_description
    
    global selected_entity
    global dragging
    global overwrite_prompt

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # =================================================
        # KEYBOARD
        # =================================================
        if event.type == pygame.KEYDOWN:

            # text input mode
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

            # =================================================
            # NORMAL CONTROLS
            # =================================================
            match event.key:

                case pygame.K_ESCAPE:
                    running = False

                case pygame.K_TAB:
                    mode_index = (mode_index + 1) % len(modes)
                    mode = modes[mode_index]

                case pygame.K_F5:
                    save_scenario()

                case pygame.K_F9:
                    load_latest_scenario()

                case pygame.K_DELETE:
                    if selected_entity:
                        entities.remove(selected_entity)
                        selected_entity = None

                case pygame.K_c:
                    entities.clear()
                    roads.clear()
                    selected_entity = None

                case pygame.K_r:
                    current_speed = 0

                case pygame.K_y:
                    if overwrite_prompt:
                        overwrite_prompt = False
                        save_scenario()

                case pygame.K_F2:
                    if overwrite_prompt:
                        overwrite_prompt = False

                    input_mode = "name"
                    input_buffer = scenario_name

                case pygame.K_F3:
                    input_mode = "description"
                    input_buffer = scenario_description

                case pygame.K_SEMICOLON:
                    set_background(background_index - 1)

                case pygame.K_QUOTE:
                    set_background(background_index + 1)

        # =================================================
        # MOUSE
        # =================================================
        if event.type == pygame.MOUSEBUTTONDOWN:

            if input_mode:
                continue

            mx, my = pygame.mouse.get_pos()
            x, y = screen_to_world(mx, my)

            # left click
            if event.button == 1:

                clicked = find_nearest(x, y)

                if clicked:
                    selected_entity = clicked
                    dragging = True

                else:
                    if mode == "car":
                        entities.append(create_car(x, y))

                    elif mode == "pedestrian":
                        entities.append(create_ped(x, y))

                    elif mode == "road":
                        roads.append(create_road(x, y))

            # right click
            elif event.button == 3:

                e = find_nearest(x, y)

                if e:
                    entities.remove(e)

                    if e == selected_entity:
                        selected_entity = None

        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False

    # dragging
    if dragging and selected_entity:
        mx, my = pygame.mouse.get_pos()

        selected_entity.x = mx
        selected_entity.y = my

    # =====================================================
    # CONTINUOUS INPUT
    # =====================================================
    keys = pygame.key.get_pressed()

    if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
        current_speed += 1

    if keys[pygame.K_MINUS]:
        current_speed -= 1

    if keys[pygame.K_w]:
        current_speed += 0.1

    if keys[pygame.K_s]:
        current_speed -= 0.1

    if keys[pygame.K_q]:
        current_heading -= 0.05

    if keys[pygame.K_e]:
        current_heading += 0.05

    if keys[pygame.K_a]:
        current_heading -= 0.01

    if keys[pygame.K_d]:
        current_heading += 0.01

    if keys[pygame.K_i]:
        current_throttle = min(1.0, current_throttle + 0.01)

    if keys[pygame.K_k]:
        current_throttle = max(0.0, current_throttle - 0.01)

    if keys[pygame.K_o]:
        current_brake = min(1.0, current_brake + 0.01)

    if keys[pygame.K_l]:
        current_brake = max(0.0, current_brake - 0.01)

    if keys[pygame.K_j]:
        current_steer = max(-1.0, current_steer - 0.01)

    if keys[pygame.K_u]:
        current_steer = min(1.0, current_steer + 0.01)


# =========================================================
# DRAW HELPERS
# =========================================================
def draw_text(text, x, y):
    screen.blit(
        uiFont.render(text, True, (255, 255, 255)),
        (x, y)
    )


def draw_roads():
    for r in roads:

        surf = pygame.Surface(
            (r.width, r.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            surf,
            (80, 80, 80),
            (0, 0, r.width, r.height)
        )

        rotated = pygame.transform.rotate(
            surf,
            -math.degrees(r.angle)
        )

        sx, sy = world_to_screen(r.x, r.y)
        rect = rotated.get_rect(center=(sx, sy))

        screen.blit(rotated, rect)


def draw_preview():
    mx, my = pygame.mouse.get_pos()

    # road preview
    if mode == "road":

        length = max(100, abs(current_speed) * 20)

        surf = pygame.Surface(
            (length, ROAD_WIDTH),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            surf,
            (120, 120, 120, 120),
            (0, 0, length, ROAD_WIDTH)
        )

        rotated = pygame.transform.rotate(
            surf,
            -math.degrees(current_heading)
        )

        rect = rotated.get_rect(
            center=(mx, my)
        )

        screen.blit(rotated, rect)

        return

    # normal preview
    px = mx + math.cos(current_heading) * 40
    py = my + math.sin(current_heading) * 40

    pygame.draw.line(
        screen,
        (100, 200, 255),
        (mx, my),
        (px, py),
        3
    )

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

    color = (
        (0, 0, 255)
        if speed >= 0
        else (255, 0, 0)
    )

    pygame.draw.line(
        screen,
        color,
        (mx, my),
        (px, py),
        3
    )


def draw_selection():
    if selected_entity:
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (int(selected_entity.x), int(selected_entity.y)),
            20,
            2
        )


def draw_ui():

    bg_name = (
        os.path.basename(background_images[background_index])
        if background_images
        else "[none]"
    )

    lines = [
        f"Mode: {mode}",
        f"Speed: {current_speed:.2f}",
        f"Heading: {math.degrees(current_heading):.1f}",
        f"Traffic Throttle: {current_throttle:.2f}",
        f"Traffic Brake: {current_brake:.2f}",
        f"Traffic Steer: {current_steer:.2f}",
        f"Background: {bg_name}",
        f"Name: {scenario_name or '[not set]'}",
        f"Description: {scenario_description or '[not set]'}",
        "",
        "TAB = switch mode",
        "; ' = switch background",
        "",
        "LMB = place/select",
        "Drag = move entity",
        "RMB = delete",
        "DEL = delete selected",
        "",
        "W/S = speed +/-",
        "A/D = heading +/-",
        "I/K = throttle +/-",
        "O/L = brake +/-",
        "U/J = steer +/-",
        "",
        "F2 = name",
        "F3 = description",
        "F5 = save",
        "F9 = load latest",
    ]

    for i, t in enumerate(lines):
        draw_text(t, 10, 10 + i * 20)

    if overwrite_prompt:
        draw_text(
            "Overwrite? Y/N",
            10,
            HEIGHT - 60
        )

    if input_mode:

        draw_text(
            "INPUT MODE (ENTER confirm, ESC cancel)",
            10,
            HEIGHT - 70
        )

        pygame.draw.rect(
            screen,
            (50, 50, 70),
            (10, HEIGHT - 40, 500, 30)
        )

        draw_text(
            f"{input_mode}: {input_buffer}",
            15,
            HEIGHT - 35
        )


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    main()