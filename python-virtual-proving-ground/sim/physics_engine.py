# physics_engine.py
import math

# Movement
MULTIPLIER = 10.0
FRICTION = 0.998

# Impact
DAMPING = 0.2
FRICTION_TANGENT = 1
IMPACT_DAMPING = 0.8  # 0.0 = no loss, 1.0 = full stop



class PhysicsEngine:

    def __init__(self, entities):
        self.entities = entities
        self.time = 0

    def step(self, dt):
        self.handle_collisions()
        for e in self.entities:
            if e.type == "car":
                vx, vy = e.get_velocity()
            else:
                vx, vy = e.vx, e.vy

            e.x += vx * dt * MULTIPLIER
            e.y += vy * dt * MULTIPLIER

            # friction
            vx *= FRICTION
            vy *= FRICTION

            if e.type == "car":
                e.set_velocity(vx, vy)
            else:
                e.vx = vx
                e.vy = vy

        self.time += dt

    def handle_collisions(self):
        n = len(self.entities)
        for i in range(n):
            for j in range(i+1, n):
                self.collide(self.entities[i], self.entities[j])

    def collide(self, a, b):
        ac = a.circles()
        bc = b.circles()

        ma = a.mass / len(ac)
        mb = b.mass / len(bc)

        for ax, ay, ar in ac:
            for bx, by, br in bc:

                dx = bx - ax
                dy = by - ay
                dist = math.hypot(dx, dy)

                if dist == 0:
                    continue

                overlap = ar + br - dist
                if overlap <= 0:
                    continue

                # ===== NORMAL =====
                nx = dx / dist
                ny = dy / dist

                # ===== VELOCITIES =====
                avx, avy = (a.get_velocity() if a.type=="car" else (a.vx, a.vy))
                bvx, bvy = (b.get_velocity() if b.type=="car" else (b.vx, b.vy))

                relvx = avx - bvx
                relvy = avy - bvy

                rel = relvx * nx + relvy * ny

                if rel > 2.0:
                    continue

                impact_speed = abs(rel)

                # ===== POSITION CORRECTION =====
                percent = 0.8
                slop = 0.01

                correction = max(overlap - slop, 0) / (1/ma + 1/mb) * percent

                cx = correction * nx
                cy = correction * ny

                a.x -= cx / ma
                a.y -= cy / ma
                b.x += cx / mb
                b.y += cy / mb

                # ===== SPLIT VELOCITY =====

                # normal
                an = avx * nx + avy * ny
                bn = bvx * nx + bvy * ny

                anx = nx * an
                any = ny * an

                bnx = nx * bn
                bny = ny * bn

                # tangent
                atx = avx - anx
                aty = avy - any

                btx = bvx - bnx
                bty = bvy - bny

                # ===== CRASH RESPONSE =====

                head_on = abs(rel) / (math.hypot(relvx, relvy) + 1e-5)

                kill = IMPACT_DAMPING * head_on

                # kill normal velocity
                an *= (1 - kill)
                bn *= (1 - kill)

                # ===== MOMENTUM TRANSFER (important fix) =====
                total_m = ma + mb

                new_an = (ma * an + mb * bn) / total_m
                new_bn = new_an

                anx = nx * new_an
                any = ny * new_an

                bnx = nx * new_bn
                bny = ny * new_bn

                # ===== SMALL DEFLECTION =====
                deflect = 0.15 * impact_speed

                anx -= ny * deflect / ma
                any += nx * deflect / ma

                bnx += ny * deflect / mb
                bny -= nx * deflect / mb

                # ===== RECOMBINE =====
                new_avx = anx + atx
                new_avy = any + aty

                new_bvx = bnx + btx
                new_bvy = bny + bty

                # ===== APPLY =====
                if a.type == "car":
                    a.set_velocity(new_avx, new_avy)
                else:
                    a.vx, a.vy = new_avx, new_avy

                if b.type == "car":
                    b.set_velocity(new_bvx, new_bvy)
                else:
                    b.vx, b.vy = new_bvx, new_bvy

                # ===== LOG =====
                crash_energy = 0.5 * (ma + mb) * (impact_speed ** 2)
                print("Collision at:", ax, ay)
                self.last_collision = {
                    "speed": impact_speed,
                    "energy": crash_energy,
                    "entities": (a, b)
                }