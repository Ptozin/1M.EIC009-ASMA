import json
import multiprocessing
import signal
import sys
import torch
from models.PPO_0 import PPO_0 as Trainer_PPO_0
from models.A2C_0 import A2C_0 as Trainer_A2C_0
from models.DQN_0 import DQN_0 as Trainer_DQN_0
from models.PPO_1 import PPO_1 as Trainer_PPO_1

def load_env_params(file_path):
    with open(file_path, "r") as file:
        env_params = json.load(file)['LunarLander-v2']
    return env_params

# Computing on GPU (if possible)
def get_default_device():
    """Pick GPU if available, else CPU"""
    if torch.cuda.is_available():
        print("Using GPU as default device")
        return torch.device('cuda')
    else:
        print("Using CPU as default device")
        return torch.device('cpu')

def train_model(trainer_class, env_params):
    trainer = trainer_class(env_params=env_params, total_iterations=100)
    trainer.train()

def signal_handler(sig, frame):
    print("Stopping all processes...")
    for process in processes:
        process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    get_default_device()
    
    signal.signal(signal.SIGINT, signal_handler)

    env_params = load_env_params("env_params.json")
    
    trainers = [
        Trainer_PPO_0,
        Trainer_A2C_0,
        Trainer_DQN_0,
        Trainer_PPO_1
    ]
    
    processes = []
    
    for trainer_class in trainers:
        process = multiprocessing.Process(target=train_model, args=(trainer_class, env_params))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()
