import pygame  # type: ignore
import math
import sys
import os
import argparse
import random
import configparser

from sim.entities import BaseEntity, Car, Pedestrian
from sim.scenario_loader import load_scenario
from sim.physics_engine import PhysicsEngine
from sim.draw import draw

# ==========================
# CONFIG / GLOBALS
# ==========================
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

MAX_EPISODE_TIME = 10.0  # seconds per scenario

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

entities = []
controlledCar = None
engine = None
scenario_files = []
scenario_index = 0
episode_time = 0.0
MODE = "manual"
HEADLESS = False

# 60 Hz physics
FIXED_DT = 1.0 / 60.0  
 # prevents spiral of death if rendering is too slow
accumulator = 0.0
MAX_ACCUMULATED_TIME = 0.25 

def main():
    global episode_time, entities, controlledCar, engine, accumulator, running, scenario_index
    running = True
    episode_time = 0.0

    # Initial load
    load_current_scenario()

    while running:
        frame_dt = deltaTimeBetweenFramesMs()
        accumulator += frame_dt

        if accumulator > MAX_ACCUMULATED_TIME:
            accumulator = MAX_ACCUMULATED_TIME  # prevents lag explosion

        # input/events still per frame
        if not HEADLESS:
            if not handle_events():
                break

        keys = pygame.key.get_pressed() if not HEADLESS else []

        # ----- PHYSICS LOOP -----
        while accumulator >= FIXED_DT:
            accumulator -= FIXED_DT

            # Control (IMPORTANT: computed per physics step, not render step)
            if MODE == "manual" and not HEADLESS:
                steer, throttle, brake = manual_control(keys, controlledCar, FIXED_DT)
            else:
                steer, throttle, brake = simple_ai_policy(controlledCar, entities)

            try:
                controlledCar.update(throttle, brake, steer, FIXED_DT)
                engine.step(FIXED_DT)
            except Exception as e:
                # temporarily accepting due to edge cases
                print(f"Error during physics update: {e}")
                # running = False
                break

            episode_time += FIXED_DT

            if episode_time > MAX_EPISODE_TIME:
                scenario_index = (scenario_index + 1) % len(scenario_files)
                reset_scenario()
                break

        # Auto-cycle scenarios
        if episode_time > MAX_EPISODE_TIME:
            scenario_index = (scenario_index + 1) % len(scenario_files)
            reset_scenario()

        # Draw / log
        if not HEADLESS:
            screen.fill((20, 20, 30))
            draw_ui()
            pygame.display.flip()
        else:
            log_headless()

    pygame.quit()
    sys.exit()


def deltaTimeBetweenFramesMs():
     """Return the time in ms since the last frame, based on the clock tick."""
     return clock.tick(FPS) / 1000.0

# ==========================
# ARGUMENT PARSING
# ==========================
def parse_args():
    """Helper argument parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=str, default="scenarios", help="Path to scenario file or folder")
    parser.add_argument("--mode", type=str, default="manual", choices=["manual", "ai"], help="Control mode")
    parser.add_argument("--headless", action="store_true", help="Run without graphics for fast simulation")
    return parser.parse_args()


# ==========================
# SCENARIO LOADING
# ==========================
def load_all_scenarios(folder_or_file):
    """Return a list of JSON scenario file paths from a file or folder."""
    if os.path.isfile(folder_or_file):
        return [folder_or_file]
    elif os.path.isdir(folder_or_file):
        files = [os.path.join(folder_or_file, f) for f in os.listdir(folder_or_file) if f.endswith(".json")]
        files.sort()
        return files
    else:
        raise FileNotFoundError(f"{folder_or_file} not found")


def transform_scenario(entities):
    """Optionally mirror the scenario and scale velocities randomly."""
    # mirror
    if random.random() < 0.5:
        for e in entities:
            e.x = WIDTH - e.x
            if hasattr(e, "vx"): e.vx = -e.vx
            if hasattr(e, "speed") and e.type == "car":
                vx, vy = e.get_velocity()
                e.set_velocity(-vx, vy)
    # speed scale
    scale = random.uniform(0.7, 1.7)
    for e in entities:
        if hasattr(e, "vx"): e.vx *= scale
        if hasattr(e, "vy"): e.vy *= scale
        if hasattr(e, "speed") and e.type == "car":
            vx, vy = e.get_velocity()
            e.set_velocity(vx*scale, vy*scale)
    return entities


def load_current_scenario():
    """Load the current scenario and initialize entities, controlledCar, and physics engine."""
    global entities, controlledCar, engine
    path = scenario_files[scenario_index]
    entities, controlledCar, scenarioName, scenarioDescription = load_scenario(path)

    # Convert dicts to objects
    for i, e in enumerate(entities):
        if e.type == "car":
            new_e = Car(e.__dict__)
            entities[i] = new_e

            if e == controlledCar:
                controlledCar = new_e

        elif e.type == "pedestrian":
            entities[i] = Pedestrian(e.__dict__)

    entities = transform_scenario(entities)
    engine = PhysicsEngine(entities)
    return entities, controlledCar, engine


# ==========================
# CONTROL
# ==========================
def manual_control(keys, controlledCar, FIXED_DT):
    """Return (steer, throttle, brake) for manual input."""
    steer = throttle = brake = 0
    if keys[pygame.K_a]: steer = -1
    if keys[pygame.K_d]: steer = 1
    if keys[pygame.K_w]: throttle = 1
    if keys[pygame.K_s]: brake = 1
    return steer, throttle, brake


def simple_ai_policy(controlledCar, entities):
    """Placeholder AI policy, returns (steer, throttle, brake)."""
    return 1, 0, 1  # Always brake for now


def handle_events():
    """Process pygame input events (keyboard/mouse)."""
    global running, MODE, scenario_index
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_TAB:
                MODE = "ai" if MODE == "manual" else "manual"
            elif event.key == pygame.K_r:
                reset_scenario()
            elif event.key == pygame.K_n:
                scenario_index = (scenario_index + 1) % len(scenario_files)
                reset_scenario()
    return True

def reset_scenario():
    """Reload the current scenario and reset episode timer."""
    global episode_time, entities, controlledCar, engine
    load_current_scenario()
    episode_time = 0.0


# DRAWING
def draw_ui():
    """Draw overlay text showing current mode, time, etc."""
    draw(
        screen,
        entities,
        controlledCar,
        mode=MODE,
        font=uiFont,
        episode_time=episode_time,
        max_time=MAX_EPISODE_TIME,
        scenario_index=scenario_index
    )


def log_headless():
    """Print scenario progress when running headless."""
    print(f"[Scenario {scenario_index+1}] t={episode_time:.2f}s, controlledCar pos=({controlledCar.x:.1f},{controlledCar.y:.1f}), speed={controlledCar.speed:.1f}")




# ==========================
# ENTRY POINT
# ==========================
if __name__ == "__main__":
    args = parse_args()
    scenario_files = load_all_scenarios(args.scenario)
    MODE = args.mode
    HEADLESS = args.headless
    main()