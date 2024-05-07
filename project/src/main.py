import gym
from stable_baselines3 import PPO

env = gym.make('LunarLander-v2', render_mode='human')
env.reset()

model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=100000)

episodes = 10

for ep in range(episodes):
    obs = env.reset()
    done = False
    while not done:
        env.render()
        obs, rewards, done, info = env.step(env.action_space.sample())
        

env.close()