import json
from environments.lunar_lander import CustomLunarLander
from stable_baselines3 import PPO

def load_env_params(file_path):
    with open(file_path, "r") as file:
        env_params = json.load(file)['LunarLander-v2']
    return env_params

def evaluate(env : CustomLunarLander, model : PPO, episodes = 10):
    for ep in range(episodes):
        cummulative_reward = 0
        obs, _ = env.reset()
        done = False
        while not done:
            action, _states = model.predict(obs)
            obs, rewards, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            env.render()
            cummulative_reward += rewards
            print(cummulative_reward)

    env.close()
    
def load_ppo_0(env_params, models_dir):
    model_path = f"{models_dir}/PPO_0/2000000.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = PPO.load(model_path, env=env.env)
    return env, model
 
if __name__ == "__main__":
    env_params = load_env_params("env_params.json")
    models_dir = "models"
    env, model = load_ppo_0(env_params, models_dir)
    
    evaluate(env, model)
