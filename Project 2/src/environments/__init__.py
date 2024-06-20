import gym
from gym import spaces

# TODO: this is still a work in progress

class CustomEnv(gym.Env):
    def __init__(self):
        super(CustomEnv, self).__init__()
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=0, high=1, shape=(1,))

    def reset(self):
        return [0]

    def step(self, action):
        return [0], 0, True, {}

    def render(self, mode='human'):
        pass

    def close(self):
        pass