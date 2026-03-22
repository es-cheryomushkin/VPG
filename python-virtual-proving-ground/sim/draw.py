import pygame
import math

def draw(screen, entities, ego, mode="manual", font=None, episode_time=0.0, max_time=10.0, scenario_index=0, show_eval=True):
    """
    Generic draw function usable by scenario creator or runner.
    """
    screen.fill((20,20,30))
    
    for e in entities:
        if e.type == "pedestrian":
            pygame.draw.circle(screen,(0,255,0),(int(e.x),int(e.y)),8)
        elif e.type == "car":
            color = (80,180,255) if e==ego else (200,50,50)
            
            # draw collision circles
            for cx, cy, r in e.circles():
                pygame.draw.circle(screen,(255,255,0),(int(cx),int(cy)),int(r),1)
            
            # rectangle covering circles
            rect_length = 2*e.front_offset
            rect_width = 2*e.radius
            rect_surf = pygame.Surface((rect_length, rect_width), pygame.SRCALPHA)
            pygame.draw.rect(rect_surf,(255,255,0,80),(0,0,rect_length,rect_width),2)
            rotated = pygame.transform.rotate(rect_surf,-math.degrees(e.heading))
            r = rotated.get_rect(center=(e.x,e.y))
            screen.blit(rotated,r)
            
            # heading arrow
            hx = e.x + math.cos(e.heading)*40
            hy = e.y + math.sin(e.heading)*40
            pygame.draw.line(screen,(255,255,0),(e.x,e.y),(hx,hy),2)
            
            # prediction arrow
            if e==ego and mode=="ai":
                px = e.x + math.cos(e.heading + getattr(e,'steer',0)*0.5)*60
                py = e.y + math.sin(e.heading + getattr(e,'steer',0)*0.5)*60
                pygame.draw.line(screen,(0,255,255),(e.x,e.y),(px,py),2)

    # UI overlay
    if font is not None:
        def draw_text(text,x,y):
            img = font.render(text,True,(255,255,255))
            screen.blit(img,(x,y))
        if show_eval:
            draw_text(f"Mode: {mode}",10,10)
            draw_text(f"Scenario: {scenario_index+1}",10,30)
            draw_text(f"Time: {episode_time:.1f}s / {max_time}s",10,50)
            draw_text("TAB=switch mode | R=reset | N=next scenario",10,70)
            score = getattr(ego,'speed',0)
            draw_text(f"Ego Eval Score: {score:.2f}",10,90)