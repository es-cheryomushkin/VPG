import unittest
import math

from sim.entities import BaseEntity, Car, Pedestrian


# =========================
# BASE ENTITY TESTS
# =========================
class TestBaseEntity(unittest.TestCase):

    def test_initialization(self):
        data = {"type": "test", "x": 10, "y": 20}
        e = BaseEntity(data)

        self.assertEqual(e.x, 10)
        self.assertEqual(e.y, 20)
        self.assertEqual(e.mass, 1)
        self.assertEqual(e.type, "test")

    def test_velocity_get_set(self):
        e = BaseEntity({"type": "test", "x": 0, "y": 0})

        e.set_velocity(3, 4)  # speed should be 5
        vx, vy = e.get_velocity()

        self.assertAlmostEqual(e.speed, 5)
        self.assertAlmostEqual(vx, 3, places=4)
        self.assertAlmostEqual(vy, 4, places=4)

    def test_default_circle(self):
        e = BaseEntity({"type": "test", "x": 5, "y": 6})
        circles = e.circles()

        self.assertEqual(len(circles), 1)
        cx, cy, r = circles[0]

        self.assertEqual(cx, 5)
        self.assertEqual(cy, 6)
        self.assertEqual(r, e.radius)


# =========================
# CAR TESTS
# =========================
class TestCar(unittest.TestCase):

    def test_initialization(self):
        data = {
            "type": "car",
            "x": 0,
            "y": 0,
            "vx": 3,
            "vy": 4,
            "heading": 0
        }
        car = Car(data)

        self.assertAlmostEqual(car.speed, 5)
        self.assertEqual(car.length, 50)
        self.assertEqual(car.width, 20)

    def test_velocity_consistency(self):
        car = Car({"type": "car", "x": 0, "y": 0})

        car.set_velocity(10, 0)
        vx, vy = car.get_velocity()

        self.assertAlmostEqual(vx, 10)
        self.assertAlmostEqual(vy, 0)

    def test_update_acceleration(self):
        car = Car({"type": "car", "x": 0, "y": 0})

        car.update(throttle=1, brake=0, steer=0, dt=1.0)

        self.assertGreater(car.speed, 0)

    def test_update_braking(self):
        car = Car({"type": "car", "x": 0, "y": 0, "vx": 10, "vy": 0})

        initial_speed = car.speed
        car.update(throttle=0, brake=1, steer=0, dt=1.0)

        self.assertLess(car.speed, initial_speed)

    def test_turning_changes_heading(self):
        car = Car({"type": "car", "x": 0, "y": 0})

        initial_heading = car.heading
        car.update(throttle=1, brake=0, steer=0.5, dt=1.0)

        self.assertNotEqual(car.heading, initial_heading)

    def test_circles_count(self):
        car = Car({"type": "car", "x": 0, "y": 0})

        circles = car.circles()
        self.assertEqual(len(circles), 2)

    def test_circles_positions(self):
        car = Car({"type": "car", "x": 0, "y": 0, "heading": 0})

        circles = car.circles()

        front = circles[0]
        rear = circles[1]

        # front should be +x direction
        self.assertGreater(front[0], 0)
        self.assertLess(rear[0], 0)


# =========================
# PEDESTRIAN TESTS
# =========================
class TestPedestrian(unittest.TestCase):

    def test_initialization(self):
        ped = Pedestrian({"type": "pedestrian", "x": 0, "y": 0})

        self.assertEqual(ped.radius, 8)

    def test_update_motion(self):
        ped = Pedestrian({
            "type": "pedestrian",
            "x": 0,
            "y": 0,
            "vx": 1,
            "vy": 2
        })

        ped.update(dt=1.0)

        self.assertEqual(ped.x, 1)
        self.assertEqual(ped.y, 2)

    def test_circles(self):
        ped = Pedestrian({"type": "pedestrian", "x": 5, "y": 6})

        circles = ped.circles()
        self.assertEqual(len(circles), 1)

        cx, cy, r = circles[0]
        self.assertEqual(cx, 5)
        self.assertEqual(cy, 6)
        self.assertEqual(r, ped.radius)


# =========================
# RUN TESTS
# =========================
if __name__ == "__main__":
    print("\nRunning Physics Engine Tests...\n")
    unittest.main(verbosity=2)