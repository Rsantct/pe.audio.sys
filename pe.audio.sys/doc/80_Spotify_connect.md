# Spotify connect client, AKA `librespot`

On a headless machine, we can use **`librespot`**, an Open Source Spotify client library.

(i) You need an **Spotify Premium account**

CREDITS: https://github.com/librespot-org/librespot

In order to customize the binary by having the **jackaudio** backend and by using the **Avahi/Bonjour** daemon from the O.S., we need to compile from source.

## Compile

### Install Rust Lang Compiler and dependencies

More info here: https://www.rust-lang.org/tools/install

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

Library dependencies:

    sudo apt install build-essential libasound2-dev libavahi-compat-libdnssd-dev pkg-config

### Low RAM systems

If you have <= 1Gb RAM, please increase your swap file to reach about 2 Gb (RAM + swap)

Instructions  Raspberry Pi OS:

    sudo dphys-swapfile swapoff
    sudo nano /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon

### Building

    cargo install --no-default-features --features "alsa-backend jackaudio-backend pulseaudio-backend with-dns-sd" librespot

This takes about 1/2 H in a Raspberry Pi 3+

The binary will be usually dropped under your cargo folder at `~/.cargo/bin/`


## Install

Simply copy or symlink the binary under `/usr/bin/`, for instance:

    ln -s  ~/.cargo/binlibrespot  /usr/bin/librespot


**Warning**: If you install the below referred librespot based package **`Raspotify`**, your /usr/bin/librespot will be overwritten.


## Pre-compiled package for Raspberry Pi

There is available a pre-compiled package called **`Raspotify`** for arm Raspberry users: raspotify https://github.com/dtcooper/raspotify

Please, after installing it, disable the default raspotify service

    sudo systemctl stop raspotify.service 
    sudo systemctl disable raspotify.service 


## Configure pe.audio.sys `config.yml`
    
    sources:
        ...
        ...
        spotify:
            jack_pname:     librespot_loop
            gain:           0.0
        ...
        ...
    
    scripts:
        ...
        ...
        # librespot (a headless Spotify Connect player daemon)
        - librespot.py
        ...
        ...

## Usage

You can control your headless Spotify player from any device in the same LAN (wifi), such an smartphone or tablet with the official Spotify App. Simply select your player by tapping the Soptify App icon *'Connect to device'*.

Unfortunately pe.audio.sys can not control the playback (play pause etc), this must be done from the Spotify App.

Currently, the only available metadata are the track title and duration. It is not available the track position, the album name, neither the artist name.
