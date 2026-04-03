#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

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
import sys
import yaml
import threading
from time import sleep

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from miscel import *

## Auxiliary globals
state         = { 'lu_offset': 0 }
last_warning  = ''
last_metadata = {}
last_lu_I     = 0

# Reading the LCD SETTINGS:
try:
    with open( f'{MAINFOLDER}/share/plugins/lcd/lcd.yml', 'r' ) as f:
        LCD_CONFIG = yaml.safe_load( f.read() )
except:
    print( '(lcd_daemon) ERROR reading lcd.yml' )
    exit()


class Changed_files_handler(FileSystemEventHandler):
    """ This is a handler that will do something when some file has changed
    """

    def on_modified(self, event):

        if event.is_directory:
            return

        path = event.src_path
        if verbose:
            print( f'(lcd_daemon) EVENT {event.event_type}: \'{path}\'' )

        # pe.audio.sys STATE changes
        if STATE_PATH in path:
            update_lcd_state()

        # METADATA perodically updated file by players.py
        if PLAYER_META_PATH in path:
            update_lcd_metadata()

        # LOUDNESS MONITOR
        if path in (LDMON_PATH):
            update_lcd_loudness_monitor()

        # TEMPORARY WARNINGS
        if AUX_INFO_PATH in path:
            show_new_warning()

        if not LCD.error:
            return

        print('(lcd_daemon) *!* detected LCDd.error')
        n = 3
        while n:
            print('(lcd_daemon) reconnecting to LCDd ...')
            if connect2LCDd():
                break
            sleep(.1)
            n -= 1


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
                'lu_offset'         : { 'pos':'12 3',    'val':'LUref:'     },
                'xo_set'            : { 'pos':'0  0',    'val':'xo:'        },
                'drc_set'           : { 'pos':'0  0',    'val':'drc:'       },
                'peq_set'           : { 'pos':'0  0',    'val':'peq:'       },
                'syseq'             : { 'pos':'0  0',    'val':''           },
                'polarity'          : { 'pos':'0  0',    'val':'pol'        },
                'target'            : { 'pos':'0  0',    'val':'pol'        }
                }

        self.aux = {
                'loudness_monitor'  : { 'pos':'12 2',    'val':'LUmon:'     }
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

    if not message.strip():
        print('(lcd_daemon) Error cannot show temporary void message')
        return

    try:

        # lcdproc manages 1/8 seconds
        timeout = 8 * timeout

        # Will try to define the screen, if already exist will receive 'huh?'
        ans = LCD.send('screen_add scr_info')
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

    except Exception as e:
        print(f'(lcd_daemon) Error cannot show temporary message "{message}": {str(e)}')


def show_new_warning():
    """ This checks for pe.audio.sys temporary warnings
        changes (looks inside AUX_INFO_PATH)
    """

    global last_warning

    curr_warn = ''

    aux_info = read_json_from_file(AUX_INFO_PATH, 0.5)
    curr_warn = aux_info.get('warning', '')

    if curr_warn and curr_warn != last_warning:
        if curr_warn:
            show_temporary_screen( curr_warn, timeout=5)
        last_warning = curr_warn

    return


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
    """ Reads system .state file, then updates the LCD """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    global state

    def show_state(priority="info"):

        ws = Widgets()

        global equal_loudness

        for key, value in state.items():

            # The LU bar disables displaying bass and treble
            if LCD_CONFIG["LUmon_bar"]:
                if key in ('bass', 'treble'):
                    continue

            # some state dict keys cannot have its
            # correspondence into the widgets_state dict
            if key not in ws.state:
                continue

            pos = ws.state[key]['pos']  # pos ~> position
            lbl = ws.state[key]['val']  # lbl ~> label

            # When booleans (equal_loudness, muted)
            # will leave the defalul widget value or will supress it
            if type(value) == bool:
                if not value:
                    lbl = ''
                # Update global to be accesible outside from auxiliary
                if key == 'equal_loudness':
                    equal_loudness = value

            # Special case: lu_offset will be rounded to integer
            #               or void if no equal_loudness
            elif key == 'lu_offset':
                if state['equal_loudness']:
                    lbl += str( int( round(value, 0) ) ).rjust(3)
                else:
                    lbl = 'LOUDc off'

            # Special case: tone will be rounded to integer
            elif key == 'bass' or key == 'treble':
                lbl += str( int(round(value, 0)) ).rjust(2)

            # Special case: midside (formerly 'mono')
            elif key == 'midside':
                if state['midside'] == 'off':
                    lbl = '>ST<'
                elif state['midside'] == 'mid':
                    lbl = 'MONO'
                elif state['midside'] == 'side':
                    lbl = 'SIDE'
                else:
                    lbl = ''
                # Special usage mono label to display if convolver is off
                if 'convolver_runs' in state and not state['convolver_runs']:
                    lbl = ' zzz' # brutefir is sleeping

            # Any else key:
            else:
                lbl += str(value)

            # sintax for string widgets:
            #   widget_set screen widget coordinate "text"
            cmd = f'widget_set {scr} {key} {pos} "{lbl}"'
            LCD.send( cmd )

        # The big screen to display the level value
        #lcdbig.show_level( str(state['level']) )
        pass

    # Reading state
    try:
        new_state = read_state_from_disk()
    except:
        return

    # If changed
    if new_state != state:

        if verbose:
            changes = dict_compare(new_state, state)
            print(f'(lcd_daemon) STATE changed: {changes}')

        # update global state
        state = new_state

        # refreshing the LU monitor bar in LCD if needed
        if LCD_CONFIG["LUmon_bar"]:
            update_lcd_loudness_monitor()

        # refresh state items in LCD
        show_state()


def update_lcd_loudness_monitor(scr='scr_1'):
    """ Reads the monitored value from the file .loudness_monitor
        then updates the LCD display.

        Optionally, a LU meter bar will be displayed, having an inserted
        marker as per the selected LU reference offset.
        (see lcd.yml config file)
        This makes it easy to adjust the proper LU reference offset setting
    """

    global last_lu_I

    ld_mon = read_json_from_file(LDMON_PATH)
    lu_I = ld_mon.get('LU_I', None)

    if lu_I == last_lu_I:
        return

    if verbose:
        print(f'(lcd_daemon) LU_I changed: {last_lu_I} -> {lu_I}')

    last_lu_I = lu_I

    # Widget
    wdg  = 'loudness_monitor'

    # LU monitor and reference as numbers option:
    if not LCD_CONFIG["LUmon_bar"]:

        ws   = Widgets()
        pos  = ws.aux[wdg]['pos']
        lbl  = ws.aux[wdg]['val']

        if lu_I is not None:
            # Will display integers values of LU-Integrated
            lbl += str( int(round(lu_I)) ).rjust(3)
        else:
            lbl += ' - '

    # LU monitor and reference bar option:
    else:

        pos = '1 2'
        lbl = ''

        # LU monitored
        if lu_I is None:
            lu_I = 0

        # LU reference offset (usually in the range from 0 to 12)
        # (it is found in the state global variable)
        lu_offset = int(round(state["lu_offset"]))

        # The LU meter bar length:
        barLen = int( round( lu_I * 20 / 12.0 ) )

        # The marker bar position for the LU reference offset value:
        p = int( round( lu_offset * 20 / 12.0 ) )
        # Clamped from 0 to 19
        p = max(min(p, 19), 0)

        # The "label" to print into the 20 char length ldc line:
        lbl = '-' * barLen + ' ' * (20-barLen)

        # Inserting the marker
        lbl = lbl[:p] + '*' + lbl[p+1:]

    cmd = f'widget_set {scr} {wdg} {pos} "{lbl}"'
    LCD.send( cmd )


def update_lcd_metadata(scr='scr_1'):
    """ Reads the metadata dict then updates the LCD display marquee """
    # http://lcdproc.sourceforge.net/docs/lcdproc-0-5-5-user.html

    global last_metadata

    # Composes a string by joining artist+album+title
    def compose_marquee(md):
        tmp = ''
        for k, v in md.items():
            if k in ('artist', 'album', 'title') and v and v != '-':
                tmp += k[:2] + ':' + str(v).replace('"', '\\"') + ' '
        return tmp[:-1]


    # Trying to read the metadata file, or early return if failed
    md = read_metadata_from_disk()
    if not md:
        return

    # Early return if no changes in title/album
    if last_metadata.get('title', '') == md.get('title', '') \
       and last_metadata.get('album', '') == md.get('album', ''):
           return

    if verbose:
       print(f'(lcd_daemon) METADATA TITLE changed: {md.get("title")}')

    last_metadata = md

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


def connect2LCDd():
    """ Connect and register a client under the LCDd server
        and reset the LCD.error flag

        returns: boolean
    """

    if LCD.connect():

        if LCD.register():
            LCD.error = False
            print( f'(lcd_daemon) hello: { LCD.send("hello") }' )
            return True

        else:
            print( f'(lcd_daemon) Error registering pe.audio.sys client on LCDd server' )

    else:
        print( f'(lcd_daemon) Error connecting pe.audio.sys client on LCDd server' )

    return False


if __name__ == "__main__":

    verbose = False
    client_verbose = False

    for opc in sys.argv[1:]:

        if opc == '-v':
            print('(lcd_daemon) VERBOSE MODE')
            verbose = True

        elif opc == 'cv':
            client_verbose = True


    # The LCD client
    LCD = lcd_client.Client('pe.audio.sys', host='localhost', port=13666, verbose=client_verbose)

    if not connect2LCDd():
        print( f'(lcd_daemon) Error registering pe.audio.sys client on LCDd server' )
        exit()

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
                      path=MAINFOLDER,
                      recursive=False)
    observer.start()
    obsloop = threading.Thread( target=observer.join() )
    obsloop.start()
