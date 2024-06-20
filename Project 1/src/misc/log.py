import logging


class Logger:
    def __init__(self, *, filename : str) -> None:
        self.logger = logging.getLogger(filename)
        filepath = "logs/" + filename + ".log"
        
        handler = logging.FileHandler(filepath)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, message):
        self.logger.info(message)    