
## December 18, 2020: version 1.0 released

- `share/eq/*.dat` files has changed its internal arrangement
- Equal loudness related commands and parameters has changed

See the `doc/` folder for detailed information about this.

**PLEASE UPDATE:**

- your `share/eq/*.dat` files with the new ones
  provided under `share/eq/eq.sample.R20_audiotools/`


- your `config.yml`:

    ```
                        refSPL=XX       (new item)
    loud_ceil       --> eq_loud_ceil
    loudness_track  --> equal_loudness
    ```

- your `.state.yml`:

    ```
    loudness_track:  --> equal_loudness: true|false
    loudness_ref:    --> lu_offset: XX
    ```

- your `macros/` files if them issue any loudness command
