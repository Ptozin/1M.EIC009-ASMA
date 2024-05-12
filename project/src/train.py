import gym
from stable_baselines3 import PPO
import os

# TODO: this is still a work in progress

models_dir = "models/PPO"
logdir = "logs"

os.makedirs(models_dir, exist_ok=True)

os.makedirs(logdir, exist_ok=True)

env = gym.make('LunarLander-v2')
env.reset()

model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=logdir)

TIMESTEPS = 10000
iters = 0
for i in range(1, 31):
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name="PPO")
    model.save(f"{models_dir}/{TIMESTEPS*i}")