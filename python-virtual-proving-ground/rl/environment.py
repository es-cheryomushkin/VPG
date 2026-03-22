import math
import numpy as np

class DrivingEnv:

    def __init__(self, engine, ego):

        self.engine = engine
        self.ego = ego
        self.max_time = 10


    def step(self, action):

        steer, throttle, brake = action

        self.apply_action(steer, throttle, brake)

        self.engine.step(0.016)

        obs = self.get_observation()

        reward = self.compute_reward()

        done = self.engine.time > self.max_time

        return obs, reward, done


    def apply_action(self, steer, throttle, brake):

        self.ego.heading += steer * 0.05

        ax = math.cos(self.ego.heading) * throttle * 200
        ay = math.sin(self.ego.heading) * throttle * 200

        self.ego.vx += ax * 0.016
        self.ego.vy += ay * 0.016

        self.ego.vx *= (1 - brake*0.1)
        self.ego.vy *= (1 - brake*0.1)


    def get_observation(self):

        obs = []

        speed = math.hypot(self.ego.vx, self.ego.vy)
        obs.append(speed)

        for e in self.engine.entities:

            if e == self.ego:
                continue

            dx = e.x - self.ego.x
            dy = e.y - self.ego.y

            obs.append(dx)
            obs.append(dy)

        return np.array(obs)


    def compute_reward(self):

        return 0.01