# entities.py
import math

# =========================
# BASE ENTITY
# =========================
class BaseEntity:
    """
    Base class for all entities in the simulation.
    """
    def __init__(self, data):
        self.type = data["type"]
        self.mass = data.get("mass", 1)
        self.x = data["x"]
        self.y = data["y"]
        self.vx = data.get("vx", 0)
        self.vy = data.get("vy", 0)
        self.heading = data.get("heading", 0)
        self.radius = 8
        self.front_offset = 8  # default for circles
        self.rear_offset = 8
        self.speed = math.hypot(self.vx, self.vy)
    
        self.length = 10
        self.width = 10
        self.wheelbase = 10
        self.steer = 0

    def update(self, *args, **kwargs):
        # base entity does nothing
        pass

    def circles(self):
        # default circle for collision
        return [(self.x, self.y, self.radius)]
    
    def get_velocity(self):
        return (math.cos(self.heading) * self.speed, math.sin(self.heading) * self.speed)

    def set_velocity(self, vx, vy):
        self.speed = math.hypot(vx, vy)
        if self.speed > 0:
            self.heading = math.atan2(vy, vx)

    def circles(self):
        return [(self.x, self.y, self.radius)]


# =========================
# CAR
# =========================
class Car(BaseEntity):
    """
    Car model with temporary internal kinematics and circular collision geometry.
    """
    def __init__(self, data):
        super().__init__(data)
        self.speed = math.hypot(self.vx, self.vy)

        # geometry
        self.length = 50
        self.width = 20
        self.wheelbase = 40

        # collision
        self.radius = 20
        self.front_offset = 15
        self.rear_offset = 15

        # control state
        self.steer = 0

    def update(self, throttle, brake, steer, dt):
        # should be moved to physics module, but for now it's here for simplicity
        # steering smoothing
        self.steer += (steer - self.steer) * 5 * dt

        # acceleration
        accel = 80 * throttle - 200 * brake
        self.speed += accel * dt

        # drag
        self.speed *= 0.995

        # turning
        if abs(self.steer) > 0.01:
            turn_radius = self.wheelbase / math.tan(self.steer)
            angular_velocity = self.speed / turn_radius
        else:
            angular_velocity = 0

        self.heading += angular_velocity * dt

        # update position
        self.x += math.cos(self.heading) * self.speed * dt
        self.y += math.sin(self.heading) * self.speed * dt

    def get_velocity(self):
        return (math.cos(self.heading) * self.speed, math.sin(self.heading) * self.speed)

    def set_velocity(self, vx, vy):
        self.speed = math.hypot(vx, vy)
        if self.speed > 0:
            self.heading = math.atan2(vy, vx)

    def circles(self):
        dx = math.cos(self.heading) * self.front_offset
        dy = math.sin(self.heading) * self.front_offset
        return [
            (self.x + dx, self.y + dy, self.radius),
            (self.x - dx, self.y - dy, self.radius)
        ]


# =========================
# PEDESTRIAN
# =========================
class Pedestrian(BaseEntity):
    """
    Simple entity representing a pedestrian, with a single circular collision shape.
    """
    def __init__(self, data):
        super().__init__(data)
        self.radius = 8

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def circles(self):
        return [(self.x, self.y, self.radius)]