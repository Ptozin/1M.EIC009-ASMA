import gym

class CustomLunarLander:
    def __init__(self, render_mode=None, **kwargs):
        """
        Initialize the LunarLander environment with custom parameters.
        
        Args:
            render_mode (str): Mode to render the environment. Defaults to None. Needs to be set to 'human' to render the environment.
            **kwargs: Additional parameters to customize the environment.
        """
        self.env = gym.make('LunarLander-v2', render_mode=render_mode)
        self.env.reset()
        
        self.__update_parameters(**kwargs)
    
    def __update_parameters(self, **kwargs):
        """
        Update the environment parameters.
        
        Args:
            **kwargs: Parameters to update the environment.
        """
        for key, value in kwargs.items():
            setattr(self.env, key, value)

    def reset(self):
        """
        Reset the environment.
        
        Returns:
            observation: The initial observation of the environment.
        """
        return self.env.reset()
    
    def step(self, action):
        """
        Take an action in the environment.
        
        Args:
            action: The action to take in the environment.
        
        Returns:
            tuple: The results of taking the action.
        """
        return self.env.step(action)
    
    def render(self):
        """
        Render the environment.
        """
        self.env.render()
    
    def close(self):
        """
        Close the environment.
        """
        self.env.close()
