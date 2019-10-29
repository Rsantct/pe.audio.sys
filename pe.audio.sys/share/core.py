#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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


import os, sys
import socket
import subprocess as sp
import threading
import yaml
import jack
import numpy as np
import threading
from time import sleep


# AUX and FILES MANAGEMENT:
def read_yaml(filepath):
    """ Returns a dictionary from an YAML file """
    with open(filepath) as f:
        d = yaml.load(f)
    return d

def save_yaml(dic, filepath):
    """ Save a dict to disk """
    with open( filepath, 'w' ) as f:
        yaml.dump( dic, f, default_flow_style=False )

def find_target_sets():
    """ Returns the uniques target filenames w/o the suffix _mag.dat or _pha.dat,
        also will add 'none' as an additional set.
    """
    result = ['none']
    files = os.listdir( EQ_FOLDER )
    tmp = [ x for x in files if x[-14:-7] == 'target_'  ]
    for x in tmp:
        if not x[:-8] in result:
            result.append( x[:-8] )
    return result

def get_eq_curve(prop, value, sta=None):
    """ Retrieves the tone or loudness curve of the desired value 
        'sta' -state- will be used only to retrieve the
        suited loudness index curve, which depends on levels.
    """
    # Tone eq curves are provided in [-6...0...+6]
    if prop in ('bass', 'treb'):
        index = 6 - int(round(value))

    # For loudness eq curves we have a flat curve index inside config.yml
    elif prop == 'loud':

        index_min   = 0
        index_max   = EQ_CURVES['loud_mag'].shape[1] - 1
        index_flat  = LOUD_FLAT_CURVE_INDEX

        if sta['loudness_track']:
            index = index_flat - sta['level'] - sta['loudness_ref']
        else:
            index = index_flat
        index = int(round(index))

        # Clamp index to available "loudness deepness" curves
        index = max( min(index, index_max), index_min )

    return EQ_CURVES[f'{prop}_mag'][:,index], EQ_CURVES[f'{prop}_pha'][:,index]

def find_eq_curves():
    """ Scans share/eq/ and try to collect the whole set of EQ curves
        needed for the EQ stage on Brutefir
    """
    EQ_CURVES = {}
    eq_files = os.listdir(EQ_FOLDER)

    fnames = (  'loudness_mag.dat', 'bass_mag.dat', 'treble_mag.dat',
                'loudness_pha.dat', 'bass_pha.dat', 'treble_pha.dat',
                'freq.dat' )

    cnames = {  'loudness_mag.dat'  : 'loud_mag',
                'bass_mag.dat'      : 'bass_mag',
                'treble_mag.dat'    : 'treb_mag',
                'loudness_pha.dat'  : 'loud_pha',
                'bass_pha.dat'      : 'bass_pha',
                'treble_pha.dat'    : 'treb_pha',
                'freq.dat'          : 'freqs'     }

    # pendings curves to find ( freq + 2x loud + 4x tones = 7 )
    pendings = len(fnames)
    for fname in fnames:

        # Only one file named as <fname> must be found
        files = [ x for x in eq_files if fname in x]
        if files:
            if len (files) == 1:
                EQ_CURVES[ cnames[fname] ] = \
                                       np.loadtxt( f'{EQ_FOLDER}/{files[0]}' )
                pendings -= 1
            else:
                print(f'(core.py) too much \'...{fname}\' files under share/eq/')
        else:
                print(f'(core.py) ERROR finding a \'...{fname}\' file under share/eq/')
    
    if not pendings:
        return EQ_CURVES
    else:
        return {}

def find_loudness_flat_curve_index():
    index_max   = EQ_CURVES['loud_mag'].shape[1] - 1
    index_flat = -1
    for i in range(index_max):
        if np.sum( abs(EQ_CURVES['loud_mag'][:,i]) ) <= 0.1:
            index_flat = i
            break
    return index_flat

def calc_eq( sta ):
    """ Calculate the eq curves to be applied on the Brutefir EQ module,
        as per the provided 'sta' state values
    """

    loud_mag, loud_pha = get_eq_curve( prop = 'loud', value = sta['loudness_ref'],
                                       sta = sta )
    bass_mag, bass_pha = get_eq_curve( prop = 'bass', value = sta['bass']         )
    treb_mag, treb_pha = get_eq_curve( prop = 'treb', value = sta['treble']       )

    target_name = sta['target']
    if target_name == 'none':
        targ_mag = np.zeros( EQ_CURVES['freqs'].shape[0] )
        targ_pha = np.zeros( EQ_CURVES['freqs'].shape[0] )
    else:
        targ_mag = np.loadtxt( f'{EQ_FOLDER}/{target_name}_mag.dat' )
        targ_pha = np.loadtxt( f'{EQ_FOLDER}/{target_name}_pha.dat' )

    eq_mag = targ_mag + loud_mag * sta['loudness_track'] + bass_mag + treb_mag
    eq_pha = targ_pha + loud_pha * sta['loudness_track'] + bass_pha + treb_pha

    return eq_mag, eq_pha

def calc_gain( sta ):
    """ Calculates the gain from: level, ref_level_gain and the source gain offset
    """
    gain    = sta['level'] + float(CONFIG['ref_level_gain']) \
              + float( CONFIG['sources'][sta['input']]['gain'] )
    return gain
    
# BRUTEFIR MANAGEMENT:          
def bf_cli(command):
    """ send commands to brutefir and disconnects from it """
    with socket.socket() as s:
        try:
            s.connect( ('localhost', 3000) )
            command = command + '; quit\n'
            s.send(command.encode())
        except:
            print (f'Brutefir socket error')

def bf_set_midside( mode ):
    """ midside (formerly mono) is implemented at the f.eq.X stages:
        in.L  ------->  eq.L
                \/
                /\
        in.L  ------->  eq.L
    """
    if   mode == 'mid':
        bf_cli( 'cfia "f.eq.L" "in.L" m0.5 ; cfia "f.eq.L" "in.R" m0.5 ;'
                'cfia "f.eq.R" "in.L" m0.5 ; cfia "f.eq.R" "in.R" m0.5  ')
    elif mode == 'side':
        bf_cli( 'cfia "f.eq.L" "in.L" m0.5 ; cfia "f.eq.L" "in.R" m-0.5 ;'
                'cfia "f.eq.R" "in.L" m0.5 ; cfia "f.eq.R" "in.R" m-0.5  ')
    elif mode == 'off':
        bf_cli( 'cfia "f.eq.L" "in.L" m1.0 ; cfia "f.eq.L" "in.R" m0.0 ;'
                'cfia "f.eq.R" "in.L" m0.0 ; cfia "f.eq.R" "in.R" m1.0  ')
    else:
        pass

def bf_set_gains( sta ):
    """ Adjust brutefir gain at drc.X stages as per the provided state values """

    gain    = calc_gain( sta )

    balance = float( sta['balance'] )

    # Booleans:
    solo    = sta['solo']
    muted   = sta['muted']
 
    # (i) m_xxxx stands for an unity multiplier
    m_solo_L = {'off': 1, 'l': 1, 'r': 0} [ solo ]
    m_solo_R = {'off': 1, 'l': 0, 'r': 1} [ solo ]
    m_mute   = {True: 0, False: 1}        [ muted ]
    
    gain_L = (gain - balance/2.0)
    gain_R = (gain + balance/2.0)
    
    # We compute from dB to a multiplier, this is an alternative to 
    # adjusting the attenuation on 'cffa' command syntax
    m_gain_L = 10**(gain_L/20.0) * m_mute * m_solo_L
    m_gain_R = 10**(gain_R/20.0) * m_mute * m_solo_R

    # cffa will apply atten at the 'from filters' input section on drc filters
    cmd =   'cffa "f.drc.L" "f.eq.L" m' + str( m_gain_L ) + ';' \
          + 'cffa "f.drc.R" "f.eq.R" m' + str( m_gain_R ) + ';'
    # print(cmd) # debug
    bf_cli(cmd)

def bf_set_eq( eq_mag, eq_pha ):
    """ Adjust the Brutefir EQ module  """
    freqs = EQ_CURVES['freqs']
    mag_pairs = []
    pha_pairs = []
    i = 0
    for freq in freqs:
        mag_pairs.append( str(freq) + '/' + str(round(eq_mag[i], 3)) )
        pha_pairs.append( str(freq) + '/' + str(round(eq_pha[i], 3)) )
        i += 1
    mag_str = ', '.join(mag_pairs)
    pha_str = ', '.join(pha_pairs)
    bf_cli('lmc eq "c.eq" mag '   + mag_str)
    bf_cli('lmc eq "c.eq" phase ' + pha_str)

def bf_read_eq():
    try:
        cmd = 'lmc eq "c.eq" info; quit'
        tmp = sp.check_output( f'echo \'{cmd}\' | nc localhost 3000', shell=True ).decode()
    except:
        return ''
    tmp = [x for x in tmp.split('\n') if x]
    return tmp[2:]

def bf_set_drc( x ):
    if x == 'none':
        cmd = ( f'cfc "f.drc.L" -1         ; cfc "f.drc.R" -1         ;' )
    else:
        cmd = ( f'cfc "f.drc.L" "drc.L.{x}"; cfc "f.drc.R" "drc.R.{x}";' )
    bf_cli( cmd )

def bf_set_xo( filters, xo ):
    for f in filters:
        cmd = ( f'cfc "f.{f}.L" "xo.{f}.{xo}"; cfc "f.{f}.R" "xo.{f}.{xo}";' )
        bf_cli( cmd )


# JACK MANAGEMENT:
def jack_loop(clientname, nports=2):
    """ creates a jack loop with given 'clientname'
        NOTICE: this process will keep running until broken,
                so if necessary you'll need to thread this when calling here.
    """
    # CREDITS:  https://jackclient-python.readthedocs.io/en/0.4.5/examples.html

    # The jack module instance for our looping ports
    client = jack.Client(name=clientname, no_start_server=True)

    if client.status.name_not_unique:
        client.close()
        print( f'(core.jack_loop) \'{clientname}\' already exists in JACK, nothing done.' )
        return

    # Will use the threading.Event mechanism to keep this alive
    event = threading.Event()

    # This sets the actual loop that copies frames from our capture to our playback ports
    @client.set_process_callback
    def process(frames):
        assert len(client.inports) == len(client.outports)
        assert frames == client.blocksize
        for i, o in zip(client.inports, client.outports):
            o.get_buffer()[:] = i.get_buffer()

    # If jack shutdowns, will trigger on 'event' so that the below 'whith client' will break.
    @client.set_shutdown_callback
    def shutdown(status, reason):
        print('(core.jack_loop) JACK shutdown!')
        print('(core.jack_loop) JACK status:', status)
        print('(core.jack_loop) JACK reason:', reason)
        # This triggers an event so that the below 'with client' will terminate
        event.set()

    # Create the ports
    for n in range( nports ):
        client.inports.register(f'input_{n+1}')
        client.outports.register(f'output_{n+1}')
    # client.activate() not needed, see below

    # This is the keeping trick
    with client:
        # When entering this with-statement, client.activate() is called.
        # This tells the JACK server that we are ready to roll.
        # Our above process() callback will start running now.

        print( f'(core.jack_loop) running {clientname}' )
        try:
            event.wait()
        except KeyboardInterrupt:
            print('\n(core.jack_loop) Interrupted by user')
        except:
            print('\n(core.jack_loop)  Terminated')

def jack_connect(p1, p2, mode='connect', wait=1):
    # Will retry during <wait> seconds, this is useful when a
    # jack port exists but it is still not active,
    # for instance Brutefir ports takes some seconds to be active.
    c = wait
    while c:
        try:
            if 'dis' in mode or 'off' in mode:
                JCLI.disconnect(p1, p2)
            else:
                if not p2 in JCLI.get_all_connections(p1):
                    JCLI.connect(p1, p2)
                else:
                    print ( f'(core) {p1.name} already connected to {p2.name}' )
            return True
        except:
            c -= 1
            print ( f'(core) waiting {str(c)}s for \'{p1.name}\' \'{p2.name}\' to be active' )
            sleep(1)
    return False
        
def jack_connect_bypattern(cap_pattern, pbk_pattern, mode='connect', wait=1):

    cap_ports = JCLI.get_ports( cap_pattern, is_output=True )
    pbk_ports = JCLI.get_ports( pbk_pattern, is_input= True )
    if not cap_ports or not pbk_ports:
        return
    #print('CAP', cap_ports) # debug
    #print('PBK', pbk_ports) # debug
    i=0
    for cap_port in cap_ports:
        pbk_port = pbk_ports[i]
        if 'dis' in mode or 'off' in mode:
            jack_connect( cap_port, pbk_port, mode='disconnect', wait=wait )
        else:
            jack_connect( cap_port, pbk_port, mode='connect',    wait=wait )
        i += 1

def jack_clear_preamp():
    """ Force clearing ANY clients, no matter what input was selected
    """
    # Clients wired to preamp_in:
    preamp_ports = JCLI.get_ports('pre_in_loop', is_input=True)
    for preamp_port in preamp_ports:
        for client in JCLI.get_all_connections(preamp_port):
            jack_connect( client, preamp_port, mode='off' )

    # And clients wired to the monitors:
    if CONFIG["source_monitors"]:
        for mon in CONFIG["source_monitors"]:
            # Clearing ANY client into monitor, no matter what input was selected:
            mon_ports = JCLI.get_ports(mon, is_input=True)
            for mon_port in mon_ports:
                for client in JCLI.get_all_connections(mon_port):
                    jack_connect( client, mon_port, mode='off' )
    
def jack_loops_prepare():
    """ The preamp will have the courtesy to prepare the loops
        as per indicated under the config sources section.
        Also a preamp_loop will be spawned.
    """
    for source in CONFIG['sources']:
        pname = CONFIG['sources'][source]['capture_port']
        if 'loop' in pname:
            jloop = threading.Thread( target = jack_loop, args=(pname,) )
            jloop.start()

    # Auto spawn the preamp ports
    jloop = threading.Thread(   target = jack_loop,
                                args=['pre_in_loop', 2]   )
    jloop.start()


# THE PREAMP: AUDIO PROCESSOR, SELECTOR, and SYSTEM STATE KEEPER
def init_source():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """
    preamp = Preamp()

    if CONFIG["init_input"]:
        preamp.select_source  (   CONFIG["init_input"]            )
    else:
        preamp.select_source  (   core.state['input']             )

    save_yaml( preamp.state, STATE_PATH )
    
    del(preamp)
    
def init_audio_settings():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """

    preamp    = Preamp()
    convolver = Convolver()

    if CONFIG["init_mute"]:
        preamp.set_mute       (   CONFIG["init_mute"]             )
    else:
        preamp.set_mute       (   preamp.state['muted']           )

    if CONFIG["init_level"]:         
        preamp.set_level      (   CONFIG["init_level"]            )
    else:
        preamp.set_level      (   preamp.state['level']           )

    if CONFIG["init_max_level"]:
        preamp.set_level(  min( CONFIG["init_max_level"], preamp.state['level'] ) )

    if CONFIG["init_bass"]:
        preamp.set_bass       (   CONFIG["init_bass"]             )
    else:
        preamp.set_bass       (   preamp.state['bass']            )

    if CONFIG["init_treble"]:        
        preamp.set_treble     (   CONFIG["init_treble"]           )
    else:
        preamp.set_treble     (   preamp.state['treble']          )

    if CONFIG["init_balance"]:       
        preamp.set_balance    (   CONFIG["init_balance"]          )
    else:
        preamp.set_balance    (   preamp.state['balance']         )

    if CONFIG["init_loudness_track"]:
        preamp.set_loud_track (   CONFIG["init_loudness_track"]   )
    else:
        preamp.set_loud_track (   preamp.state['loudness_track']  )

    if CONFIG["init_loudness_ref"]:
        preamp.set_loud_ref   (   CONFIG["init_loudness_ref"]     )
    else:
        preamp.set_loud_ref   (   preamp.state['loudness_ref']    )

    if CONFIG["init_midside"]:       
        preamp.set_midside    (   CONFIG["init_midside"]          )
    else:
        preamp.set_midside    (   preamp.state['midside']         )

    if CONFIG["init_solo"]:          
        preamp.set_solo       (   CONFIG["init_solo"]             )
    else:
        preamp.set_solo       (   preamp.state['solo']            )

    if CONFIG["init_xo"]:
        convolver.set_xo      (   CONFIG["init_xo"]               )
    else:
        convolver.set_xo      (   preamp.state['xo_set']          )

    if CONFIG["init_drc"]:
        convolver.set_drc     (   CONFIG["init_drc"]              )
    else:
        convolver.set_drc     (   preamp.state['drc_set']         )

    if CONFIG["init_target"]:
        preamp.set_target     (   CONFIG["init_target"]           )
    else:
        preamp.set_target     (   preamp.state['target']          )

    save_yaml( preamp.state, STATE_PATH )

    del(convolver)
    del(preamp)

class Preamp(object):

    def __init__(self):

        # The state dictionary
        self.state = read_yaml( STATE_PATH )
        # The target curves available under the 'eq' folder
        self.target_sets = find_target_sets()
        # The available span for tone curves
        self.bass_span   = int( (EQ_CURVES['bass_mag'].shape[1] - 1) / 2 )
        self.treble_span = int( (EQ_CURVES['treb_mag'].shape[1] - 1) / 2 )
        # Max authorised gain
        self.gmax        = float(CONFIG['gain_max'])
        # Max authorised balance
        self.balmax      = float(CONFIG['balance_max'])
        
    def _validate( self, candidate ):
        
        g               = calc_gain( candidate )
        b               = candidate['balance']
        eq_mag, eq_pha  = calc_eq(candidate)

        headroom = self.gmax - g - np.max(eq_mag) - np.abs(b/2.0)

        if headroom >= 0:
            # APPROVED
            bf_set_gains( candidate )
            bf_set_eq( eq_mag, eq_pha )
            self.state = candidate
            return 'done'
        else:
            # REFUSED
            return 'not enough headroom'

    def set_level(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['level'] += round(float(value), 2)
        else:
            candidate['level'] =  round(float(value), 2)
        return self._validate( candidate )

    def set_balance(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['balance'] += round(float(value), 2)
        else:
            candidate['balance'] =  round(float(value), 2)
        if abs(candidate['balance']) <= self.balmax:
            return self._validate( candidate )
        else:
            return 'too much'
        
    def set_bass(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['bass'] += round(float(value), 2)
        else:
            candidate['bass'] =  round(float(value), 2)
        if abs(candidate['bass']) <= self.bass_span:
            return self._validate( candidate )
        else:
            return 'too much'
        
    def set_treble(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['treble'] += round(float(value), 2)
        else:
            candidate['treble'] =  round(float(value), 2)
        if abs(candidate['treble']) <= self.treble_span:
            return self._validate( candidate )
        else:
            return 'too much'

    def set_loud_ref(self, value):
        candidate = self.state.copy()
        # this try just validate the given value
        try:
            candidate['loudness_ref'] = round(float(value), 2)
            return self._validate( candidate )
        except:
            return 'bad value'

    def set_loud_track(self, value):
        candidate = self.state.copy()
        # this try just validate the given value
        try:
            value = { 'on':True , 'off':False, 'true':True, 'false':False,
                      'toggle': {True:False, False:True}[self.state['loudness_track']]
                    } [ value.lower() ]
            candidate['loudness_track'] = value
            return self._validate( candidate )
        except:
            return 'bad option'

    def set_target(self, value):
        candidate = self.state.copy()
        if value in self.target_sets:
            candidate['target'] = value
            return self._validate( candidate )
        else:
            return f'target \'{value}\' not available'

    def set_solo(self, value):
        if value.lower() in ['off', 'l', 'r']:
            self.state['solo'] = value.lower()
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'

    def set_mute(self, value):
        if value.lower() in ['false', 'true', 'off', 'on', 'toggle']:
            value = { 'false':False, 'off':False, 
                      'true' :True,  'on' :True,
                      'toggle': {False:True, True:False} [ self.state['muted'] ]
                    } [ value.lower() ]
            self.state['muted'] = value
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'

    def set_midside(self, value):
        if   value.lower() in [ 'mid', 'side', 'off' ]:
            bf_set_midside( value.lower() )
            self.state['midside'] = value.lower()
        else:
            return 'bad option'
        return 'done'

    def get_eq(self):
        return bf_read_eq()

    def select_source(self, value):
        """ this is the source selector """
        
        def source_select(source):

            if source == 'none':
                jack_clear_preamp()
                return True

            if not source in CONFIG['sources']:
                # do nothing
                return False

            # clearing 'preamp' connections
            jack_clear_preamp()

            # connecting the new SOURCE to PREAMP input
            jack_connect_bypattern( CONFIG['sources'][source]['capture_port'],
                                    'pre_in' )

            # and connecting also to the MONITORS:
            if CONFIG["source_monitors"]:
                for monitor in CONFIG["source_monitors"]:
                    jack_connect_bypattern( CONFIG['sources'][source]['capture_port'],
                                            monitor )

            return True

        if source_select(value):
            self.state['input'] = value
            return 'done'
        else:
            return f'source \'{value}\' not defined'


# THE CONVOLVER: DRC and XO Brutefir stages management
class Convolver(object):

    def __init__(self):
        self.name = CONFIG['loudspeaker']
        files = os.listdir(LSPK_FOLDER)

        # ------ DRC sets ------
        # DRC pcm files must be named:
        #    drc.X.DRCSETNAME.pcm   where X must be L | R
        #    0123456.........-4    
        #
        self.drc_sets       = []
        tmp = [ x for x in files if x[:4] == 'drc.'  ]
        for x in tmp:
            if not x[6:-4] in self.drc_sets:
                self.drc_sets.append( x[6:-4] )

        # ------  XO sets ------
        # XO pcm files must be named:
        #    xo.XY.XOSETNAME.pcm   where XY must be fr | lo | mi | hi | sw
        #    0123456........-4    
        #
        self.xo_sets        = []
        tmp = [ x for x in files if x[:3] == 'xo.' ]
        for x in tmp:
            if not x[6:-4] in self.xo_sets:
                self.xo_sets.append( x[6:-4] )
        
        # ------  WAYS (brutefir filters) ------
        self.filters = []
        for x in tmp:
            if not x[3:5] in self.filters:
                self.filters.append( x[3:5] )
        
    def set_drc(self, drc):
        if drc in self.drc_sets or drc == 'none':
            bf_set_drc( drc )
            return 'done'
        else:
            return f'drc set \'{drc}\' not available'

    def set_xo(self, xo):
        if xo in self.xo_sets:
            bf_set_xo( self.filters, xo )
            return 'done'
        else:
            return f'xo set \'{xo}\' not available'


# THE CLIENT INTERFACE TO THE JACK SERVER
# IMPORTANT: this module core.py NEEDS JACK to be running.
try:
    JCLI = jack.Client('tmp', no_start_server=True)
except:
    print( '(core.py) ERROR cannot commuticate to JACK SERVER.' )

# COMMON USE VARIABLES:
UHOME           = os.path.expanduser("~")
CONFIG          = read_yaml( f'{UHOME}/pe.audio.sys/config.yml' )
LSPK_FOLDER     = f'{UHOME}/pe.audio.sys/loudspeakers/{CONFIG["loudspeaker"]}'
STATE_PATH      = f'{UHOME}/pe.audio.sys/.state.yml'
EQ_FOLDER       = f'{UHOME}/pe.audio.sys/share/eq'
EQ_CURVES       = find_eq_curves()

if not EQ_CURVES:
    print( '(core.py) ERROR loading EQ_CURVES from share/eq/' )
    sys.exit()

LOUD_FLAT_CURVE_INDEX = find_loudness_flat_curve_index()

if LOUD_FLAT_CURVE_INDEX < 0:
    print( f'(core) MISSING FLAT LOUDNESS CURVE. BYE :-/' )        
    sys.exit()

