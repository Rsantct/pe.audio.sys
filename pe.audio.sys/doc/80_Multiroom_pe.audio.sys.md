## Listen to a remote pe.audio.sys

The file `share/scripts/zita_link.py` allows you to receive the listening source from a ***remote*** pe.audio.sys


### (Needed) Configuration inside the **RECEIVER** `config.yml`:

- Include `zita_link.py` under the `scripts:` section:

    ```
    scripts:
        ...
        ...
        ## A LAN audio receiver
        - zita_link.py
    ```

- Define the remote system as a local source.
    
    - The source name must include the **`remote`** keyword
    - Put the remote **`IP:CTRLPORT`** (default control port is 9990) in the `jack_pname:` field

Example:

    ```
    sources:
        ...
        ...
        remoteLivingRoom:
            gain:       0
            jack_pname: 192.168.1.XXX
    ```
    
The `zita_link.py` script will autospawn a new jack port named `zita_n2j_XXX`

### (Optional) Configuration inside the **SENDER** `config.yml`:

- Include `remote_volume_daemon.py` under your `scripts:` section:

    ```
    scripts:
        ...
        ...
        ## A volume forwarder to remote listeners
        - remote_volume_daemon.py
    ```

### Using a macro to balance latencies for simultaneous listening

Depending on the processing latency on both the local and the remote pe.audio.sys systems, you may want to customize added delays and/or filtering options.

Just copy the the provided `macros/examples/X_RemoteSource` under your `macros/` folder.

Then customize the macro with the needed delays and filtering alternatives for the **local** and/or **remote** pe.audio.sys systems.

TIP: you can use any name for the macro file so that it will be meaningfully displayed in the web control page macro buttons, for instance:

    macros/04_Living_Room
    
    
