import pygame
import math
import sys
import os
import argparse
import random
import time

from sim.entities import BaseEntity, Car, Pedestrian
from sim.scenario_loader import load_scenario
from sim.physics_engine import PhysicsEngine

# ==========================
# CONFIG
# ==========================
WIDTH = 800
HEIGHT = 640
FPS = 60
MAX_EPISODE_TIME = 10.0  # seconds per scenario

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 24)

# ==========================
# COMMAND LINE ARGUMENTS
# ==========================
parser = argparse.ArgumentParser()
parser.add_argument("--scenario", type=str, default="scenarios", help="Path to scenario file or folder")
parser.add_argument("--mode", type=str, default="manual", choices=["manual", "ai"], help="Control mode")
parser.add_argument("--headless", action="store_true", help="Run without graphics for fast simulation")
args = parser.parse_args()

SCENARIO_PATH = args.scenario
MODE = args.mode
HEADLESS = args.headless

# ==========================
# SIMPLE AI POLICY (placeholder)
# ==========================
def simple_ai_policy(ego, entities):
    steer = 0
    throttle = 1
    brake = 0
    return steer, throttle, brake

# ==========================
# SCENARIO LOADING
# ==========================
def load_all_scenarios(folder_or_file):
    if os.path.isfile(folder_or_file):
        return [folder_or_file]
    elif os.path.isdir(folder_or_file):
        files = [os.path.join(folder_or_file,f) for f in os.listdir(folder_or_file) if f.endswith(".json")]
        files.sort()
        return files
    else:
        raise FileNotFoundError(f"{folder_or_file} not found")

scenario_files = load_all_scenarios(SCENARIO_PATH)
scenario_index = 0

def load_current():
    global entities, ego, engine
    path = scenario_files[scenario_index]
    entities, ego = load_scenario(path)

    # -----------
    for i,e in enumerate(entities):
        if e.type=="car":
            entities[i] = Car(e.__dict__)
        elif e.type=="pedestrian":
            entities[i] = Pedestrian(e.__dict__)
    
    entities = transform_scenario(entities)
    engine = PhysicsEngine(entities)
    return entities, ego, engine

def transform_scenario(entities):
    # mirror
    if random.random() < 0.5:
        for e in entities:
            e.x = WIDTH - e.x
            if hasattr(e,"vx"): e.vx = -e.vx
            if hasattr(e,"speed") and e.type=="car":
                vx, vy = e.get_velocity()
                e.set_velocity(-vx, vy)
    # speed scale
    scale = random.uniform(0.7, 1.7)
    for e in entities:
        if hasattr(e,"vx"): e.vx *= scale
        if hasattr(e,"vy"): e.vy *= scale
        if hasattr(e,"speed") and e.type=="car":
            vx, vy = e.get_velocity()
            e.set_velocity(vx*scale, vy*scale)
    return entities

# ==========================
# DRAWING
# ==========================
def draw():
    screen.fill((20,20,30))
    for e in entities:
        if e.type == "pedestrian":
            pygame.draw.circle(screen,(0,255,0),(int(e.x),int(e.y)),8)
        elif e.type == "car":
            color = (80,180,255) if e == ego else (200,50,50)
            # draw collision circles
            for cx, cy, r in e.circles():
                pygame.draw.circle(screen, (255,255,0), (int(cx), int(cy)), int(r), 1)
            # draw rectangle covering circles
            rect_length = 2*e.front_offset
            rect_width = 2*e.radius
            rect_surf = pygame.Surface((rect_length, rect_width), pygame.SRCALPHA)
            pygame.draw.rect(rect_surf, (255,255,0,80), (0,0,rect_length,rect_width), 2)
            rotated = pygame.transform.rotate(rect_surf, -math.degrees(e.heading))
            r = rotated.get_rect(center=(e.x,e.y))
            screen.blit(rotated, r)
            # heading arrow
            hx = e.x + math.cos(e.heading)*40
            hy = e.y + math.sin(e.heading)*40
            pygame.draw.line(screen,(255,255,0),(e.x,e.y),(hx,hy),2)
            # prediction arrow
            if e==ego and MODE=="ai":
                px = e.x + math.cos(e.heading + e.steer*0.5)*60
                py = e.y + math.sin(e.heading + e.steer*0.5)*60
                pygame.draw.line(screen,(0,255,255),(e.x,e.y),(px,py),2)
    # UI text
    draw_text(f"Mode: {MODE}",10,10)
    draw_text(f"Scenario: {scenario_index+1}/{len(scenario_files)}",10,30)
    draw_text(f"Time: {episode_time:.1f}s / {MAX_EPISODE_TIME}s",10,50)
    draw_text("TAB = switch mode | R = reset | N = next scenario",10,70)
    draw_text(f"Ego Eval Score: {get_eval_score():.2f}",10,90)

def draw_text(text,x,y):
    img = FONT.render(text,True,(255,255,255))
    screen.blit(img,(x,y))

def get_eval_score():
    return ego.speed if hasattr(ego,"speed") else 0

# ==========================
# CONTROL
# ==========================
def manual_control(keys, ego, dt):
    steer, throttle, brake = 0,0,0
    if keys[pygame.K_a]: steer=-1
    if keys[pygame.K_d]: steer=1
    if keys[pygame.K_w]: throttle=1
    if keys[pygame.K_s]: brake=1
    return steer, throttle, brake

def reset():
    global episode_time
    load_current()
    episode_time = 0

# ==========================
# INITIAL LOAD
# ==========================
entities, ego, engine = load_current()
episode_time = 0

# ==========================
# MAIN LOOP
# ==========================
running = True
while running:
    dt = clock.tick(FPS)/1000
    episode_time += dt

    # handle events
    if not HEADLESS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running=False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running=False
                elif event.key == pygame.K_TAB: MODE="ai" if MODE=="manual" else "manual"
                elif event.key == pygame.K_r: reset()
                elif event.key == pygame.K_n:
                    scenario_index = (scenario_index+1) % len(scenario_files)
                    reset()

    # control
    keys = pygame.key.get_pressed() if not HEADLESS else []
    if MODE=="manual" and not HEADLESS:
        steer, throttle, brake = manual_control(keys, ego, dt)
    else:
        steer, throttle, brake = simple_ai_policy(ego, entities)

    ego.update(throttle, brake, steer, dt)
    engine.step(dt)

    # auto-cycle scenarios
    if episode_time > MAX_EPISODE_TIME:
        scenario_index = (scenario_index+1) % len(scenario_files)
        reset()

    # draw only if not headless
    if not HEADLESS:
        draw()
        pygame.display.flip()
    else:
        # headless logging
        print(f"[Scenario {scenario_index+1}] t={episode_time:.2f}s, Ego pos=({ego.x:.1f},{ego.y:.1f}), speed={ego.speed:.1f}")

pygame.quit()
sys.exit()