# Project 1: Multi-agent delivery system using drones

## Group G2

| Name             | Number    | E-Mail             |
| ---------------- | --------- | ------------------ |
| Diogo Silva      | 202004288 | up202004288@edu.fe.up.pt   |
| João Araújo      | 202004293 | up202004293@edu.fe.up.pt   |

### Description

You can find the project's description [here](description/trabalho1.pdf).

### How to run

*Assuming that docker pyenv is already fully setup*

Please alter the file `data/global_variables.json` with the correct container id for the prosody server. It should look something like this:

```json
{
    "docker_container_id": "123456789abcdef",
    "prosody_password": "admin"
}
```

Then, in order to run the project you should have python installed in your machine and the `uv` package in order to install the project's dependencies:
```bash
pip install uv
```

After that, you can run the project by executing the following command:
```bash
make

# wait for the dependencies to be installed in the .venv folder --

make run # to run the project

make visualization # visualize the simulation in the browser on a map
```

