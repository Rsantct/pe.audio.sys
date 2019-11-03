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

"""
    A daemon service that displays pe.audio.sys info on LCD
"""
# This is based on monitoring file changes under the pe.audio.sys folder
# v1.1  from pre.di.c to pe.audio.sys

import sys
from time import sleep
import yaml
import json

import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import lcd_client
#import lcdbig

import os
UHOME = os.path.expanduser("~")

sys.path.append( f'{UHOME}/pe.audio.sys/share/services' )
import players

LEVEL_OLD = None

# 'loudness_track' as global because loudness_monitor value does not
# belong to the state dict and the updater needs to kwow about it.
loudness_track = False


# Will watch for files changed on this folder and subfolders:
WATCHED_DIR      = f'{UHOME}/pe.audio.sys'
# The files we are going to pay attention to:
STATE_file       = f'{WATCHED_DIR}/.state.yml'
LIBRESPOT_file   = f'{WATCHED_DIR}/.librespot_events'
SPOTIFY_file     = f'{WATCHED_DIR}/.spotify_events'
ISTREAMS_file    = f'{WATCHED_DIR}/.istreams_events'
DVB_file         = f'{WATCHED_DIR}/.dvb_events'
MPD_file         = f'{WATCHED_DIR}/.mpd_events'
LOUDNESSMON_file = f'{WATCHED_DIR}/.loudness_monitor'

# Reading the LCD SETTINGS:
f = open( f'{UHOME}/pe.audio.sys/share/scripts/lcd/lcd.yml', 'r' )
tmp = f.read()
f.close()
try:
    LCD_CONFIG = yaml.load(tmp)
except:
    print ( 'YAML error reading lcd.yml' )

def show_temporary_screen( message, timeout=LCD_CONFIG['info_screen_timeout'] ):
    """An additional screen to display temporary information"""

    def split_by_n( seq, n ):
        # a generator to divide a sequence into chunks of n units
        while seq:
            yield seq[:n]
            seq = seq[n:]

    # lcdproc manages 1/8 seconds
    timeout = 8 * timeout

    # Will try to define the screen, if already exist will receive 'huh?'
    ans = LCD.query('screen_add scr_info')
    if not 'huh?' in ans:
        LCD.send(f'screen_set scr_info -cursor no -priority foreground -timeout {str(timeout)}' )
        LCD.send('widget_add scr_info info_tit title')
        LCD.send('widget_add scr_info info_txt2 string')
        LCD.send('widget_add scr_info info_txt3 string')
        LCD.send('widget_add scr_info info_txt4 string')

    # Define the screen title (at line 1)
    LCD.send('widget_set scr_info info_tit "pe.audio.sys info:"')

    # Display the temporary message
    line = 2
    for data in split_by_n(message, 20):
        LCD.send('widget_set scr_info info_txt' + str(line) + ' 1 ' + str(line) + ' "' + data + '"')
        line += 1
        if line > 4:
            break

def define_widgets():

    # The screen layout draft:
    #       0        1         2
    #       12345678901234567890
    #
    # 1     v:-15.0  bl:-1  MONO
    # 2     b:+1 t:-2 LOUDref 12
    # 3     inputname     mon 12
    # 4     a_metadata_marquee_

    # The widget collection definition (as global variables)
    # Values are defaults, later update_state() will add the current 
    # state info or supress the value in case of booleans.
    
    # If position is set to '0 0' the widget will not be displayed
    
    global widgets_state # defined text type when prepare_main_screen
    widgets_state = {
                'input'             : { 'pos':'1  3',    'val':''         },
                'level'             : { 'pos':'1  1',    'val':'v:'       },
                'headroom'          : { 'pos':'0  0',    'val':'hrm:'     },
                'balance'           : { 'pos':'10 1',    'val':'bl:'      },
                # the former 'mono' key is now 'midside' 
                'midside'           : { 'pos':'17 1',    'val':''         },
                'solo'              : { 'pos':'0  0',    'val':''         },
                'muted'             : { 'pos':'1  1',    'val':'MUTED    '},
                'bass'              : { 'pos':'1  2',    'val':'b:'       },
                'treble'            : { 'pos':'6  2',    'val':'t:'       },
                'loudness_ref'      : { 'pos':'15 2',    'val':'ref'      },
                'loudness_track'    : { 'pos':'11 2',    'val':'LOUD'     },
                'xo_set'            : { 'pos':'0  0',    'val':'xo:'      },
                'drc_set'           : { 'pos':'0  0',    'val':'drc:'     },
                'peq_set'           : { 'pos':'0  0',    'val':'peq:'     },
                'syseq'             : { 'pos':'0  0',    'val':''         },
                'polarity'          : { 'pos':'0  0',    'val':'pol'      },
                'target'            : { 'pos':'0  0',    'val':'pol'      }
                }

    global widgets_aux # info outside pe.audio.sys state
    widgets_aux = {
                'loudness_monitor'  : { 'pos':'15 3',    'val':'mon'     }
                }
                
    global widgets_meta # defined scroller type when prepare_main_screen
    widgets_meta = {
                'artist'            : { 'pos':'0  0',    'val':'' },
                'album'             : { 'pos':'0  0',    'val':'' },
                'title'             : { 'pos':'0  0',    'val':'' },
                'bottom_marquee'    : { 'pos':'1  4',    'val':'' },
                }

def prepare_main_screen():
    """ Defines info main screen 'src_1' and his set of widgets """
    # Adding the screen itself:
    LCD.send('screen_add scr_1')

    # Definig the set of widgets (widgets_xxxx becomes global variables)
    define_widgets()

    # Adding the previously defined widgets to the main screen:
    
    # 1) pe.audio.sys state widgets
    for wName, wProps in widgets_state.items():
        cmd = f'widget_add scr_1 { wName } string'
        LCD.send( cmd )
    # 2) Aux widgets
    for wName, wProps in widgets_aux.items():
        cmd = f'widget_add scr_1 { wName } string'
        LCD.send( cmd )
    # 3) metadata players widgets
    for wName, wProps in widgets_meta.items():
        cmd = f'widget_add scr_1 { wName } scroller'
        LCD.send( cmd )

def update_state():
    """ Reads system .state.yml then updates the LCD """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    def show_state(data, priority="info"):
        global LEVEL_OLD
        global loudness_track
        
        for key, value in data.items():
            pos = widgets_state[key]['pos'] # pos ~> position
            lab = widgets_state[key]['val'] # lab ~> label

            # When booleans (loudness_track, muted)
            # will leave the defalul widget value or will supress it
            if type(value) == bool:
                if not value:
                    lab = ''
                # Update global to be accesible outside from auxiliary
                if key == 'loudness_track':
                    loudness_track = value
                    
            # Special case: loudness_ref will be rounded to integer
            #               or void if no loudness_track
            elif key == 'loudness_ref':
                if data['loudness_track']:
                    lab += str( int(round(value,0)) ).rjust(3)
                else:
                    lab = ''

            # Special case: tone will be rounded to integer
            elif key == 'bass' or key == 'treble':
                lab += str( int(round(value,0)) ).rjust(2)

            # Special case: midside (formerly 'mono')
            elif key == 'midside':
                if data['midside'] == 'off':
                    lab = ''
                else:
                    lab = data['midside'].upper()
                    
            # Any else key:
            else:
                lab += str(value)

                
            # sintax for string widgets:
            #   widget_set screen widget coordinate "text"
            cmd = f'widget_set scr_1 { key } { pos } "{ lab }"'
            #print(cmd)
            LCD.send( cmd )
            
        if LEVEL_OLD != data['level']:
            #lcdbig.show_level( str(data['level']) )
            LEVEL_OLD = data['level']

    with open(STATE_file, 'r') as f:
        state = yaml.load(f)
        show_state( state )
        
def update_loudness_monitor():
    """ Reads the monitored value inside the file .loudness_monitor
        then updates the LCD display.
    """
    
    def show_loudness_monitor(value):
        wdg = 'loudness_monitor'
        pos = widgets_aux[wdg]['pos']
        lab = widgets_aux[wdg]['val']
        
        value = int( round(value,0) )
        if loudness_track:
            lab += str(value).rjust(3)
        else:
            lab = ''
            
        cmd = f'widget_set scr_1 { wdg } { pos } "{ lab }"'
        #print(cmd)
        LCD.send( cmd )


    loudmon = 0.0
    try:
        with open(LOUDNESSMON_file, 'r') as f:
            loudmon = f.read().strip()
            loudmon = round( float(loudmon), 1)
    except:
        pass

    show_loudness_monitor( loudmon )

def update_metadata(metadata, mode='composed_marquee', scr='scr_1'):
    """ Reads the metadata dict then updates the LCD display """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    def compose_marquee(md):
        """ compose a string to be displayed on a LCD bottom line marquee.
        """
        
        tmp = '{ "bottom_marquee":"'
        for k,v in json.loads(md).items():
            if k in ('artist', 'album', 'title') and v != '-':
                tmp += k[:2] + ':' + str(v) + ' '
        tmp += '" }'
        
        return tmp
    
    # This compose a unique marquee widget with all metadata fields:
    if mode == 'composed_marquee':
        metadata = json.loads( compose_marquee(metadata) )
    # This is if you want to use separate widgets kind of:
    else:
        metadata = json.loads(metadata)

    for key, value in metadata.items():

        if key in widgets_meta.keys():
        
            pos =       widgets_meta[key]['pos']
            label =     widgets_meta[key]['val']
            label +=    str(value)
        
            left, top   = pos.split()
            right       = 20
            bottom      = top
            direction   = 'm' # (h)orizontal (v)ertical or (m)arquee
            speed       = str( LCD_CONFIG['scroller_speed'] )
            # adding a space for marquee mode
            if direction == 'm':
                label += ' '
        
            # sintax for scroller widgets:
            #   widget_set screen widget left top right bottom direction speed "text"
            cmd = f'widget_set {scr} {key} {left} {top} {right} {bottom} {direction} {speed} "{label}"'
            #print(cmd)
            LCD.send( cmd )

class changed_files_handler(FileSystemEventHandler):
    """
        This is a handler that will do something when some file has changed
    """

    def on_modified(self, event):

        path = event.src_path

        # The pe.audio.sys STATE has changed
        if STATE_file in path:
            update_state()

        # A MPLAYER event file has changed
        # (i) The MPLAYER metadata file will be alive only for a 1/4 sec
        #     because players.py will flush each second when the control
        #     web page inquires.
        #     Also we only want <title> field, so it is enough to get
        #     metadata in 'readonly' mode and ignoring it if empty.
        if path in (DVB_file,
                    ISTREAMS_file):
            sleep(1) # avoids bouncing
            # needs decode() because players gives bytes-like
            meta = players.player_get_meta(readonly=True).decode()
            if json.loads(meta)['title'] != '-':
                update_metadata( meta , mode='composed_marquee')

        # ANOTHER PLAYER event file has changed
        if path in (MPD_file,
                    SPOTIFY_file,
                    LIBRESPOT_file):
            sleep(1) # avoids bouncing
            # needs decode() because players gives bytes-like
            meta = players.player_get_meta(readonly=False).decode()
            update_metadata( meta, mode='composed_marquee')

        # The LOUDNESS MONITOR file has changed
        # loudness monitor changes counter
        if path in (LOUDNESSMON_file):
            update_loudness_monitor()
            
if __name__ == "__main__":

    # Registers a client under the LCDd server
    LCD = lcd_client.Client('pe.audio.sys', host='localhost', port=13666)
    if LCD.connect():
        LCD.register()
        print( '(lcd_service )', f'hello: { LCD.query("hello") }' )
    else:
        print( 'Error registering pe.audio.sys on LCDd' )
        sys.exit()

    # Prepare the main screen
    prepare_main_screen()
    show_temporary_screen('    Hello :-)')

    # Displays the state of pe.audio.sys
    update_state()
    # Displays update_loudness_monitor
    update_loudness_monitor()
    
    # Displays metadata
    #md =  '{"artist":"Some ARTIST",'
    #md += ' "album":"Some ALBUM",'
    #md += ' "title":"ファイヴ・スポット・アフター・ダーク"}'
    # needs to decode because players gives bytes-like
    update_metadata( players.player_get_meta().decode() , mode='composed_marquee')

    # Starts a WATCHDOG to see pe.audio.sys files changes,
    # and handle these changes to update the LCD display
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    observer = Observer()
    # recursive=True because will observe changes also under WATCHED_DIR/config/ subdirectory
    observer.schedule(event_handler=changed_files_handler(), path=WATCHED_DIR, recursive=True)
    observer.start()
    obsloop = threading.Thread( target = observer.join() )
    obsloop.start()
