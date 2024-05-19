import gym
from stable_baselines3 import PPO

models_dir = "models/PPO"

env = gym.make('LunarLander-v2', render_mode='human')
env.reset()

model_path = f"{models_dir}/290000.zip"
model = PPO.load(model_path, env=env)

episodes = 5

for ep in range(episodes):
    obs, _info = env.reset()
    done = False
    while not done:
        action, _states = model.predict(obs)
        obs, rewards, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        env.render()
        
env.close()