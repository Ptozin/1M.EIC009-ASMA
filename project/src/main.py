import gym
from stable_baselines3 import PPO

env = gym.make('Blackjack-v1', render_mode='human')
env.reset()

# model = PPO("MlpPolicy", env, verbose=1)
# model.learn(total_timesteps=1000)

episodes = 10

for ep in range(episodes):
    obs = env.reset()
    done = False
    while not done:
        action, _states =  env.action_space.sample(), "" #model.predict(obs)
        obs, rewards, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        env.render()
        print(rewards)

    
env.close()