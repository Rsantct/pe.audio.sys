#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A module to manage CD-AUDIO
"""
# (i) I/O FILES MANAGED HERE:
#
# .cdda_info        'w'     CDDA album and tracks info in json format.
#
#   Example:
#
#   {   'artist': 'xxxx',
#        'album': 'xxxx',
#            '1': { 'title': 'xxxx', 'length': 'mm:ss.cc' }
#            '2': { ... ...
#            ...
#   }
#

import  musicbrainzngs as mz
import  json
import  sys
from    os.path import expanduser

UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    config import CONFIG, CDDA_INFO_PATH
from    fmt    import Fmt

try:
    import  discid
except Exception as e:
    print(str(e))
    print(f'{Fmt.BOLD}{Fmt.BLINK}Have you activated your Python Virtual Environment?{Fmt.END}')



## cdrom device to use
if 'cdrom_device' in CONFIG:
    CDROM_DEVICE = CONFIG['cdrom_device']
else:
    CDROM_DEVICE = '/dev/cdrom'
    print(f'{Fmt.BLUE}(cdda.py) Using default \'{CDROM_DEVICE}\'{Fmt.END}')

# cd port under Jack
try:
    CD_JACK_PNAME = CONFIG['sources']['cd']['jack_pname']
except:
    CD_JACK_PNAME = 'mplayer_cdda'

# cdda info template with a fake track #1
CDDA_INFO_TEMPLATE = { 'discid':'', 'artist': '-', 'album': '-',
                       '1':      {'title': '-', 'length': '00:00.00'}
                     }


def mmsscc2msec(mmsscc):
    """ input:   'mm:ss.cc' (str)
        output:  millisecs  (int)
    """
    mm   = int( mmsscc.split(':')[0] )
    sscc =      mmsscc.split(':')[1]
    ss   = int( sscc.split('.')[0]   )
    cc   = int( sscc.split('.')[1]   )

    millisec = mm * 60 * 1000 + ss * 1000 + cc * 10

    return millisec


def msec2string(msec):
    """ input:  millisecs  (float)
        output: 'mm:ss.cc' (str)
    """
    sec  = msec / 1e3
    mm   = f'{sec // 60:.0f}'.zfill(2)
    ss   = f'{sec %  60:.2f}'.zfill(5)
    return f'{mm}:{ss}'


def read_disc_metadata(device=CDROM_DEVICE):

    def simple_md(disc):
        """ For disc not found, we can derive the tracks and tracks length
            from the 'disc' object properties.
        """
        print( f'(cdda.py) {disc.last_track_num} tracks found on discid \'{disc.id}\'' )
        # https://musicbrainz.org/doc/Development/XML_Web_Service/Version_2#discid
        # The toc consists of the following:
        #   First track (always 1)
        #   total number of tracks
        #   sector offset of the leadout (end of the disc
        #   a list of sector offsets for each track, beginning with track 1 (generally 150 sectors)
        #
        # Example of TOC for a 7 tracks disc:
        # disc.toc_string: '1 7 235745 150 40742 77847 108042 118682 154277 191952'
        toc = disc.toc_string.split()

        # A second of CD-AUDIO has 75 frames (or sectors) -wikipedia-
        track_sectors = toc[3:] + [toc[2]]
        track_sectors = [int(x) for x in track_sectors]
        for i in range(len(track_sectors)):
            if i == 0:
                continue
            trackNum = i
            trackLen = ( track_sectors[i] - track_sectors[i - 1] ) / 75
            md[str(trackNum)] = {'title': 'track ' + f'{trackNum}'.zfill(2),
                                 'length': msec2string(trackLen * 1e3)}

        return md

    # will complete md with info retrieved from musicbrainz
    md = CDDA_INFO_TEMPLATE.copy()

    mz.set_useragent('tmp', '0.1', 'dummy@mail')

    try:
        disc = discid.read(device)
        md['discid'] = disc.id
        global CDDA_DISCID
        CDDA_DISCID  = disc.id
    except:
        print('(cdaa.py) not CDDA found')
        return md

    try:
        result = mz.get_releases_by_discid( disc.id,
                                      includes=['artists', 'recordings'] )
    except Exception as e:
        print(f'{Fmt.BOLD}(cdda.py) disc not found or bad response: {str(e)}{Fmt.END}')
        return simple_md(disc)

    # most of discs are 'disc' musicbrainz kinf of
    if result.get('disc'):

        print(f'(cdda.py) musicbrainz got \'disc\': {disc.id}' )

        mz_md = result['disc']['release-list'][0]

        md['artist'] = mz_md['artist-credit-phrase']

        md['album']  = mz_md['title']

        track_list   = mz_md['medium-list'][0]['track-list']

    # but somo are 'cdstub' musicbrainz kind of
    elif result.get('cdstub'):

        print(f'(cdda.py) musicbrainz got \'cdstub\': {disc.id}' )

        mz_md = result['cdstub']

        if 'artist' in mz_md:
            md['artist'] = mz_md['artist']
        elif 'artist-credit-phrase' in mz_md:
            md['artist'] = mz_md['artist-credit-phrase']

        if 'title' in mz_md:
            md['album']  = mz_md['title']

        # (!) pending on investigate more on tracks under 'cdstub'
        if 'track-list' in mz_md:
            track_list   = mz_md['track-list']
        else:
            track_list   = []

    # Lets complete our track list structure inside the 'md' template
    for pos, track in enumerate( track_list ):

        # Retrieve track length
        # from normal 'disc':
        if 'recording' in track and 'length' in track['recording']:
            lengthStr = msec2string( float(track['recording']['length']) )
        # from some 'cdstub':
        elif 'length' in track:
            lengthStr = msec2string( float(track['length']) )
        # from some 'cdstub':
        elif 'track_or_recording_length' in track:
            lengthStr = msec2string( float(track['track_or_recording_length']) )
        else:
            lengthStr = msec2string( 0.0 )

        # Retrieve track title
        if 'recording' in track and 'title' in track['recording']:
            track_title = track['recording']['title']
        elif 'title' in track:
            track_title = track['title']

        # adding to our metadata disc structure
        md[ str(pos + 1) ] = { 'title':  track_title,
                               'length': lengthStr }

    return md


def save_disc_metadata(device=CDROM_DEVICE):
    with open(CDDA_INFO_PATH, 'w') as f:
        f.write( json.dumps( read_disc_metadata(device) ) )


def make_pls():

    md = read_disc_metadata()

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

    md = read_disc_metadata()

    m3u =   '#EXTM3U\n'

    for k in md.keys():

        if not k.isdigit():
            continue

        durationms = mmsscc2msec( md[k]["length"] )
        durationsec = str( int(round( durationms / 1e3, 0)) )

        m3u += '#EXTINF:'
        m3u += f'{durationsec},'
        m3u += f'{md[k]["title"]}\n'
        m3u += f'cdda:/{CDROM_DEVICE}/{k}\n'

    return m3u


def save_cdda_playlist(mode='m3u'):
    """ Saves a playlist for MPD :-)
    """
    folder = f'{UHOME}/.config/mpd/playlists'
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
