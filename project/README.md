# Project 2: Reinforcement learning agents

## Group G2

| Name             | Number    | E-Mail             |
| ---------------- | --------- | ------------------ |
| Diogo Silva      | 202004288 | up202004288@edu.fe.up.pt   |
| João Araújo      | 202004293 | up202004293@edu.fe.up.pt   |

## Useful Information (TO REMOVE)

- [Gymnasium](https://gymnasium.farama.org)
- [YT Tutorials](https://www.youtube.com/watch?v=dLP-2Y6yu70&list=PLQVvvaa0QuDf0O2DWwLZBfJeYY-JOeZB1&index=2)
- [YT Tutorials - Site](https://pythonprogramming.net/saving-and-loading-reinforcement-learning-stable-baselines-3-tutorial/)
- [Pytorch Get Started](https://pytorch.org/get-started/locally/)
- [Stable Baseline 3 - Callbacks](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html#checkpointcallback)
    We will probably use CheckpointCallback to save the model every X steps, StopTrainingOnNoMoreImprovement to stop the training if the model doesn't improve for Y steps.

If you can't use the GPU to train the models by default, use this command if you want to install the pytorch library with GPU support (CUDA 12.1):
```bash
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

To visualize the training process, you can use the following command:
```bash
make tensorboard
```

Then, open [this](http://localhost:6006/?darkMode=true#scalars) link in your browser.
In order to see the updates in real-time, you should go to the `scalars` tab, then on `Settings`, enable the `Reload periodically` option and set the interval to 30 second.

### Description

You can find the project's description [here](description/assignment2.pdf).

### How to run

In order to run the project you should have python installed in your machine and the `uv` package in order to install the project's dependencies:
```bash
pip install uv
```

After that, you can run the project by executing the following command:
```bash
make

# wait for the dependencies to be installed in the .venv folder --

make run # to run the project
```
