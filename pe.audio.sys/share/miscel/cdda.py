#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" A module to manage CD-AUDIO
"""

import  musicbrainzngs as mz
import  json
import  sys
import  os
from    miscel import CONFIG, CDDA_INFO_PATH, CDDA_INFO_TEMPLATE, \
                      Fmt, msec2str, read_mpd_config

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


UHOME                 = os.path.expanduser("~")
CDDA_MUSICBRAINZ_PATH = f'{UHOME}/pe.audio.sys/.cdda_musicbrainz'

# (i) I/O FILES MANAGED HERE:
#
# pe.audio.sys/.cdda_info           CDDA album and tracks info in json format for players use
# pe.audio.sys/.cdda_musicbrainz    dump file with no use
# MPD_playlist_folder/cdda.m3u      M3U CD playlist to be loaded from MPD


def _get_disc_metadata(device=CDROM_DEVICE):

    def find_medium_list_idx(disc_id, medium_list_items):
        """
            Double CD sets, will have several medium-list items
            and we need to choose the one matching our disc.id
        """

        idx = 0

        for i, item in enumerate(medium_list_items):

            for dl_item in item["disc-list"]:

                if disc_id==dl_item["id"]:

                    idx = i
                    break

        return idx


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

            md["tracks"][str(trackNum)] = {'title': 'track ' + f'{trackNum}'.zfill(2),
                                 'length': msec2str(trackLen * 1e3)}

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
        print(f'{Fmt.RED}(cdaa.py) not CDDA found{Fmt.END}')
        return md

    try:
        result = mz.get_releases_by_discid( disc.id,
                                      includes=['artists', 'recordings'] )
        with open(CDDA_MUSICBRAINZ_PATH, 'w') as f:
            f.write( json.dumps( result ) )
        print(f'{Fmt.BLUE}(cdda.py) Full musicbrainz CD data saved to {CDDA_MUSICBRAINZ_PATH}{Fmt.END}')

    except Exception as e:
        print(f'{Fmt.BOLD}(cdda.py) disc not found or bad response: {str(e)}{Fmt.END}')
        return simple_md(disc)

    # most of discs are 'disc' musicbrainz kinf of
    if result.get('disc'):

        print(f'{Fmt.BLUE}(cdda.py) musicbrainz got \'disc\': {disc.id}{Fmt.END}' )

        mz_md = result['disc']['release-list'][0]

        md['artist'] = mz_md['artist-credit-phrase']

        md['album']  = mz_md['title']

        # (!) Double CD sets, will have several medium-list
        medium_list_idx = find_medium_list_idx( disc.id, mz_md['medium-list'] )

        track_list   = mz_md['medium-list'][medium_list_idx]['track-list']

    # but somo are 'cdstub' musicbrainz kind of
    elif result.get('cdstub'):

        print(f'(cdda.py) musicbrainz got \'cdstub\': {disc.id}' )

        mz_md = result['cdstub']

        # JUST MAKE A SIMPLE MD
        return simple_md(disc)

        # NOT USED BECAUSE FAKE DATA
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
            lengthStr = msec2str( float(track['recording']['length']) )

        # from some 'cdstub':
        elif 'length' in track:
            lengthStr = msec2str( float(track['length']) )

        # from some 'cdstub':
        elif 'track_or_recording_length' in track:
            lengthStr = msec2str( float(track['track_or_recording_length']) )
        else:
            lengthStr = msec2str( 0.0 )

        # Retrieve track title
        if 'recording' in track and 'title' in track['recording']:
            track_title = track['recording']['title']

        elif 'title' in track:
            track_title = track['title']

        # Some track names can contain the album title, this is redundant
        if md["album"] in track_title:
            track_title = track_title.replace(md["album"], '')
            if track_title[0] in (':', ',', '.'):
                track_title = track_title[1:].strip()

        # adding to our metadata disc structure
        md["tracks"][ str(pos + 1) ] = { 'title':  track_title,
                               'length': lengthStr }

    return md


def _save_cdda_playlist(md={}, mode='m3u'):
    """ Saves a playlist for MPD :-)
        (PLS mode is not tested)
    """

    def make_m3u(md):

        m3u =   '#EXTM3U\n'

        for k, v in md["tracks"].items():

            durationms = msec2str( string=v["length"] )
            durationsec = str( int(round( durationms / 1e3, 0)) )

            m3u += '#EXTINF:'
            m3u += f'{durationsec},'
            m3u += f'{v["title"]}\n'
            m3u += f'cdda:/{CDROM_DEVICE}/{k}\n'

        return m3u


    def make_pls(md):

        pls =   '<?xml version="1.0" encoding="UTF-8"?>\n'
        pls +=  '<playlist version="1" xmlns="http://xspf.org/ns/0/">\n'
        pls +=  '  <trackList>\n'

        for k, v in md["tracks"].items():

            duration = msec2str( string=v["length"] )

            pls +=  '    <track>\n'
            pls += f'      <location>cdda:///{k}</location>\n'
            pls += f'      <creator>{md["artist"]}</creator>\n'
            pls += f'      <album>{md["album"]}</album>\n'
            pls += f'      <title>{v["title"]}</title>\n'
            pls += f'      <duration>{duration}</duration>\n'
            pls +=  '    </track>\n'

        pls +=  '  </trackList>\n'
        pls +=  '</playlist>\n'

        return pls


    if mode == 'm3u':
        tmp = make_m3u( md )
        fname = f'{ read_mpd_config()["playlist_directory"] }/cdda.m3u'

    elif mode == 'pls':
        tmp = make_pls( md )
        fname = f'{ read_mpd_config()["playlist_directory"] }/cdda.pls'

    else:
        return

    with open(f'{fname}', 'w') as f:
        f.write(tmp)

    print(f'{Fmt.BLUE}(cdda.py) MPD CD playlist saved to {fname}{Fmt.END}')



def dump_cdda_metadata(device=CDROM_DEVICE):
    """ dump CD-Audio disc matadata to:

            pe.audio.sys/.cdda_info

            {MPD_playlists_folder}/cdda_mpd_playlist.m3u
    """

    md = _get_disc_metadata(device)

    with open(CDDA_INFO_PATH, 'w') as f:
        f.write( json.dumps( md ) )

    if md["discid"]:

        print(f'{Fmt.BLUE}(cdda.py) CD metadata saved to {CDDA_INFO_PATH}{Fmt.END}')

        _save_cdda_playlist( md )



if __name__ == "__main__":

    if sys.argv[1:] and '-d' in sys.argv[1]:
        dump_cdda_metadata()
