import multiprocessing as mp
import time
import random

from sim.entities import Car, Pedestrian
from sim.physics_engine import PhysicsEngine
from sim.scenario_loader import load_scenario


# ==========================
# ENVIRONMENT WORKER
# ==========================
def env_worker(pipe, scenario_files, max_time, fixed_dt):
    """
    A single simulation environment running in its own process.
    Communicates via a Pipe.
    """
    parent_conn, child_conn = pipe
    parent_conn.close()

    scenario_index = 0

    def load_env():
        nonlocal scenario_index

        path = scenario_files[scenario_index]
        entities, ego = load_scenario(path)

        # Convert to objects
        new_entities = []
        new_ego = None

        for e in entities:
            if e.type == "car":
                obj = Car(e.__dict__)
                if e == ego:
                    new_ego = obj
            elif e.type == "pedestrian":
                obj = Pedestrian(e.__dict__)
            else:
                obj = e

            new_entities.append(obj)

        engine = PhysicsEngine(new_entities)

        return new_entities, new_ego, engine

    entities, ego, engine = load_env()
    episode_time = 0.0

    while True:
        cmd, data = child_conn.recv()

        if cmd == "step":
            steer, throttle, brake = data

            ego.update(throttle, brake, steer, fixed_dt)
            engine.step(fixed_dt)

            episode_time += fixed_dt

            # ===== OBSERVATION =====
            obs = {
                "ego_x": ego.x,
                "ego_y": ego.y,
                "speed": ego.speed
            }

            # ===== REWARD (example) =====
            reward = ego.speed * fixed_dt

            done = False

            # collision penalty
            if engine.last_collision:
                reward -= 10.0
                done = True

            # timeout
            if episode_time > max_time:
                done = True

            if done:
                scenario_index = (scenario_index + 1) % len(scenario_files)
                entities, ego, engine = load_env()
                episode_time = 0.0

            child_conn.send((obs, reward, done))

        elif cmd == "reset":
            entities, ego, engine = load_env()
            episode_time = 0.0

            obs = {
                "ego_x": ego.x,
                "ego_y": ego.y,
                "speed": ego.speed
            }

            child_conn.send(obs)

        elif cmd == "close":
            child_conn.close()
            break


# ==========================
# VECTOR ENV MANAGER
# ==========================
class VectorEnv:
    def __init__(self, scenario_files, num_envs=4, max_time=10.0, fixed_dt=1/60):
        self.num_envs = num_envs
        self.processes = []
        self.pipes = []

        for _ in range(num_envs):
            parent_conn, child_conn = mp.Pipe()

            proc = mp.Process(
                target=env_worker,
                args=((parent_conn, child_conn), scenario_files, max_time, fixed_dt)
            )
            proc.start()

            child_conn.close()

            self.processes.append(proc)
            self.pipes.append(parent_conn)

    def step(self, actions):
        """
        actions: list of (steer, throttle, brake)
        """
        for pipe, action in zip(self.pipes, actions):
            pipe.send(("step", action))

        results = [pipe.recv() for pipe in self.pipes]

        obs, rewards, dones = zip(*results)
        return list(obs), list(rewards), list(dones)

    def reset(self):
        for pipe in self.pipes:
            pipe.send(("reset", None))

        obs = [pipe.recv() for pipe in self.pipes]
        return obs

    def close(self):
        for pipe in self.pipes:
            pipe.send(("close", None))

        for p in self.processes:
            p.join()

if __name__ == "__main__":
    from scenario_runner_gui import load_all_scenarios

    scenario_files = load_all_scenarios("scenarios")

    env = VectorEnv(scenario_files, num_envs=4)

    obs = env.reset()

    for step in range(1000):
        actions = []

        for o in obs:
            # random policy (replace with NN later)
            action = (
                random.uniform(-1, 1),  # steer
                random.uniform(0, 1),   # throttle
                random.uniform(0, 1)    # brake
            )
            actions.append(action)

        obs, rewards, dones = env.step(actions)

        print(f"Step {step}, reward={rewards}")

    env.close()