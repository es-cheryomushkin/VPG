import pygame  # type: ignore
import math

# ==============================
# Text Drawing Function
# ==============================
def draw_text(screen, text, x, y, font, color=(255,255,255)):
    """
    Draw a single line of text on the screen.

    Args:
        screen: pygame Surface to draw on
        text (str): The string to render
        x (int): X-coordinate
        y (int): Y-coordinate
        font: pygame Font object
        color (tuple): RGB color of the text
    """
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


# ==============================
# Main Draw Function
# ==============================
def draw(screen, entities, ego, mode="manual", font=None,
         episode_time=0.0, max_time=10.0, scenario_index=0, show_legend=True):
    """
    Draws all entities, UI overlay, and optional prediction arrows.

    Args:
        screen: pygame Surface to draw on
        entities (list): List of entity objects (Car, Pedestrian, etc.)
        ego: Reference to the ego vehicle
        mode (str): "manual" or "ai"
        font: pygame Font object for UI text
        episode_time (float): Current simulation time
        max_time (float): Maximum episode duration
        scenario_index (int): Index of current scenario
        show_legend (bool): Whether to show legend
    """
    # Fill background
    screen.fill((20, 20, 30))

    for e in entities:
        if e.type == "pedestrian":
            # Draw pedestrian as green circle
            pygame.draw.circle(screen, (0, 255, 0), (int(e.x), int(e.y)), 8)

        elif e.type == "car":
            # Color: blue for ego, red for others
            color = (80, 180, 255) if e == ego else (200, 50, 50)

            # Draw collision circles (yellow outline)
            for cx, cy, r in e.circles():
                pygame.draw.circle(screen, (255, 255, 0), (int(cx), int(cy)), int(r), 1)

            # Draw rectangle covering circles (semi-transparent)
            rect_length = 2 * e.front_offset
            rect_width = 2 * e.radius
            rect_surf = pygame.Surface((rect_length, rect_width), pygame.SRCALPHA)
            pygame.draw.rect(rect_surf, color, (0, 0, rect_length, rect_width), 4)
            rotated = pygame.transform.rotate(rect_surf, -math.degrees(e.heading))
            r = rotated.get_rect(center=(e.x, e.y))
            screen.blit(rotated, r)

            # Draw heading arrow
            hx = e.x + math.cos(e.heading + getattr(e, 'steer', 0) * 0.5) * 60
            hy = e.y + math.sin(e.heading + getattr(e, 'steer', 0) * 0.5) * 60
            pygame.draw.line(screen, (255, 255, 0), (e.x, e.y), (hx, hy), 2)


    # ==============================
    # UI Overlay
    # ==============================
    if font is not None and show_legend:
        draw_text(screen, f"Mode: {mode}", 10, 10, font)
        draw_text(screen, f"Scenario: {scenario_index + 1}", 10, 30, font)
        draw_text(screen, f"Time: {episode_time:.1f}s / {max_time}s", 10, 50, font)
        draw_text(screen, "TAB=switch mode | R=reset | N=next scenario", 10, 70, font)
        if ego is not None:
            speed = getattr(ego, 'speed', 0)
            real_speed = speed * 10 # MULTIPLIER
            kmh = real_speed * 3.6

            draw_text(screen, f"Ego Speed: {speed:.2f} m/s ({kmh:.1f} km/h)", 10, 90, font)
            draw_text(screen, f"Ego Position: ({ego.x:.1f}, {ego.y:.1f}) m", 10, 110, font)