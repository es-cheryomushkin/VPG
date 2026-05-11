import math

# ==========================
# PHYSICS CONSTANTS
# ==========================
MULTIPLIER = 10.0

FRICTION_LINEAR = 1.0           # global drag
RESTIUTION = 0.03               # very low bounce (cars don't bounce)

MAX_IMPULSE = 6.0               # prevents explosions
POSITION_CORRECTION_PERCENT = 0.25
SLOP = 0.02                     # penetration tolerance

# Car stability tuning (VERY IMPORTANT)
LATERAL_FRICTION = 0.2          # kills sideways sliding
FORWARD_DAMPING = 0.995         # keeps forward motion stable

IMPACT_DAMPING = 0.7
COLLISION_FRICTION = 0.8
RESTIUTION = 0.0

# ego car
MAX_FORWARD_SPEED = 25.0
MAX_REVERSE_SPEED = -8.0

REVERSE_STABILITY = 0.5     # less grip when reversing
SPIN_DAMPING = 0.7         # kills sudden flips

class PhysicsEngine:
    def __init__(self, entities):
        self.entities = entities
        self.time = 0.0
        self.last_collision = None

    # ==========================
    # MAIN STEP
    # ==========================
    def step(self, dt):
        """
        Advance simulation by dt seconds.
        Handles collisions first, then moves all entities and applies friction.
        """
        self.handle_collisions()
        self.update_positions(dt)
        self.time += dt

    # ==========================
    # POSITION UPDATE
    # ==========================
    def update_positions(self, dt):
        for e in self.entities:
            vx, vy = self._get_velocity(e)

            # Update position
            e.x += vx * dt * MULTIPLIER
            e.y += vy * dt * MULTIPLIER

            # global damping
            vx *= FRICTION_LINEAR
            vy *= FRICTION_LINEAR

            self._set_velocity(e, vx, vy)

    def apply_vehicle_dynamics(self, dt):
        for e in self.entities:

            if e.type != "car":
                continue

            vx, vy = e.get_velocity()

            fx = math.cos(e.heading)
            fy = math.sin(e.heading)

            # =========================================
            # FORWARD VELOCITY
            # =========================================
            forward_speed = vx * fx + vy * fy * MULTIPLIER

            # =========================================
            # ENGINE FORCE
            # =========================================
            engine_accel = 12.0
            brake_accel = 20.0

            accel = e.throttle * engine_accel

            # braking opposes motion
            if abs(forward_speed) > 0.1:
                accel -= math.copysign(
                    e.brake * brake_accel,
                    forward_speed
                )
            else:
                accel -= e.brake * brake_accel

            # =========================================
            # APPLY ACCELERATION
            # =========================================
            forward_speed += accel * dt

            # =========================================
            # DRAG
            # =========================================
            drag = 0.4
            forward_speed *= (1.0 - drag * dt)

            # =========================================
            # SPEED LIMITS
            # =========================================
            max_forward = 30.0
            max_reverse = -10.0

            forward_speed = max(
                max_reverse,
                min(max_forward, forward_speed)
            )

            # =========================================
            # STEERING
            # =========================================
            steer_angle = e.steer * 0.6

            if abs(steer_angle) > 0.001:

                turn_radius = e.wheelbase / math.tan(steer_angle)

                angular_velocity = forward_speed / turn_radius

                e.heading += angular_velocity * dt

            # =========================================
            # REBUILD VELOCITY VECTOR
            # =========================================
            vx = math.cos(e.heading) * forward_speed
            vy = math.sin(e.heading) * forward_speed

            e.set_velocity(vx, vy)


    # ==========================
    # COLLISIONS
    # ==========================
    def handle_collisions(self):
        """
        Check all entity pairs for collisions and apply response.
        """
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
                # NORMAL IMPULSE
                # ==========================
                j = -(1 + RESTIUTION) * rel_n
                j /= (1/ma + 1/mb)

                j = max(-MAX_IMPULSE, min(MAX_IMPULSE, j))

                impulse_a = j / ma
                impulse_b = j / mb

                av_n += impulse_a
                bv_n -= impulse_b

                # ==========================
                # TANGENTIAL (FRICTION) IMPULSE
                # ==========================
                # relative tangential velocity
                rel_tx = av_tx - bv_tx
                rel_ty = av_ty - bv_ty

                jt = -(rel_tx * nx + rel_ty * ny)  # projected tangential magnitude
                jt /= (1/ma + 1/mb)

                # Coulomb-style friction clamp
                jt = max(-j * COLLISION_FRICTION, min(j * COLLISION_FRICTION, jt))

                # apply friction impulse
                av_tx += jt * nx / ma
                av_ty += jt * ny / ma

                bv_tx -= jt * nx / mb
                bv_ty -= jt * ny / mb

                # ==========================
                # IMPACT DAMPING (VERY IMPORTANT)
                # ==========================
                av_n *= IMPACT_DAMPING
                bv_n *= IMPACT_DAMPING

                # ==========================
                # RECONSTRUCT VELOCITY
                # ==========================
                avx = av_tx + av_n * nx
                avy = av_ty + av_n * ny

                bvx = bv_tx + bv_n * nx
                bvy = bv_ty + bv_n * ny

                # ==========================
                # CAR STABILITY FIX
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

        # forward direction
        fx = math.cos(e.heading)
        fy = math.sin(e.heading)

        # decompose velocity
        forward = vx * fx + vy * fy
        lateral = vx * (-fy) + vy * fx

        # ==========================
        # SPEED CLAMP (VERY IMPORTANT)
        # ==========================
        if forward > MAX_FORWARD_SPEED:
            forward = MAX_FORWARD_SPEED
        if forward < MAX_REVERSE_SPEED:
            forward = MAX_REVERSE_SPEED

        # ==========================
        # REVERSE HANDLING
        # ==========================
        if forward < 0:
            # less grip when reversing (prevents spin flips)
            lateral *= LATERAL_FRICTION * REVERSE_STABILITY

            # extra damping so it doesn't "whip"
            forward *= FORWARD_DAMPING * SPIN_DAMPING
        else:
            # normal forward driving
            lateral *= LATERAL_FRICTION
            forward *= FORWARD_DAMPING

        # ==========================
        # REBUILD VELOCITY
        # ==========================
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