## CamillaDSP

From version 2.0, we can use CamillaDSP, by now only used to provide an optional compressor.

The compressor is designed to facilitate the intelligibility of movies with difficult to hear  dialogues at low listening levels.


### Install CamillaDSP with the JACK backend

CamillaDSP pre-built binaries only provides ALSA or Pulseaudio backend. We need to compile our in order to include the **JACK audio backend**.

NOTE: do not need `sudo`, just complite under your pe.audio.sys regular Linux user.

#### Get the RUST compiler

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

#### Install compiler dependencies

    sudo apt-get install pkg-config libasound2-dev openssl libssl-dev \
                 jackd2 libjack-jackd2-dev

#### Get the CamillaDSP source code

https://github.com/HEnquist/camilladsp/releases


#### Compile

    RUSTFLAGS='-C target-feature=+neon -C target-cpu=native' \
    cargo build --release --features jack-backend

Finally, copy the binary to your `~/bin` folder, in order to be available for the pe.audio.sys scripts.

    cp target/release/camilladsp ~/bin/

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#building)

