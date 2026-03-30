import unittest
import os
import tempfile
import json

from sim.entities import Car, Pedestrian
from sim.physics_engine import PhysicsEngine

# Import functions from your runner file
import scenario_runner_gui as main


class TestRunner(unittest.TestCase):

    # ==========================
    # SCENARIO LOADING
    # ==========================
    def test_load_all_scenarios_single_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp.write(b"[]")
            tmp_path = tmp.name

        files = main.load_all_scenarios(tmp_path)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], tmp_path)

        os.remove(tmp_path)

    def test_load_all_scenarios_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i in range(3):
                p = os.path.join(tmpdir, f"s{i}.json")
                with open(p, "w") as f:
                    json.dump([], f)
                paths.append(p)

            files = main.load_all_scenarios(tmpdir)
            self.assertEqual(len(files), 3)

    # ==========================
    # TRANSFORM SCENARIO
    # ==========================
    def test_transform_changes_velocity(self):
        entities = [
            Car({"type":"car","x":0,"y":0,"vx":10,"vy":0}),
            Pedestrian({"type":"pedestrian","x":10,"y":10,"vx":1,"vy":0})
        ]

        original = [(e.get_velocity() if e.type=="car" else (e.vx, e.vy)) for e in entities]

        new_entities = main.transform_scenario(entities)

        new = [(e.get_velocity() if e.type=="car" else (e.vx, e.vy)) for e in new_entities]

        self.assertNotEqual(original, new)

    # ==========================
    # CONTROL
    # ==========================
    def test_manual_control_keys(self):
        # simulate key array
        keys = [0] * 512

        keys[main.pygame.K_w] = 1
        keys[main.pygame.K_a] = 1

        steer, throttle, brake = main.manual_control(keys, None, 0)

        self.assertEqual(throttle, 1)
        self.assertEqual(steer, -1)
        self.assertEqual(brake, 0)

    def test_ai_policy(self):
        steer, throttle, brake = main.simple_ai_policy(None, [])
        self.assertEqual((steer, throttle, brake), (0,1,0))

    # ==========================
    # PHYSICS STEP (HEADLESS CORE)
    # ==========================
    def test_engine_step_moves_entities(self):
        car = Car({"type":"car","x":0,"y":0,"vx":10,"vy":0})
        engine = PhysicsEngine([car])

        x_before = car.x
        engine.step(0.1)
        x_after = car.x

        self.assertNotEqual(x_before, x_after)

    # ==========================
    # RESET SCENARIO
    # ==========================
    def test_reset_scenario(self):
        # create fake scenario
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump([{
                "type": "car",
                "x": 0,
                "y": 0,
                "vx": 10,
                "vy": 0,
                "heading": 0,
                "mass": 1500
            }], tmp)
            tmp_path = tmp.name

        main.scenario_files = [tmp_path]
        main.scenario_index = 0

        main.reset_scenario()

        self.assertIsNotNone(main.entities)
        self.assertIsNotNone(main.engine)

        os.remove(tmp_path)

    # ==========================
    # HEADLESS LOGGING
    # ==========================
    def test_log_headless_runs(self):
        # minimal setup
        main.ego = Car({"type":"car","x":0,"y":0,"vx":1,"vy":0})
        main.episode_time = 1.0
        main.scenario_index = 0

        # should not crash
        main.log_headless()


# ==========================
# RUN TESTS
# ==========================
if __name__ == "__main__":
    print("\nRunning Runner Tests...\n")
    unittest.main(verbosity=2)