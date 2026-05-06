from .simulation_state import SimulationState, load_current_scenario
from .sim.physics_engine import FIXED_DT, MAX_EPISODE_TIME

class DrivingEnv:
    def __init__(self, scenario_files):
        self.state = SimulationState()
        self.state.scenario_files = scenario_files
        self.reset()

    def reset(self):
        load_current_scenario(self.state)
        return self._get_obs()

    def step(self, action):
        steer, throttle, brake = action

        ego = self.state.controlledCar

        ego.update(throttle, brake, steer, FIXED_DT)
        self.state.engine.step(FIXED_DT)

        self.state.episode_time += FIXED_DT

        obs = self._get_obs()
        reward = self._get_reward()
        done = self._get_done()

        return obs, reward, done, {}

    def _get_obs(self):
        ego = self.state.controlledCar
        return [
            ego.x,
            ego.y,
            ego.speed,
            ego.heading
        ]

    def _get_reward(self):
        ego = self.state.controlledCar
        reward = ego.speed * 0.1

        if self.state.engine.last_collision:
            reward -= 10

        return reward

    def _get_done(self):
        if self.state.engine.last_collision:
            return True

        if self.state.episode_time > MAX_EPISODE_TIME:
            return True

        return False