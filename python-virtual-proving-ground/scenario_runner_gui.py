import pygame  # type: ignore
import math
import sys
import os
import argparse
import random
import configparser

from sim.entities import BaseEntity, Car, Pedestrian
from sim.scenario_loader import load_scenario, SimulationState
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

running = True
scenarioState = SimulationState()
"""
contains all of the:
    entities = []
    controlledCar = None
    engine = None
    scenario_files = []
    scenario_index = 0
    episode_time = 0.0
    MODE = "manual"
    HEADLESS = False
"""

# 60 Hz physics
simulation_frames = 60.0
FIXED_DT = 1.0 / simulation_frames 

 # prevents spiral of death if rendering is too slow
accumulator = 0.0
MAX_ACCUMULATED_TIME = 0.25 

def main():
    global scenarioState , accumulator, running
    # previously used:
    # global episode_time, entities, controlledCar, engine, accumulator, running, scenario_index
    scenarioState.scenario_files = load_all_scenarios(args.scenario)

    print("FILES:", scenarioState.scenario_files)
    print("INDEX:", scenarioState.scenario_index)

    running = True
    scenarioState.episode_time = 0.0
    load_current_scenario(scenarioState)


    while running:
        frame_dt = deltaTimeBetweenFramesMs()
        accumulator += frame_dt

        if accumulator > MAX_ACCUMULATED_TIME:
            accumulator = MAX_ACCUMULATED_TIME  # prevents lag explosion

        # input/events still per frame
        if not HEADLESS:
            if not handle_events(scenarioState):
                break

        keys = pygame.key.get_pressed() if not HEADLESS else []

        # ----- PHYSICS LOOP -----
        while accumulator >= FIXED_DT:
            accumulator -= FIXED_DT

            # Control (IMPORTANT: computed per physics step, not render step)
            if MODE == "manual" and not HEADLESS:
                steer, throttle, brake = manual_control(keys, FIXED_DT)
            else:
                steer, throttle, brake = simple_ai_policy(scenarioState)

            # !!! needs urgent replacement with moving logic of acceleration/turning etc into the physics engine
            scenarioState.controlledCar.update(throttle, brake, steer, FIXED_DT)
            # because that's just bad form

            scenarioState.engine.step(FIXED_DT)
            scenarioState.episode_time += FIXED_DT

            if scenarioState.episode_time > MAX_EPISODE_TIME:
                scenarioState.scenario_index = (scenarioState.scenario_index + 1) % len(scenario_files)
                reset_scenario(scenarioState)
                break

        # Auto-cycle scenarios
        if scenarioState.episode_time > MAX_EPISODE_TIME:
            scenarioState.scenario_index = (scenarioState.scenario_index + 1) % len(scenario_files)
            reset_scenario(scenarioState)

        # Draw / log
        if not HEADLESS:
            screen.fill((20, 20, 30))
            draw_ui(scenarioState)
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


def load_current_scenario(scenarioState):
    """Load the current scenario and initialize entities, controlledCar, and physics engine."""
    path = scenarioState.scenario_files[scenarioState.scenario_index]

    entities, controlledCar, _, _ = load_scenario(path)

    new_entities = []
    new_controlled = None

    for e in entities:
        if e.type == "car":
            new_e = Car(e.__dict__)
            if e == controlledCar:
                new_controlled = new_e
        elif e.type == "pedestrian":
            new_e = Pedestrian(e.__dict__)
        else:
            new_e = e

        new_entities.append(new_e)

    scenarioState.entities = transform_scenario(new_entities)
    scenarioState.controlledCar = new_controlled
    scenarioState.engine = PhysicsEngine(scenarioState.entities)
    scenarioState.episode_time = 0.0


# ==========================
# CONTROL
# ==========================
def manual_control(keys, FIXED_DT):
    """Return (steer, throttle, brake) for manual input."""
    steer = throttle = brake = 0
    if keys[pygame.K_a]: steer = -1
    if keys[pygame.K_d]: steer = 1
    if keys[pygame.K_w]: throttle = 1
    if keys[pygame.K_s]: brake = 1
    return steer, throttle, brake


def simple_ai_policy(controlledCar, scenarioState):
    """Placeholder AI policy, returns (steer, throttle, brake)."""
    # should take data from the model
    return 0, 0, 1  # Always brake for now


def handle_events(scenarioState):
    """Process pygame input events (keyboard/mouse)."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_TAB:
                scenarioState.mode = "ai" if scenarioState.mode == "manual" else "manual"
            elif event.key == pygame.K_r:
                reset_scenario(scenarioState)
            elif event.key == pygame.K_n:
                scenarioState.scenario_index = (scenarioState.scenario_index + 1) % len(scenarioState.scenario_files)
                reset_scenario(scenarioState)

    return True

def reset_scenario(scenarioState):
    """Reload the current scenario and reset episode timer."""
    load_current_scenario(scenarioState)
    scenarioState.episode_time = 0.0


# DRAWING
def draw_ui(scenarioState):
    """Draw overlay text showing current mode, time, etc."""
    draw(
        screen,
        scenarioState.entities,
        scenarioState.controlledCar,
        mode=scenarioState.mode,
        font=uiFont,
        episode_time=scenarioState.episode_time,
        max_time=MAX_EPISODE_TIME,
        scenario_index=scenarioState.scenario_index
    )


def log_headless(scenarioState):
    """
    Logs the car states when launched headless.
    """
    ego = scenarioState.controlledCar
    print(f"[Scenario {scenarioState.scenario_index+1}] "
          f"t={scenarioState.episode_time:.2f}s, "
          f"pos=({ego.x:.1f},{ego.y:.1f}), "
          f"speed={ego.speed:.1f}")



# ==========================
# ENTRY POINT
# ==========================
if __name__ == "__main__":
    args = parse_args()
    scenario_files = load_all_scenarios(args.scenario)
    MODE = args.mode
    HEADLESS = args.headless
    main()