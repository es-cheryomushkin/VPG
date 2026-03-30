import math
import unittest

from sim.entities import Car, Pedestrian
from sim.physics_engine import PhysicsEngine


# ==========================
# HELPERS
# ==========================
def make_car(x=0, y=0, vx=0, vy=0, mass=1000):
    return Car({
        "type": "car",
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "heading": math.atan2(vy, vx) if (vx or vy) else 0,
        "mass": mass
    })


def make_ped(x=0, y=0, vx=0, vy=0):
    return Pedestrian({
        "type": "pedestrian",
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "mass": 80
    })


# ==========================
# TEST CLASS
# ==========================
class TestPhysicsEngine(unittest.TestCase):

    # --------------------------
    # BASIC MOTION
    # --------------------------
    def test_entity_moves_forward(self):
        car = make_car(vx=10, vy=0)
        engine = PhysicsEngine([car])

        engine.step(1.0)

        self.assertGreater(car.x, 0)
        self.assertAlmostEqual(car.y, 0, places=5)

    def test_friction_reduces_speed(self):
        car = make_car(vx=10, vy=0)
        engine = PhysicsEngine([car])

        speed_before = car.speed
        engine.step(1.0)
        speed_after = car.speed

        self.assertLess(speed_after, speed_before)

    # --------------------------
    # COLLISIONS
    # --------------------------
    def test_head_on_collision_reduces_speed(self):
        car1 = make_car(x=0, y=0, vx=10, vy=0)
        car2 = make_car(x=10, y=0, vx=-10, vy=0)

        engine = PhysicsEngine([car1, car2])
        engine.step(0.1)

        self.assertLess(car1.speed, 9)
        self.assertLess(car2.speed, 9)

    def test_rear_collision_pushes_forward(self):
        car1 = make_car(x=0, y=0, vx=20, vy=0)
        car2 = make_car(x=10, y=0, vx=5, vy=0)

        engine = PhysicsEngine([car1, car2])
        engine.step(0.1)

        self.assertGreater(car2.speed, 5)

    def test_collision_creates_log(self):
        car1 = make_car(x=0, y=0, vx=10, vy=0)
        car2 = make_car(x=10, y=0, vx=-10, vy=0)

        engine = PhysicsEngine([car1, car2])
        engine.step(0.1)

        self.assertIsNotNone(engine.last_collision)
        self.assertIn("speed", engine.last_collision)
        self.assertIn("energy", engine.last_collision)

    # --------------------------
    # MULTI-CIRCLE CAR
    # --------------------------
    def test_car_has_two_collision_circles(self):
        car = make_car()
        circles = car.circles()

        self.assertEqual(len(circles), 2)

    def test_rear_circle_collision_detected(self):
        car1 = make_car(x=0, y=0, vx=0, vy=0)
        car2 = make_car(x=-20, y=0, vx=10, vy=0)

        engine = PhysicsEngine([car1, car2])
        engine.step(0.2)

        self.assertIsNotNone(engine.last_collision)

    # --------------------------
    # PEDESTRIAN
    # --------------------------
    def test_car_hits_pedestrian(self):
        car = make_car(x=0, y=0, vx=10, vy=0)
        ped = make_ped(x=20, y=0)

        engine = PhysicsEngine([car, ped])
        engine.step(0.1)

        self.assertEqual(abs(ped.vx), 0.0)

    # --------------------------
    # STABILITY
    # --------------------------
    def test_no_nan_velocities(self):
        car1 = make_car(x=0, y=0, vx=10, vy=0)
        car2 = make_car(x=30, y=0, vx=-10, vy=0)

        engine = PhysicsEngine([car1, car2])
        engine.step(0.1)

        for e in [car1, car2]:
            vx, vy = e.get_velocity()
            self.assertFalse(math.isnan(vx))
            self.assertFalse(math.isnan(vy))

    def test_no_sticking_after_collision(self):
        car1 = make_car(x=0, y=0, vx=10, vy=0)
        car2 = make_car(x=30, y=0, vx=-10, vy=0)

        engine = PhysicsEngine([car1, car2])

        engine.step(0.1)
        pos_after_1 = (car1.x, car1.y)

        engine.step(0.1)
        pos_after_2 = (car1.x, car1.y)

        self.assertNotEqual(pos_after_1, pos_after_2)


# ==========================
# RUN TESTS
# ==========================
if __name__ == "__main__":
    print("\nRunning Physics Engine Tests...\n")
    unittest.main(verbosity=2)