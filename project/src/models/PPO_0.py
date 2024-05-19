import os
from stable_baselines3 import PPO
from . import ModelTrainer

class PPO_0(ModelTrainer):
    """
    Custom ModelTrainer class for the PPO model.
    Runs the default PPO model.
    """
    def __init__(self, env_params={}, model_dir="models/", log_dir="logs", timesteps=10000, total_iterations=30):
        """
        Initialize the ModelTrainer class.
        
        Args:
            env_params (dict): Parameters for the custom environment.
            model_dir (str): Directory to save the trained models.
            log_dir (str): Directory for logging.
            timesteps (int): Number of timesteps for each training iteration.
            total_iterations (int): Total number of training iterations.
        """
        super().__init__(env_params, timesteps, total_iterations)
        self.model_dir = model_dir + "PPO_0/"
        self.log_dir = log_dir
        self.timesteps = timesteps
        self.total_iterations = total_iterations
        self.tb_log_name = "PPO_0"

        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.model = PPO(
            'MlpPolicy', 
            self.env.env, 
            verbose=1, 
            tensorboard_log=self.log_dir
        )