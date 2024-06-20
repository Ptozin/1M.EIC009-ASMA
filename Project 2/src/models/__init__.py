import os
from stable_baselines3 import PPO, A2C, DQN
from environments.lunar_lander import CustomLunarLander

class ModelTrainer:
    def __init__(self, env_params : dict = {}, timesteps : int = 10000, total_iterations : int = 30):
        """
        Initialize the ModelTrainer class.
        
        Args:
            env_params (dict): Parameters for the custom environment.
            model_dir (str): Directory to save the trained models.
            log_dir (str): Directory for logging.
            timesteps (int): Number of timesteps for each training iteration.
            total_iterations (int): Total number of training iterations.
        """
        self.env = CustomLunarLander(**env_params)
        self.timesteps = timesteps
        self.total_iterations = total_iterations
        
        # This is overwritten by the custom models
        self.model : PPO | A2C | DQN = None
        self.model_dir : str = None
        self.log_dir : str = None
        self.tb_log_name : str = None

    def train(self):
        """
        Train the model with the specified number of iterations.
        """
        for i in range(1, self.total_iterations + 1):
            self.model.learn(total_timesteps=self.timesteps, reset_num_timesteps=False, tb_log_name=self.tb_log_name)
            self.model.save(f"{self.model_dir}/{self.timesteps * i}")

    def evaluate(self, episodes=10):
        """
        Evaluate the trained model.
        
        Args:
            episodes (int): Number of episodes to evaluate the model.
        """
        for ep in range(episodes):
            obs = self.env.reset()
            done = False
            while not done:
                action, _states = self.model.predict(obs)
                obs, rewards, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                self.env.render()
                print(rewards)

        self.env.close()

if __name__ == "__main__":
    # Example usage
    env_params = {'render_mode': 'human'}
    trainer = ModelTrainer(env_params=env_params)
    trainer.train()
    trainer.evaluate()
