import math

# ==========================
# PHYSICS CONSTANTS
# ==========================
MULTIPLIER = 10.0

FRICTION_LINEAR = 0.98          # global drag
RESTIUTION = 0.03               # very low bounce (cars don't bounce)

MAX_IMPULSE = 6.0               # prevents explosions
POSITION_CORRECTION_PERCENT = 0.25
SLOP = 0.02                     # penetration tolerance

# Car stability tuning (VERY IMPORTANT)
LATERAL_FRICTION = 0.2          # kills sideways sliding
FORWARD_DAMPING = 0.995         # keeps forward motion stable


class PhysicsEngine:
    def __init__(self, entities):
        self.entities = entities
        self.time = 0.0
        self.last_collision = None

    # ==========================
    # MAIN STEP
    # ==========================
    def step(self, dt):
        self.handle_collisions()
        self.update_positions(dt)
        self.time += dt

    # ==========================
    # POSITION UPDATE
    # ==========================
    def update_positions(self, dt):
        for e in self.entities:
            vx, vy = self._get_velocity(e)

            e.x += vx * dt * MULTIPLIER
            e.y += vy * dt * MULTIPLIER

            # global damping
            vx *= FRICTION_LINEAR
            vy *= FRICTION_LINEAR

            self._set_velocity(e, vx, vy)

    # ==========================
    # COLLISIONS
    # ==========================
    def handle_collisions(self):
        n = len(self.entities)

        for i in range(n):
            for j in range(i + 1, n):
                self.collide(self.entities[i], self.entities[j])

    def collide(self, a, b):
        for ax, ay, ar in a.circles():
            for bx, by, br in b.circles():

                dx = bx - ax
                dy = by - ay
                dist = math.hypot(dx, dy)

                if dist == 0:
                    continue

                overlap = (ar + br) - dist
                if overlap <= 0:
                    continue

                nx = dx / dist
                ny = dy / dist

                avx, avy = self._get_velocity(a)
                bvx, bvy = self._get_velocity(b)

                # ==========================
                # VELOCITY DECOMPOSITION
                # ==========================
                av_n, av_tx, av_ty = self._decompose(avx, avy, nx, ny)
                bv_n, bv_tx, bv_ty = self._decompose(bvx, bvy, nx, ny)

                # relative normal velocity
                rel_n = av_n - bv_n

                # ignore tiny jitter collisions
                if rel_n > -0.5:
                    continue

                # ==========================
                # MASS
                # ==========================
                ma = max(a.mass / len(a.circles()), 1.0)
                mb = max(b.mass / len(b.circles()), 1.0)

                # ==========================
                # SOFT POSITION CORRECTION
                # ==========================
                correction = max(overlap - SLOP, 0.0)
                correction /= (1/ma + 1/mb)
                correction *= POSITION_CORRECTION_PERCENT

                cx = correction * nx
                cy = correction * ny

                a.x -= cx / ma
                a.y -= cy / ma
                b.x += cx / mb
                b.y += cy / mb

                # ==========================
                # IMPULSE (CLAMPED)
                # ==========================
                j = -(1 + RESTIUTION) * rel_n
                j = max(-MAX_IMPULSE, min(MAX_IMPULSE, j))

                impulse_a = j / ma
                impulse_b = j / mb

                av_n += impulse_a
                bv_n -= impulse_b

                # ==========================
                # RECONSTRUCT VELOCITY
                # ==========================
                avx = av_tx + av_n * nx
                avy = av_ty + av_n * ny

                bvx = bv_tx + bv_n * nx
                bvy = bv_ty + bv_n * ny

                # ==========================
                # CAR STABILITY FIX
                # (kills sideways chaos)
                # ==========================
                avx, avy = self._apply_car_stability(a, avx, avy)
                bvx, bvy = self._apply_car_stability(b, bvx, bvy)

                self._set_velocity(a, avx, avy)
                self._set_velocity(b, bvx, bvy)

                # ==========================
                # DEBUG LOG
                # ==========================
                self.last_collision = {
                    "impulse": j,
                    "overlap": overlap,
                    "entities": (a, b)
                }

    # ==========================
    # CAR STABILITY MODEL
    # ==========================
    def _apply_car_stability(self, e, vx, vy):
        if e.type != "car":
            return vx, vy

        # forward direction (car heading)
        fx = math.cos(e.heading)
        fy = math.sin(e.heading)

        # forward / lateral decomposition
        forward = vx * fx + vy * fy
        lateral = vx * (-fy) + vy * fx

        # kill sideways motion (tire grip model)
        lateral *= LATERAL_FRICTION

        # stabilize forward motion
        forward *= FORWARD_DAMPING

        # rebuild velocity
        vx = fx * forward - fy * lateral
        vy = fy * forward + fx * lateral

        return vx, vy

    # ==========================
    # HELPERS
    # ==========================
    def _decompose(self, vx, vy, nx, ny):
        normal = vx * nx + vy * ny
        tx = vx - normal * nx
        ty = vy - normal * ny
        return normal, tx, ty

    def _get_velocity(self, e):
        if e.type == "car":
            return e.get_velocity()
        return e.vx, e.vy

    def _set_velocity(self, e, vx, vy):
        if e.type == "car":
            e.set_velocity(vx, vy)
        else:
            e.vx = vx
            e.vy = vy