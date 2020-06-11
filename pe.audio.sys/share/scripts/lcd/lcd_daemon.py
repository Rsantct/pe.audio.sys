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
    A daemon that displays pe.audio.sys info on LCD
"""
# This module is based on monitoring file changes under the pe.audio.sys folder
#   https://watchdog.readthedocs.io/en/latest/
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import lcd_client
#import lcdbig # NOT USED, displays the level value in full size
import os
import yaml
import json
import threading

UHOME = os.path.expanduser("~")

## OBSERVER DIRECTORY and subfolders:
WATCHED_DIR      = f'{UHOME}/pe.audio.sys'
# FILES of interest:
STATE_file       = f'{WATCHED_DIR}/.state.yml'
LOUDNESSMON_file = f'{WATCHED_DIR}/.loudness_monitor'
PLAYER_META_file = f'{WATCHED_DIR}/.player_metadata'

## Auxiliary globals
_state      = {}
_last_state = {}
_last_md    = {}

# Reading the LCD SETTINGS:
try:
    with open( f'{UHOME}/pe.audio.sys/share/scripts/lcd/lcd.yml', 'r' ) as f:
        LCD_CONFIG = yaml.safe_load( f.read() )
except:
    print( '(lcd_daemon) ERROR reading lcd.yml' )
    exit()


class Changed_files_handler(FileSystemEventHandler):
    """ This is a handler that will do something when some file has changed
    """

    def on_modified(self, event):

        path = event.src_path
        #print( f'(lcd_daemon) file {event.event_type}: \'{path}\'' ) # DEBUG

        # pe.audio.sys STATE changes
        if STATE_file in path:
            update_lcd_state()
        # METADATA perodically updated file by players.py
        if PLAYER_META_file in path:
            update_lcd_metadata()
        # LOUDNESS MONITOR
        if path in (LOUDNESSMON_file):
            update_lcd_loudness_monitor()


class Widgets(object):

    # The screen layout draft:
    #       0        1         2
    #       12345678901234567890
    #
    # 1     v:-15.0  bl:-1  MONO
    # 2     b:+1 t:-2  LUref: 12
    # 3     inputname  LUmon: 12
    # 4     ..metadata_marquee..
    #
    # The widget collection definition
    # Values are defaults, later they will be modified.
    #
    # If position is set to '0 0' the widget will not be displayed
    #
    # (i) widget names can be directly MAPPED to pe.audio.sys variables

    def __init__(self):

        self.state = {
                'input'             : { 'pos':'1  3',    'val':''           },
                'level'             : { 'pos':'1  1',    'val':'v:'         },
                'headroom'          : { 'pos':'0  0',    'val':'hrm:'       },
                'balance'           : { 'pos':'9  1',    'val':'bl:'        },
                # the former 'mono' key is now 'midside'
                'midside'           : { 'pos':'17 1',    'val':''           },
                'solo'              : { 'pos':'0  0',    'val':''           },
                'muted'             : { 'pos':'1  1',    'val':'(MUTED) '   },
                'bass'              : { 'pos':'1  2',    'val':'b:'         },
                'treble'            : { 'pos':'6  2',    'val':'t:'         },
                'loudness_ref'      : { 'pos':'12 2',    'val':'LUref:'     },
                'xo_set'            : { 'pos':'0  0',    'val':'xo:'        },
                'drc_set'           : { 'pos':'0  0',    'val':'drc:'       },
                'peq_set'           : { 'pos':'0  0',    'val':'peq:'       },
                'syseq'             : { 'pos':'0  0',    'val':''           },
                'polarity'          : { 'pos':'0  0',    'val':'pol'        },
                'target'            : { 'pos':'0  0',    'val':'pol'        }
                }

        self.aux = {
                'loudness_monitor'  : { 'pos':'12 3',    'val':'LUmon:'     }
                }

        self.meta = {
                'artist'            : { 'pos':'0  0',    'val':''           },
                'album'             : { 'pos':'0  0',    'val':''           },
                'title'             : { 'pos':'0  0',    'val':''           }
                }

        self.scroller = {
                'bottom_marquee'    : { 'pos':'1  4',    'val':''           }
                }


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
    if 'huh?' not in ans:
        LCD.send(f'screen_set scr_info -cursor no -priority foreground ' + \
                 f'-timeout {str(timeout)}' )
        LCD.send('widget_add scr_info info_tit title')
        LCD.send('widget_add scr_info info_txt2 string')
        LCD.send('widget_add scr_info info_txt3 string')
        LCD.send('widget_add scr_info info_txt4 string')

    # Define the screen title (at line 1)
    LCD.send('widget_set scr_info info_tit "pe.audio.sys info:"')

    # Display the temporary message
    line = 2
    for data in split_by_n(message, 20):
        LCD.send('widget_set scr_info info_txt' + str(line) + ' 1 ' +
                 str(line) + ' "' + data + '"')
        line += 1
        if line > 4:
            break


def prepare_main_screen():

    # Adding the screen itself:
    LCD.send('screen_add scr_1')

    # Adding widgets to the main screen:
    # (i) not all them will be used
    ws = Widgets()
    for w in ws.state:
        LCD.send( f'widget_add scr_1 {w} string' )
    for w in ws.aux:
        LCD.send( f'widget_add scr_1 {w} string' )
    for w in ws.meta:
        LCD.send( f'widget_add scr_1 {w} string' )
    for w in ws.scroller:
        LCD.send( f'widget_add scr_1 {w} scroller' )


def update_lcd_state(scr='scr_1'):
    """ Reads system .state.yml then updates the LCD """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    global _state, _last_state

    def show_state(data, priority="info"):

        ws = Widgets()

        global loudness_track

        for key, value in data.items():

            # some state dict keys cannot have its
            # correspondence into the widgets_state dict
            if key not in ws.state:
                continue

            pos = ws.state[key]['pos']  # pos ~> position
            lbl = ws.state[key]['val']  # lbl ~> label

            # When booleans (loudness_track, muted)
            # will leave the defalul widget value or will supress it
            if type(value) == bool:
                if not value:
                    lbl = ''
                # Update global to be accesible outside from auxiliary
                if key == 'loudness_track':
                    loudness_track = value

            # Special case: loudness_ref will be rounded to integer
            #               or void if no loudness_track
            elif key == 'loudness_ref':
                if data['loudness_track']:
                    lbl += str( int( round(value, 0) ) ).rjust(3)
                else:
                    lbl = 'LOUDc off'

            # Special case: tone will be rounded to integer
            elif key == 'bass' or key == 'treble':
                lbl += str( int(round(value, 0)) ).rjust(2)

            # Special case: midside (formerly 'mono')
            elif key == 'midside':
                if data['midside'] == 'off':
                    lbl = '>ST<'
                elif data['midside'] == 'mid':
                    lbl = 'MONO'
                elif data['midside'] == 'side':
                    lbl = 'SIDE'
                else:
                    lbl = ''
                # Special usage mono label to display if convolver is off
                if 'convolver_runs' in data and not data['convolver_runs']:
                    lbl = ' zzz' # brutefir is sleeping

            # Any else key:
            else:
                lbl += str(value)

            # sintax for string widgets:
            #   widget_set screen widget coordinate "text"
            cmd = f'widget_set {scr} {key} {pos} "{lbl}"'
            LCD.send( cmd )

        # The big screen to display the level value
        #lcdbig.show_level( str(data['level']) )
        pass

    with open(STATE_file, 'r') as f:
        _state = yaml.safe_load(f)
        # avoid if reading an empty file:
        if _state and _state != _last_state:
            show_state( _state )
            _last_state = _state


def update_lcd_loudness_monitor(scr='scr_1'):
    """ Reads the monitored value from the file .loudness_monitor
        then updates the LCD display.
    """
    ws   = Widgets()
    wdg  = 'loudness_monitor'
    pos  = ws.aux[wdg]['pos']
    lbl  = ws.aux[wdg]['val']

    try:
        with open(LOUDNESSMON_file, 'r') as f:
            # e.g. {'LU_I': -6.0, 'scope': 'album'}
            lu_dict = json.loads( f.read() )
            lu_I = lu_dict["LU_I"]
            # Will display integers values of LU-Integrated
            lbl += str( int( round( lu_I , 0) ) ).rjust(3)
    except:
        lbl += ' - '

    cmd = f'widget_set {scr} {wdg} {pos} "{lbl}"'
    LCD.send( cmd )


def update_lcd_metadata(scr='scr_1'):
    """ Reads the metadata dict then updates the LCD display marquee """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    def compose_marquee(md):
        # Will compose a satring by joining artist+album+title
        tmp = ''
        for k, v in md.items():
            if k in ('artist', 'album', 'title') and v != '-':
                tmp += k[:2] + ':' + str(v).replace('"', '\\"') + ' '
        return tmp[:-1]

    # Read metadata file
    global _last_md
    md = {}
    with open(PLAYER_META_file, 'r') as f:
        md = json.loads( f.read() )

    if md == _last_md:
        return
    else:
        _last_md = md

    # Modify the metadata dict to have a new field 'composed_marquue'
    # with artist+album+title to be displayed on the LCD bottom line marquee.
    marquee = compose_marquee(md)

    ws = Widgets()
    pos =   ws.scroller['bottom_marquee']['pos']
    lbl =   ws.scroller['bottom_marquee']['val']
    lbl +=  str(marquee)

    left, top   = pos.split()
    right       = 20
    bottom      = top
    direction   = 'm'  # (h)orizontal (v)ertical or (m)arquee
    speed       = str( LCD_CONFIG['scroller_speed'] )
    # adding a space for marquee mode
    if direction == 'm':
        lbl += ' '

    # sintax for scroller widgets:
    # widget_set screen widget left top right bottom direction speed "text"
    cmd = f'widget_set {scr} bottom_marquee {left} {top} {right} {bottom} ' + \
          f'{direction} {speed} "{lbl}"'
    LCD.send( cmd )


if __name__ == "__main__":

    # Registers a client under the LCDd server
    LCD = lcd_client.Client('pe.audio.sys', host='localhost', port=13666)
    if LCD.connect():
        LCD.register()
        print( f'(lcd_daemon) hello: { LCD.query("hello") }' )
    else:
        print( f'(lcd_daemon) Error registering pe.audio.sys client on LCDd server' )
        exit()

    #LCD.set_verbose(True)  # only for DEBUG purposes

    # Prepare the main screen
    prepare_main_screen()
    show_temporary_screen('    Hello :-)')

    # First update:
    update_lcd_state()
    update_lcd_loudness_monitor()
    update_lcd_metadata()

    # Starts a WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #  (i) Even observing recursively the CPU load is negligible
    observer = Observer()
    observer.schedule(event_handler=Changed_files_handler(),
                      path=WATCHED_DIR,
                      recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()
