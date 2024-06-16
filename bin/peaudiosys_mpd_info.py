#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A command line MPD audio info tool
"""
import mpd


if __name__ == "__main__":

    c = mpd.MPDClient()
    c.connect('localhost', 6600)

    s = c.status()

    res = f'state:   { s["state"] }'

    if 'bitrate' in s:
        res += f'\nbitrate: { s["bitrate"] }'

    if 'audio' in s:
        res += f'\nformat:  { s["audio"] }'

    print(res)
