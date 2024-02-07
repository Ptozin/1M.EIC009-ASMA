## How to run Prosody

Run the `run.bat` file on this current folder. It will start the Prosody server. If you encounter this issue:
    
```
*certmanager* **error** SSL/TLS: Failed to load '/etc/prosody/certs/localhost.key': Check that the permissions allow Prosody to read this file. (for localhost)
```

Please run the `fix.bat` with the following command after accessing the docker container:

```sh
chown -R prosody /etc/prosody/
```

Afterwards just restart and it should all be done.