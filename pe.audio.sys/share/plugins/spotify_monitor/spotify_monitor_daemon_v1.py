#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A daemon that listen for GLib events from Spotify Desktop
    then writes down the metadata into a file for others to read it.
"""

#################### NOTICE ############################
# spotify_monitor_daemon_v1.py works with playerctl v0.x
########################################################

# CREDITS:
# Based on 'example.py' from https://github.com/acrisci/playerctl
# More info about interfacing with Spotify in Linux:
# https://wiki.archlinux.org/index.php/spotify

# Dependency: python-gi
# gi.repository is the Python module for PyGObject (which stands for Python GObject introspection)
# which holds Python bindings and support for the GTK+ 3 toolkit and for the GNOME apps.
# See https://wiki.gnome.org/Projects/PyGObject
# > apt list python-gi
# python-gi/xenial,now 3.20.0-0ubuntu1 amd64 [instalado, automático]
# > aptitude search python-gi
# i A python-gi                                 - Python 2.x bindings for gobject-introspection libra

# NOTICE: It is needed to have access to the desktop Dbus session.
# If you have access:
#   $ playerctl --list-all
#   spotify
# If you have not access:
#   $ playerctl --list-all
#   No players were found
#   $ dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause
#   Error org.freedesktop.DBus.Error.ServiceUnknown: The name org.mpris.MediaPlayer2.spotify was not provided by any .service files

# Playerctl is a MPRIS interface for desktop players:
import gi
gi.require_version('Playerctl', '1.0')
from gi.repository import Playerctl, GLib
import sys
import os
import json
from time import sleep

UHOME = os.path.expanduser("~")

##  events dumping file for pre.di.c's players.py reading from
events_file = f'{UHOME}/pe.audio.sys/.spotify_events'


def on_metadata(player, metadata):
    """ Handler functions when Spotify announces metadata.
        Dumps a json file containing spotify metadata extracted from gi.GLib
    """
    #print("on_metadata handler triggered")

    # metadata example:
    # {
    # 'mpris:trackid': <'spotify:track:0AvA3sGmYZRtlj1gV4RS9c'>,
    # 'mpris:length': <uint64 305000000>,
    # 'mpris:artUrl': <'https://open.spotify.com/image/48a93e16069610d640b7731cd677daa295ce74a0'>,
    # 'xesam:album': <'Part: Cello Concerto / Perpetuum Mobile / Symphonies No. 1, No. 2 and No. 3'>,
    # 'xesam:albumArtist': <['Arvo Pärt']>,
    # 'xesam:artist': <['Arvo Pärt']>,
    # 'xesam:autoRating': <0.040000000000000001>,
    # 'xesam:discNumber': <1>,
    # 'xesam:title': <'Pro et contra: I. Maestoso'>,
    # 'xesam:trackNumber': <1>,
    # 'xesam:url': <'https://open.spotify.com/track/0AvA3sGmYZRtlj1gV4RS9c'>
    # }

    # As per 'metadata' type is <class 'gi.overrides.GLib.Variant'>,
    # lets make a standard dictionary for json compatibility:
    d = {}
    for k in metadata.keys():
        d[k] = metadata[k]

    with open( events_file, 'w' ) as f:
        f.write( json.dumps( d ) )


def on_play(player):
    """ Handler function triggered when starting playing
    """
    #print("on_play handler triggered")
    pass


def on_pause(player):
    """ Handler function triggered when pausing playing
    """
    #print("on_pause handler triggered")
    pass


def main_loop():

    # Try to connect Spotify through by a Playerctl instance, which
    # is a dbus mpris interface to query some desktop player.
    tries = 10
    while tries:
        player = Playerctl.Player(player_name='spotify')
        if player.props.status:
            break
        tries -= 1
        sleep(1)

    if not tries:
        print( "(spotify_monitor_daemon_v1) Error connecting to Spotify Desktop" )
        sys.exit()

    # Events an handlers: player.on( eventID, handlerFunction )
    #player.on('play', on_play)
    #player.on('pause', on_pause)
    player.on('metadata', on_metadata)  # This is enough

    # Main loop waits for GLib events:
    loop = GLib.MainLoop()
    loop.run()


if __name__ == "__main__":

    if len(sys.argv) > 1:
        print( __doc__ )
        sys.exit()

    main_loop()
