import docker

# Connect to Docker
client = docker.from_env()

container_id = ''
# container_id = "fbc55aad55f53f85f6e5b70012de22ff8200f1d36c24708ea0d8838da6c57f2d"

if container_id == '':
    print("Please provide the container ID or name of your Prosody instance.")
    exit(1)


# Find the Prosody container
container = client.containers.get(container_id)

username = "user_1"
domain = "localhost"
password = "admin"


# Assuming Prosody command-line tool is available within the container
# You may need to adjust this command based on how Prosody is installed
command = "prosodyctl register " + username + " " + domain + " " +  password

# Execute the command inside the container
exit_code, output = container.exec_run(command)

if exit_code == 0:
    print("User created successfully.")
else:
    print(f"Failed to create user: {output.decode('utf-8')}")
