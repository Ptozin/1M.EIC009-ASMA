import json
import gym
from environments.lunar_lander import CustomLunarLander
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder

def load_env_params(file_path):
    with open(file_path, "r") as file:
        env_params = json.load(file)['LunarLander-v2']
    return env_params
   
def record_video(model : PPO | A2C | DQN, video_length=1500, prefix="", video_folder="videos/", **env_params):
        eval_env = DummyVecEnv([lambda: gym.make("LunarLander-v2",
                                                 render_mode="rgb_array",
                                                 **env_params, # comment if needed
                                                 #gravity=-5, # uncomment if needed
                                                 #enable_wind=True, # uncomment if needed
                                                 #wind_power=20.0, # uncomment if needed
                                                 #turbulence_power=1.0, # uncomment if needed
                                            )])
        # Start the video at step=0 and record 1500 steps
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
            obs, _reward, _done, _info = eval_env.step(action)

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

def load_dqn_1(env_params, models_dir, time_step):
    model_path = f"{models_dir}/DQN_1/{time_step}.zip"
    env = CustomLunarLander(render_mode='human', **env_params)
    model = DQN.load(model_path, env=env.env)
    return model
 
if __name__ == "__main__":
    env_params = load_env_params("env_params.json")
    models_dir = "models"
    
    # Update this value to the timestep you want to load
    time_step = 2_000_000
    
    models = []
    
    # Append (model, prefix) tuple to models list
    models.append((load_ppo_0(env_params, models_dir, time_step), "ppo_0-LunarLander-default-2M"))
    models.append((load_ppo_1(env_params, models_dir, time_step), "ppo_1-LunarLander-default-2M"))
    models.append((load_a2c_0(env_params, models_dir, time_step), "a2c_0-LunarLander-default-2M"))
    models.append((load_dqn_0(env_params, models_dir, time_step), "dqn_0-LunarLander-default-2M"))
    models.append((load_dqn_1(env_params, models_dir, time_step), "dqn_1-LunarLander-default-2M"))
    
    for model, prefix in models:
        # Record 30 seconds of video
        record_video(model = model, video_length=1500, prefix=prefix, video_folder="videos/", **env_params)
