import docker

class ProsodyClient:
    """
    A class to interact with a Prosody instance running in a Docker container.
    
    Example of usage:
    ```py
    client = ProsodyClient(container_id="123456789abcdef")

    client.create_user("admin")
    ```
    """
    def __init__(self, container_id: str = "", domain: str = "localhost") -> None:
        self.client : docker.DockerClient = docker.from_env()

        if domain == "":
            raise ValueError("ProsodyClient: No domain provided.")
        
        self.domain : str = domain

        if container_id == '':
            print("Please provide the container ID or name of your Prosody instance.")
            print("These are the running containers:")
            print([f"{container.name}: {container.id}" for container in self.client.containers.list()])
            raise ValueError("ProsodyClient: No container ID provided.")

        self.container : docker.models.containers.Container = self.client.containers.get(container_id)

        ## Check if the container is running

        if self.container.status != "running":
            raise ValueError("ProsodyClient: Container is not running.")
        
        ## Print success message

        print(f"ProsodyClient: Successfuly connected to container {self.container.name}")

    def create_user(self, username: str = "", password: str = "admin") -> None:
        if username == "":
            print("ProsodyClient: Cannot create User - no username provided.")
            raise ValueError("ProsodyClient: No username provided.")
        
        command = f"prosodyctl about {username}@{self.domain}"
        exit_code, output = self.container.exec_run(command)
        if exit_code == 0:
            print(f"ProsodyClient: Cannot create User - `{username}` already exists.")
            return
        
        command = f"prosodyctl register {username} {self.domain} {password}"
        exit_code, output = self.container.exec_run(command)

        if exit_code == 0:
            print(f"ProsodyClient: User {username} created successfully.")
        else:
            print(f"ProsodyClient: Failed to create user {username}: {output.decode('utf-8')}")

"""
Example of usage:

client = ProsodyClient(container_id="{id}")

client.create_user("admin")
"""