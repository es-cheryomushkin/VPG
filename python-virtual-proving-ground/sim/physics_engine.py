# physics_engine.py
import math

# ==========================
# PHYSICS CONSTANTS
# ==========================
MULTIPLIER = 10.0      # Scaling factor for motion, brings speed units to metres/second
FRICTION = 0.998       # Global friction for velocity damping

IMPACT_DAMPING = 0.8   # Fraction of normal velocity lost during impact
FRICTION_TANGENT = 1   # Tangential friction (not fully used)
DAMPING = 0.2          # Unused general damping constant


class PhysicsEngine:
    """
    Simple physics engine handling motion and collisions for cars and pedestrians.
    """
    def __init__(self, entities):
        self.entities = entities
        self.time = 0
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
        """
        Move entities based on their velocities and apply friction.
        """
        for e in self.entities:
            vx, vy = e.get_velocity() if e.type == "car" else (e.vx, e.vy)

            # Update position
            e.x += vx * dt * MULTIPLIER
            e.y += vy * dt * MULTIPLIER

            # Apply friction
            vx *= FRICTION
            vy *= FRICTION

            # Set updated velocity
            if e.type == "car":
                e.set_velocity(vx, vy)
            else:
                e.vx, e.vy = vx, vy

    # ==========================
    # COLLISION HANDLING
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
        """
        Handle collision between two entities using circle approximation.
        """
        a_circles = a.circles()
        b_circles = b.circles()

        mass_a = a.mass / len(a_circles)
        mass_b = b.mass / len(b_circles)

        for ax, ay, ar in a_circles:
            for bx, by, br in b_circles:
                dx = bx - ax
                dy = by - ay
                dist = math.hypot(dx, dy)

                if dist == 0:
                    continue

                overlap = ar + br - dist
                if overlap <= 0:
                    continue

                # ===== NORMAL VECTOR =====
                nx, ny = dx / dist, dy / dist

                # ===== RELATIVE VELOCITY =====
                avx, avy = a.get_velocity() if a.type == "car" else (a.vx, a.vy)
                bvx, bvy = b.get_velocity() if b.type == "car" else (b.vx, b.vy)

                relvx = avx - bvx
                relvy = avy - bvy
                rel_normal = relvx * nx + relvy * ny

                if rel_normal > 2.0:
                    continue  # Skip fast separating entities

                # ===== POSITION CORRECTION =====
                self._position_correction(a, b, nx, ny, overlap, mass_a, mass_b)

                # ===== VELOCITY RESPONSE =====
                self._velocity_response(a, b, nx, ny, avx, avy, bvx, bvy, mass_a, mass_b, rel_normal)

    # ==========================
    # POSITION CORRECTION
    # ==========================
    def _position_correction(self, a, b, nx, ny, overlap, ma, mb):
        """
        Push entities apart based on overlap.
        """
        percent = 0.8  # usually 20% slack
        slop = 0.01    # small tolerance

        correction = max(overlap - slop, 0) / (1 / ma + 1 / mb) * percent
        cx = correction * nx
        cy = correction * ny

        a.x -= cx / ma
        a.y -= cy / ma
        b.x += cx / mb
        b.y += cy / mb

    # ==========================
    # VELOCITY RESPONSE
    # ==========================
    def _velocity_response(self, a, b, nx, ny, avx, avy, bvx, bvy, ma, mb, rel_normal):
        """
        Apply collision response including momentum transfer, damping, and small deflection.
        """
        # Skip separating
        if rel_normal > 0:
            return

        # ===== RESTITUTION (bounciness) =====
        restitution = 0.1  # 0 = no bounce, 1 = perfect bounce

        # ===== IMPULSE =====
        j = -(1 + restitution) * rel_normal
        j /= (1 / ma + 1 / mb)

        ix = j * nx
        iy = j * ny

        # Apply impulse
        avx += ix / ma
        avy += iy / ma

        bvx -= ix / mb
        bvy -= iy / mb

        # ===== TANGENTIAL FRICTION =====
        tx = -ny
        ty = nx

        rel_t = (avx - bvx) * tx + (avy - bvy) * ty

        friction = 0.5  # tune this

        jt = -rel_t
        jt /= (1 / ma + 1 / mb)
        jt *= friction

        fx = jt * tx
        fy = jt * ty

        avx += fx / ma
        avy += fy / ma

        bvx -= fx / mb
        bvy -= fy / mb

        # ===== APPLY =====
        if a.type == "car":
            a.set_velocity(avx, avy)
        else:
            a.vx, a.vy = avx, avy

        if b.type == "car":
            b.set_velocity(bvx, bvy)
        else:
            b.vx, b.vy = bvx, bvy

        # ===== LOG =====
        impact_speed = abs(rel_normal)
        crash_energy = 0.5 * (ma + mb) * (impact_speed ** 2)

        self.last_collision = {
            "speed": impact_speed,
            "energy": crash_energy,
            "entities": (a, b)
        }