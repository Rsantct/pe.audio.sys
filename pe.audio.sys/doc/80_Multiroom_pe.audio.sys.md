## Listen to a remote pe.audio.sys

_pe.audio.sys_ integrates an automatic point-to-point LAN audio connection based on **zita-njbridge by Fons Adriaensen**.

You can listen to **one or more remote** _pe.audio.sys_


### (Needed) Configuration inside the **RECEIVER** `config.yml`:

Define the remote system as a local source.

- The source name must include the **`remote`** keyword
- Put the remote **`IP:CTRLPORT`** (default control port is 9990) in the `jack_pname:` field

Example:

    sources:
        ...
        ...
        remoteLivingRoom:
            gain:       0
            jack_pname: 192.168.1.XXX

_pe.audio.sys_ will do automagically:

- Autospawn a new local **jack port** named **`zita_n2j_XXX`**

- Run a remote `zita-j2n` process on the remote machine, pointing to our local one.


### (Optional) Configuration inside the **SENDER** `config.yml`:

- Include `remote_volume_daemon.py` under their `plugins:` section:

    ```
    plugins:
        ...
        ...
        ## A volume forwarder to remote listeners
        - remote_volume_daemon.py
    ```

NOTICE: In order to link the listener volume and LU offset with the sender ones, the listening machine must send a `hello` command. See more details under `macros/examples/X_RemoteSource`

### Using a macro to balance latencies for simultaneous listening

Depending on the processing latency on both the local and the remote pe.audio.sys systems, you may want to customize added delays and/or filtering options.

Just copy the the provided `macros/examples/X_RemoteSource` under your `macros/` folder.

Then customize the macro with the needed delays and filtering alternatives for the **local** and/or **remote** _pe.audio.sys_ systems.

TIP: you can use any name for the macro file so that it will be meaningfully displayed in the web control page macro buttons, for instance:

    macros/04_Living_Room


