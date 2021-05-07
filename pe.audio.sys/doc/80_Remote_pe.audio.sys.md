## Remote pe.audio.sys as local source

The file `share/scripts/zita_link.py` allows you to receive the listening source from a ***remote*** pe.audio.sys

#### Needed configuration inside the **RECEIVER** `config.yml`:

- Define the remote system as a local source. The source name must include the '**remote**' keyword, also use the *remote_IP* or *remote_hostname* for the `capture_port:` field:

    ```
    sources:
        ...
        ...
        remoteRemoteName:
            gain: 0
            capture_port:   192.168.1.123
    ```
    
- Include `zita_link.py` under the `scripts:` section:

    ```
    scripts:
        ...
        ...
        ## A LAN audio receiver
        - zita_link.py
    ```


#### Optional configuration inside the **SENDER** `config.yml`:

- Include `remote_volume_daemon.py` under your `scripts:` section:

    ```
    scripts:
        ...
        ...
        ## A volume forwarder to remote listeners
        - remote_volume_daemon.py
    ```

### Using a macro to balance delays for simultaneous listening

Just copy the the provided `macros/examples/X_remote_source.py` under your `macros/` folder.

Then customize the needed delays and filtering for the **local** and/or **remote** pe.audio.sys systems.

TIP: you can use any name for the macro file so that it will be meaningfully displayed in the web control page macro buttons, for instance:

    macros/04_Living_Room
    
    
