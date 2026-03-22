import pygame
import json
import math
import os
from datetime import datetime

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)

entities = []

current_speed = 0
current_heading = 0

mode = "car"  # or pedestrian


def draw_text(text, x, y):
    img = font.render(text, True, (255,255,255))
    screen.blit(img, (x,y))


def save_scenario():
    os.makedirs("scenarios", exist_ok=True)

    name = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"scenarios/scenario_{name}.json"

    with open(path, "w") as f:
        json.dump(entities, f, indent=2)

    print("Saved:", path)


def create_car(x, y):

    vx = math.cos(current_heading) * current_speed
    vy = math.sin(current_heading) * current_speed

    return {
        "type":"car",
        "x":x,
        "y":y,
        "vx":vx,
        "vy":vy,
        "heading":current_heading,
        "mass":1500
    }


def create_ped(x, y):

    vx = math.cos(current_heading) * current_speed
    vy = math.sin(current_heading) * current_speed

    return {
        "type":"pedestrian",
        "x":x,
        "y":y,
        "vx":vx,
        "vy":vy,
        "mass":80
    }


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_TAB:
                mode = "pedestrian" if mode == "car" else "car"

            if event.key == pygame.K_BACKQUOTE:
                save_scenario()

            if event.key == pygame.K_c:
                entities.clear()

            if event.key == pygame.K_DELETE and entities:
                entities.pop()

            if event.key == pygame.K_r:
                current_speed = 0

        if event.type == pygame.MOUSEBUTTONDOWN:

            x, y = pygame.mouse.get_pos()

            if mode == "car":
                entities.append(create_car(x,y))

            else:
                entities.append(create_ped(x,y))

    keys = pygame.key.get_pressed()

    # speed control
    if keys[pygame.K_w]:
        current_speed += 0.1

    if keys[pygame.K_s]:
        current_speed -= 0.1

    # heading control
    if keys[pygame.K_q]:
        current_heading -= 0.05

    if keys[pygame.K_e]:
        current_heading += 0.05

    if keys[pygame.K_a]:
        current_heading -= 0.01

    if keys[pygame.K_d]:
        current_heading += 0.01

    screen.fill((20,20,30))

    # draw entities
    for e in entities:

        if e["type"] == "pedestrian":

            pygame.draw.circle(screen,(0,255,0),(int(e["x"]),int(e["y"])),6)

        if e["type"] == "car":

            rect = pygame.Surface((60,30))
            rect.fill((200,50,50))

            rotated = pygame.transform.rotate(rect,-math.degrees(e["heading"]))
            r = rotated.get_rect(center=(e["x"],e["y"]))

            screen.blit(rotated,r)

        # draw velocity arrow
        vx = e["vx"]
        vy = e["vy"]

        pygame.draw.line(
            screen,
            (255,255,0),
            (e["x"], e["y"]),
            (e["x"] + vx*3, e["y"] + vy*3),
            2
        )

    # draw preview arrow (for next placement)
    mx, my = pygame.mouse.get_pos()

    px = mx + math.cos(current_heading)*40
    py = my + math.sin(current_heading)*40

    pygame.draw.line(screen,(100,200,255),(mx,my),(px,py),3)

    # UI text
    draw_text(f"Mode: {mode}",10,10)
    draw_text(f"Speed: {current_speed:.2f}",10,30)
    draw_text(f"Heading: {math.degrees(current_heading):.1f}",10,50)

    draw_text("Left click = place",10,80)
    draw_text("TAB = switch mode",10,100)
    draw_text("W/S = speed",10,120)
    draw_text("Q/E = rotate",10,140)
    draw_text("A/D = fine rotate",10,160)
    draw_text("` (Backquote) = save",10,180)

    pygame.display.flip()
    clock.tick(60)