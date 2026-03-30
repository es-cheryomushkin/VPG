import pygame  # type: ignore
import math
import sys
import os
import argparse
import random

from sim.entities import BaseEntity, Car, Pedestrian
from sim.scenario_loader import load_scenario
from sim.physics_engine import PhysicsEngine
from sim.draw import draw

# ==========================
# CONFIG / GLOBALS
# ==========================
WIDTH = 1200
HEIGHT = 600
FPS = 60
MAX_EPISODE_TIME = 10.0  # seconds per scenario

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 24)

entities = []
ego = None
engine = None
scenario_files = []
scenario_index = 0
episode_time = 0.0
MODE = "manual"
HEADLESS = False

# ==========================
# ARGUMENT PARSING
# ==========================
def parse_args():
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
    """Load the current scenario and initialize entities, ego, and physics engine."""
    global entities, ego, engine
    path = scenario_files[scenario_index]
    entities, ego = load_scenario(path)

    # Convert dicts to objects
    for i, e in enumerate(entities):
        if e.type == "car":
            new_e = Car(e.__dict__)
            entities[i] = new_e

            if e == ego:
                ego = new_e

        elif e.type == "pedestrian":
            entities[i] = Pedestrian(e.__dict__)

    entities = transform_scenario(entities)
    engine = PhysicsEngine(entities)
    return entities, ego, engine


# ==========================
# CONTROL
# ==========================
def manual_control(keys, ego, dt):
    """Return (steer, throttle, brake) for manual input."""
    steer = throttle = brake = 0
    if keys[pygame.K_a]: steer = -1
    if keys[pygame.K_d]: steer = 1
    if keys[pygame.K_w]: throttle = 1
    if keys[pygame.K_s]: brake = 1
    return steer, throttle, brake


def simple_ai_policy(ego, entities):
    """Placeholder AI policy, returns (steer, throttle, brake)."""
    return 0, 1, 0


# ==========================
# EVENT HANDLING
# ==========================
def handle_events():
    """Process pygame events (keyboard/mouse)."""
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
    global episode_time, entities, ego, engine
    load_current_scenario()
    episode_time = 0.0


# ==========================
# DRAWING
# ==========================
def draw_ui():
    """Draw overlay text showing current mode, time, etc."""
    draw(
        screen,
        entities,
        ego,
        mode=MODE,
        font=FONT,
        episode_time=episode_time,
        max_time=MAX_EPISODE_TIME,
        scenario_index=scenario_index
    )


def log_headless():
    """Print scenario progress when running headless."""
    print(f"[Scenario {scenario_index+1}] t={episode_time:.2f}s, Ego pos=({ego.x:.1f},{ego.y:.1f}), speed={ego.speed:.1f}")


# ==========================
# MAIN LOOP
# ==========================
def main():
    global episode_time, entities, ego, engine, running, scenario_index
    running = True
    episode_time = 0.0

    # Initial load
    load_current_scenario()

    while running:
        dt = clock.tick(FPS) / 1000
        episode_time += dt

        if not HEADLESS:
            # Event handling
            if not handle_events():
                break

        # Control
        keys = pygame.key.get_pressed() if not HEADLESS else []
        if MODE == "manual" and not HEADLESS:
            steer, throttle, brake = manual_control(keys, ego, dt)
        else:
            steer, throttle, brake = simple_ai_policy(ego, entities)

        # Update ego & physics
        ego.update(throttle, brake, steer, dt)
        engine.step(dt)

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


# ==========================
# ENTRY POINT
# ==========================
if __name__ == "__main__":
    args = parse_args()
    scenario_files = load_all_scenarios(args.scenario)
    MODE = args.mode
    HEADLESS = args.headless
    main()