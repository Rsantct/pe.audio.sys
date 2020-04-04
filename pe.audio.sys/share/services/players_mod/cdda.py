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
import yaml
import sys

UHOME = expanduser("~")

## cdrom device to use
try:
    with open(f'{UHOME}/pe.audio.sys/config.yml', 'r') as f:
        PEASYSCONFIG = yaml.safe_load(f)
    CDROM_DEVICE = PEASYSCONFIG['cdrom_device']
except:
    CDROM_DEVICE = '/dev/cdrom'
    print(f'(cdda.py) Using default \'{CDROM_DEVICE}\'')


def cdda_meta_template():
    return {'artist':'-', 'album':'-',
            '1':{'title':'-', 'length':'00:00.00'} }

def mmsscc2msec(mmsscc):
    """ input:   'mm:ss.cc' (str)
        output:  millisecs  (int)
    """
    mm   = int( mmsscc.split(':')[0] )
    sscc =      mmsscc.split(':')[1]
    ss   = int( sscc.split('.')[0]   )
    cc   = int( sscc.split('.')[1]   )

    millisec = mm*60*1000 + ss*1000 + cc*10

    return millisec

def msec2string(msec):
    """ input:  millisecs  (float)
        output: 'mm:ss.cc' (str)
    """
    sec  = msec / 1e3
    mm   = f'{sec // 60:.0f}'.zfill(2)
    ss   = f'{sec %  60:.2f}'.zfill(5)
    return f'{mm}:{ss}'

def get_disc_metadata(device=CDROM_DEVICE):

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
        print(f'(cdda.py) musicbrainz got \'disc\': {disc.id}' )
        mz_md = result['disc']['release-list'][0]
        md['artist'] = mz_md['artist-credit-phrase']
        md['album']  = mz_md['title']
        track_list   = mz_md['medium-list'][0]['track-list']

    elif result.get('cdstub'):
        print(f'(cdda.py) musicbrainz got \'cdstub\': {disc.id}' )
        mz_md = result['cdstub']
        md['artist'] = mz_md['artist-credit-phrase']
        md['album']  = mz_md['title']
        track_list   = []

    for track in track_list:
        lenghtStr = msec2string( float(track['recording']['length']) )
        md[ track['position'] ] = {'title':  track['recording']['title'],
                                   'length': lenghtStr}

    return md

def save_disc_metadata(device=CDROM_DEVICE,
                       fname=f'{UHOME}/pe.audio.sys/.cdda_info'):
    with open(fname, 'w') as f:
        f.write( json.dumps( get_disc_metadata(device) ) )

def make_pls():

    md = get_disc_metadata()

    pls =   '<?xml version="1.0" encoding="UTF-8"?>\n'
    pls +=  '<playlist version="1" xmlns="http://xspf.org/ns/0/">\n'
    pls +=  '  <trackList>\n'

    for k in md.keys():

        if not k.isdigit():
            continue

        duration = mmsscc2msec( md[k]["length"] )

        pls +=  '    <track>\n'
        pls += f'      <location>cdda:///{k}</location>\n'
        pls += f'      <creator>{md["artist"]}</creator>\n'
        pls += f'      <album>{md["album"]}</album>\n'
        pls += f'      <title>{md[k]["title"]}</title>\n'
        pls += f'      <duration>{duration}</duration>\n'
        pls +=  '    </track>\n'

    pls +=  '  </trackList>\n'
    pls +=  '</playlist>\n'

    return pls

def make_m3u():

    md = get_disc_metadata()

    m3u =   '#EXTM3U\n'

    for k in md.keys():

        if not k.isdigit():
            continue

        durationms = mmsscc2msec( md[k]["length"] )
        durationsec = str( int(round( durationms/1e3, 0)) )

        m3u += '#EXTINF:'
        m3u += f'{durationsec},'
        m3u += f'{md[k]["title"]}\n'
        m3u += f'cdda:/{CDROM_DEVICE}/{k}\n'

    return m3u

def save_cdda_playlist(mode='m3u'):
    """ Saves a playlist for MPD :-)
    """
    folder= f'{UHOME}/.config/mpd/playlists'
    if mode == 'm3u':
        tmp = make_m3u()
        fname = f'{folder}/.cdda.m3u'
    elif mode == 'pls':
        tmp = make_pls()
        fname = f'{folder}/.cdda.pls'
    else:
        return
    with open(f'{fname}', 'w') as f:
        f.write(tmp)

if __name__ == "__main__":
    if sys.argv[1:] and '-s' in sys.argv[1]:
        save_cdda_playlist()
