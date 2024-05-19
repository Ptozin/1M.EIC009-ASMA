import json
import gym
from environments.lunar_lander import CustomLunarLander
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder

def load_env_params(file_path):
    with open(file_path, "r") as file:
        env_params = json.load(file)['LunarLander-v2']
    return env_params

def evaluate(env : CustomLunarLander, model : PPO | A2C | DQN, episodes = 10):
    for ep in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _states = model.predict(obs)
            obs, rewards, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            env.render()
            print(rewards)

    env.close()

   
def record_video(model, video_length=500, prefix="", video_folder="videos/", **env_params):
        eval_env = DummyVecEnv([lambda: gym.make("LunarLander-v2",
                                                 render_mode="rgb_array",
                                                 **env_params)])
        # Start the video at step=0 and record 500 steps
        eval_env = VecVideoRecorder(
            eval_env,
            video_folder=video_folder,
            record_video_trigger=lambda step: step == 0,
            video_length=video_length,
            name_prefix=prefix,
        )

        obs = eval_env.reset()
        for _ in range(video_length):
            action, _ = model.predict(obs)
            obs, _reward, _truncated, _info = eval_env.step(action)

        # Close the video recorder
        eval_env.close()
        
def load_ppo_0(env_params, models_dir, time_step):
    model_path = f"{models_dir}/PPO_0/{time_step}.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = PPO.load(model_path, env=env.env)
    return model

def load_ppo_1(env_params, models_dir, time_step):
    model_path = f"{models_dir}/PPO_0/{time_step}.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = PPO.load(model_path, env=env.env)
    return model

def load_a2c_0(env_params, models_dir, time_step):
    model_path = f"{models_dir}/A2C_0/{time_step}.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = A2C.load(model_path, env=env.env)
    return model

def load_dqn_0(env_params, models_dir, time_step):
    model_path = f"{models_dir}/DQN_0/{time_step}.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = DQN.load(model_path, env=env.env)
    return model
 
if __name__ == "__main__":
    env_params = load_env_params("env_params.json")
    
    models_dir = "models"
    time_step = 1000_000
    
    models = []
    
    models.append((load_dqn_0(env_params, models_dir, time_step), "ppo_0-LunarLander"))
    models.append((load_a2c_0(env_params, models_dir, time_step), "ppo_1-LunarLander"))
    models.append((load_ppo_0(env_params, models_dir, time_step), "a2c_0-LunarLander"))
    models.append((load_ppo_1(env_params, models_dir, time_step), "dqn_0-LunarLander"))
    
    for model, prefix in models:
        record_video(model = model, video_length=1500, prefix=prefix, video_folder="videos/", **env_params)
        #evaluate(env, model)
