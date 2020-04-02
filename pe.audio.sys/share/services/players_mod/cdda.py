#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

""" A module to manage CD-AUDIO
"""
# (i) I/O FILES MANAGED HERE:
#
# .cdda_info        'w'     CDDA album and tracks info in json format
#

import discid
import musicbrainzngs as mz
from os.path import expanduser
import json

UHOME = expanduser("~")

def cdda_meta_template():
    return {'artist':'n/a', 'album':'n/a',
            '1':{'title':'n/a', 'length':'00:00.00'} }

def msec2string(msec):
    """ input:  millisecs  (float)
        output: 'mm:ss.cc' (str)
    """
    sec  = msec / 1e3
    mm   = f'{sec // 60:.0f}'.zfill(2)
    ss   = f'{sec %  60:.2f}'.zfill(5)
    return f'{mm}:{ss}'

def get_disc_metadata(device):

    md = cdda_meta_template()

    mz.set_useragent('tmp', '0.1', 'dummy@mail')

    try:
        disc = discid.read(device)
    except:
        print('(cdaa.py) not CDDA found')
        return md

    try:
        result = mz.get_releases_by_discid( disc.id,
                                      includes=['artists','recordings'] )
    except mz.ResponseError:
        print('(cdda.py) disc not found or bad response')
        return md


    if result.get('disc'):
        print('(cdda.py) musicbrainz got \'disc\'' )
        mz_md = result['disc']['release-list'][0]
        md['artist'] = mz_md['artist-credit-phrase']
        md['album']  = mz_md['title']
        track_list   = mz_md['medium-list'][0]['track-list']

    elif result.get('cdstub'):
        print('(musicbrainz) got \'cdstub\'' )
        mz_md = result['cdstub']
        md['artist'] = mz_md['artist-credit-phrase']
        md['album']  = mz_md['title']
        track_list   = []

    for track in track_list:
        lenghtStr = msec2string( float(track['recording']['length']) )
        md[ track['position'] ] = {'title':  track['recording']['title'],
                                   'length': lenghtStr}

    return md

def save_disc_metadata(device, fname=f'{UHOME}/pe.audio.sys/.cdda_info'):
    with open(fname, 'w') as f:
        f.write( json.dumps( get_disc_metadata(device) ) )
