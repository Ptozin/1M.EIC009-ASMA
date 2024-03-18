import json, pandas as pd
from create_user import ProsodyClient

def create_users(user_uids, container_id, prosody_password):
    """
    Creates users in prosody server if they don't exist already
    """
    with ProsodyClient(container_id) as prosody_client:
        for user_uid in user_uids:
            prosody_client.create_user(username=user_uid, password=prosody_password)

def main():
    try:
        # Read global variables
        with open('data/global_variables.json') as file:
            content = json.load(file)
            container_id = content['docker_container_id']
            prosody_password = content['prosody_password']
            print(container_id, prosody_password)

        # Read delivery drones agents
        content = pd.read_csv('data/delivery_drones.csv', delimiter=';')
        print(content)

        # Create users
        create_users(content['id'], container_id, prosody_password)
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()