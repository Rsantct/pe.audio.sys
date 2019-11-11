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
from time import sleep


# AUX and FILES MANAGEMENT: ====================================================

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
        needed for the EQ stage in Brutefir
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
    """ scan all curves under the file xxx_loudness_mag.dat to find the flat one """
    index_max   = EQ_CURVES['loud_mag'].shape[1] - 1
    index_flat = -1
    for i in range(index_max):
        if np.sum( abs(EQ_CURVES['loud_mag'][:,i]) ) <= 0.1:
            index_flat = i
            break
    return index_flat

def calc_eq( sta ):
    """ Calculate the eq curves to be applied in the Brutefir EQ module,
        as per the provided dictionary of state values 'sta'
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
    gain    = sta['level'] + float(CONFIG['ref_level_gain'])
    if sta['input'] != 'none':
        gain += float( CONFIG['sources'][sta['input']]['gain'] )
    return gain
    
# BRUTEFIR MANAGEMENT: =========================================================        

def bf_cli(command):
    """ send commands to Brutefir and disconnects from it """
    # using 'with' will disconnect the socket when done
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
    """ Adjust Brutefir gain at drc.X stages as per the provided 'sta'te values """

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
    """ Returns a raw printout from issuing an 'info' query to the Brutefir's EQ module  
    """
    try:
        cmd = 'lmc eq "c.eq" info; quit'
        tmp = sp.check_output( f'echo \'{cmd}\' | nc localhost 3000', shell=True ).decode()
    except:
        return ''
    tmp = [x for x in tmp.split('\n') if x]
    return tmp[2:]

def bf_set_drc( drcID ):
    """ Changes the FIR for DRC at runtime """
    if drcID == 'none':
        cmd = ( f'cfc "f.drc.L" -1             ; cfc "f.drc.R" -1             ;' )
    else:
        cmd = ( f'cfc "f.drc.L" "drc.L.{drcID}"; cfc "f.drc.R" "drc.R.{drcID}";' )
    bf_cli( cmd )

def bf_set_xo( ways, xo_coeffs, xoID ):
    """ Changes the FIRs for XOVER at runtime """

    # example:    
    #   ways:       
    #               f.lo.L f.hi.L f.lo.R f.hi.R f.sw
    #   xo_coeffs:  
    #               xo.hi.L.mp  xo.hi.R.lp 
    #               xo.hi.R.mp  xo.hi.L.lp
    #               xo.lo.mp    xo.lo.lp 
    #               xo.sw.mp    xo.sw.lp
    #   xo_sets:    
    #               mp          lp
    # NOTICE:
    #   This example has dedicated coeff FIRs for hi.L and hi.R,
    #   so when seleting the appropiate coeff we will try 'best matching'
    
    def find_best_match_coeff(way):

        found = ''
        # lets try matching coeff with way[2:] including the channel id
        for coeff in xo_coeffs:
            if way[2:] in coeff[3:] and xoID == coeff.split('.')[-1]:
                found = coeff

        # if not matches, then try just the way[2:4], e.g. 'lo'
        if not found:
            for coeff in xo_coeffs:
                if way[2:4] in coeff[3:] and xoID == coeff.split('.')[-1]:
                    found = coeff
                
        return found
        
    cmd = ''
    for way in ways:
        BMcoeff = find_best_match_coeff(way)
        cmd += f'cfc "{way}" "{BMcoeff}"; ' 
    
    #print (cmd)
    bf_cli( cmd )

def get_brutefir_config(prop):
    """ returns a property from brutefir_config file
        (BETA: currently only works for ludspeaker ways)
    """
    with open(f'{LSPK_FOLDER}/brutefir_config','r') as f:
        lines = f.read().split('\n')
    
    if prop == 'ways':
        ways = []
        for line in [ x for x in lines if x and 'filter' in x.strip().split() ]:
            if not '"f.eq.' in line and not '"f.drc.' in line and \
               line.startswith('filter'):
                   way = line.split()[1].replace('"','')
                   ways.append( way )
        return ways
    else:
        return []

# JACK MANAGEMENT: =============================================================

def jack_loop(clientname, nports=2):
    """ Creates a jack loop with given 'clientname'
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
    """ Low level tool to connect / disconnect a pair of ports, by retriyng for a while """
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
    """ High level tool to connect/disconnect a given port name patterns """
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
    """ Force clearing ANY clients, no matter what input was selected """

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


# THE PREAMP: AUDIO PROCESSOR, SELECTOR, and SYSTEM STATE KEEPER ===============

def init_source():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """
    preamp = Preamp()

    if CONFIG["on_init"]["input"]:
        preamp.select_source  (   CONFIG["on_init"]["input"]      )
    else:
        preamp.select_source  (   core.state['input']             )
    
    state = preamp.state
    del(preamp)

    return state

    
def init_audio_settings():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """

    preamp    = Preamp()
    convolver = Convolver()

    # (i) using != None below to detect 0 values

    on_init = CONFIG["on_init"]

    if on_init["muted"]:
        preamp.set_mute       (   on_init["muted"]                )
    else:
        preamp.set_mute       (   preamp.state['muted']           )

    if on_init["level"] != None:         
        preamp.set_level      (   on_init["level"]                )
    else:
        preamp.set_level      (   preamp.state['level']           )

    if on_init["max_level"] != None:
        preamp.set_level(  min( on_init["max_level"], preamp.state['level'] ) )

    if on_init["bass"] != None :
        preamp.set_bass       (   on_init["bass"]                 )
    else:
        preamp.set_bass       (   preamp.state['bass']            )

    if on_init["treble"] != None :        
        preamp.set_treble     (   on_init["treble"]               )
    else:
        preamp.set_treble     (   preamp.state['treble']          )

    if on_init["balance"] != None :       
        preamp.set_balance    (   on_init["balance"]              )
    else:
        preamp.set_balance    (   preamp.state['balance']         )

    if on_init["loudness_track"]:
        preamp.set_loud_track (   on_init["loudness_track"]       )
    else:
        preamp.set_loud_track (   preamp.state['loudness_track']  )

    if on_init["loudness_ref"] != None :
        preamp.set_loud_ref   (   on_init["loudness_ref"]         )
    else:
        preamp.set_loud_ref   (   preamp.state['loudness_ref']    )

    if on_init["midside"]:       
        preamp.set_midside    (   on_init["midside"]              )
    else:
        preamp.set_midside    (   preamp.state['midside']         )

    if on_init["solo"]:          
        preamp.set_solo       (   on_init["solo"]                 )
    else:
        preamp.set_solo       (   preamp.state['solo']            )

    if on_init["xo"]:
        convolver.set_xo      (   on_init["xo"]                   )
    else:
        convolver.set_xo      (   preamp.state['xo_set']          )

    if on_init["drc"]:
        convolver.set_drc     (   on_init["drc"]                  )
    else:
        convolver.set_drc     (   preamp.state['drc_set']         )

    if on_init["target"]:
        preamp.set_target     (   on_init["target"]               )
    else:
        preamp.set_target     (   preamp.state['target']          )

    state = preamp.state

    del(convolver)
    del(preamp)
    
    return state

class Preamp(object):
    """ attributes:

            state           state dictionary
            inputs          the available inputs dict.
            target_sets     target curves available under the 'eq' folder
            bass_span       available span for tone curves
            treble_span
            gain_max        max authorised gain       
            balance_max     max authorised balance

        methods:

            select_source
            set_level
            set_balance
            set_bass
            set_treble
            set_loud_ref
            set_loud_track
            set_target
            set_solo
            set_mute
            set_midside

            get_state
            get_inputs
            get_target_sets
            get_eq
    """

    def __init__(self):
        
        # The available inputs
        self.inputs = CONFIG['sources']
        # The state dictionary
        self.state = read_yaml( STATE_PATH )
        # The target curves available under the 'eq' folder
        self.target_sets = find_target_sets()
        # The available span for tone curves
        self.bass_span   = int( (EQ_CURVES['bass_mag'].shape[1] - 1) / 2 )
        self.treble_span = int( (EQ_CURVES['treb_mag'].shape[1] - 1) / 2 )
        # Max authorised gain
        self.gain_max    = float(CONFIG['gain_max'])
        # Max authorised balance
        self.balance_max = float(CONFIG['balance_max'])
        
    def _validate( self, candidate ):
        """ Validates that the given 'candidate' (new state dictionary)
            does not exceeds gain limits
        """
        
        g               = calc_gain( candidate )
        b               = candidate['balance']
        eq_mag, eq_pha  = calc_eq( candidate )

        headroom = self.gain_max - g - np.max(eq_mag) - np.abs(b/2.0)

        if headroom >= 0:
            # APPROVED
            bf_set_gains( candidate )
            bf_set_eq( eq_mag, eq_pha )
            self.state = candidate
            return 'done'
        else:
            # REFUSED
            return 'not enough headroom'

    # Bellow we use *dummy to accommodate the pasysctrl.py parser mechanism wich
    # will include two arguments for any function call, even when not necessary. 

    def get_state(self, *dummy):
        return yaml.dump( self.state, default_flow_style=False )

    def get_target_sets(self, *dummy):
        return '\n'.join( self.target_sets )

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
        if abs(candidate['balance']) <= self.balance_max:
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

    def set_loud_ref(self, value, relative=False):
        candidate = self.state.copy()
        # this try if intended just to validate the given value
        try:
            if relative:
                candidate['loudness_ref'] += round(float(value), 2)
            else:
                candidate['loudness_ref'] =  round(float(value), 2)
            return self._validate( candidate )
        except:
            return 'bad value'

    def set_loud_track(self, value, *dummy):
        candidate = self.state.copy()
        try:
            value = { 'on':True , 'off':False, 'true':True, 'false':False,
                      'toggle': {True:False, False:True}[self.state['loudness_track']]
                    } [ value.lower() ]
            candidate['loudness_track'] = value
            return self._validate( candidate )
        except:
            return 'bad option'

    def set_target(self, value, *dummy):
        candidate = self.state.copy()
        if value in self.target_sets:
            candidate['target'] = value
            return self._validate( candidate )
        else:
            return f'target \'{value}\' not available'

    def set_solo(self, value, *dummy):
        if value.lower() in ['off', 'l', 'r']:
            self.state['solo'] = value.lower()
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'

    def set_mute(self, value, *dummy):
        try:
            if value.lower() in ['false', 'true', 'off', 'on', 'toggle']:
                value = { 'false':False, 'off':False, 
                          'true' :True,  'on' :True,
                          'toggle': {False:True, True:False} [ self.state['muted'] ]
                        } [ value.lower() ]
                self.state['muted'] = value
                bf_set_gains( self.state )
                return 'done'
        except:
            return 'bad option'

    def set_midside(self, value, *dummy):
        if   value.lower() in [ 'mid', 'side', 'off' ]:
            bf_set_midside( value.lower() )
            self.state['midside'] = value.lower()
        else:
            return 'bad option'
        return 'done'

    def get_eq(self, *dummy):
        return yaml.dump( bf_read_eq(), default_flow_style=False )

    def select_source(self, value, *dummy):
        """ this is the source selector """

        def on_change_input_behavior():
            candidate = self.state.copy()
            try:
                for option, value in CONFIG["on_change_input"].items():
                    if value != None:
                        candidate[option] = value
            except:
                print( '(config.yml) missing \'on_change_input\' options' )
            return candidate
        
        def try_select(source):

            if source == 'none':
                jack_clear_preamp()
                return 'done'

            if not source in self.inputs:
                # do nothing
                return f'source \'{source}\' not defined'

            # clearing 'preamp' connections
            jack_clear_preamp()

            # connecting the new SOURCE to PREAMP input
            jack_connect_bypattern( CONFIG['sources'][source]['capture_port'],
                                    'pre_in' )

            # connecting also to the MONITORS:
            if CONFIG["source_monitors"]:
                for monitor in CONFIG["source_monitors"]:
                    jack_connect_bypattern( CONFIG['sources'][source]['capture_port'],
                                            monitor )

            # last, trying to set the desired xo for this source 
            try:
                xo = CONFIG["sources"][source]['xo']
            except:
                return 'done'

            if not xo:
                return 'done'

            else:
                c = Convolver()
                if c.set_xo( xo ) == 'done':
                    self.state['xo_set'] = xo
                    del(c)
                    return 'done'
                else:
                    del(c)
                    return f'\'xo: {xo}\' in \'{source}\' is not valid'


        result = try_select(value)
        if result:
            self.state['input'] = value
            self._validate( on_change_input_behavior() )
            return result
        else:
            return f'something was wrong selecting \'{value}\''

    def get_inputs(self, *dummy):
        return '\n'.join( self.inputs )
        
# THE CONVOLVER: DRC and XO Brutefir stages management =========================

class Convolver(object):
    """ attributes:

            drc_coeffs      list of pcm FIRs for DRC
            xo_coeffs       list of pcm FIRs for XOVER
            drc_sets        sets of FIRs for DRC
            xo_sets         sets of FIRs for XOVER
            ways            filtering stages (loudspeaker ways)

        methods:

            set_drc
            set_xo
            
            get_drc_sets
            get_xo_sets
    """

    def __init__(self):

        # DRC pcm files must be named:
        #    drc.X.DRCSETNAME.pcm   where X must be L | R
        #
        # XO pcm files must be named:
        #   xo.XX[.C].XOSETNAME.pcm     where XX must be:  fr | lo | mi | hi | sw
		#								and channel C is **OPTIONAL**
        #                               can be: L | R 
        #   Using C allows to have dedicated FIR per channel if necessary  

        files   = os.listdir(LSPK_FOLDER)
        coeffs  = [ x.replace('.pcm','') for x in files ]
        self.drc_coeffs = [ x for x in coeffs if x[:4] == 'drc.'  ]
        self.xo_coeffs  = [ x for x in coeffs if x[:3] == 'xo.'   ]
        #print('\nxo_coeffs:', xo_coeffs) # debug
        
        # The available DRC sets
        self.drc_sets = []
        for drc_coeff in self.drc_coeffs:
            drcSetName = drc_coeff[6:]
            if not drcSetName in self.drc_sets:
                self.drc_sets.append( drcSetName )

        # The available XO sets, i.e the last part of a xo_coeff
        self.xo_sets = []
        for xo_coeff in self.xo_coeffs:
            xoSetName = xo_coeff.split('.')[-1]
            if not xoSetName in self.xo_sets:
                self.xo_sets.append( xoSetName )
        #print('xo_sets:', self.xo_sets) # debug
        
        # Ways are the XO filter stages definded inside brutefir_config
        # 'f.WW.C' where WW:fr|lo|mi|hi|sw and C:L|R 
        self.ways = get_brutefir_config('ways')
        # print('ways:', self.ways) # debug
        
    # Bellow we use *dummy to accommodate the pasysctrl.py parser mechanism wich
    # will include two arguments for any function call, even when not necessary. 

    def set_drc(self, drc, *dummy):
        if drc in self.drc_sets or drc == 'none':
            bf_set_drc( drc )
            return 'done'
        else:
            return f'drc set \'{drc}\' not available'

    def set_xo(self, xo_set, *dummy):
        if xo_set in self.xo_sets:
            bf_set_xo( self.ways, self.xo_coeffs, xo_set )
            return 'done'
        else:
            return f'xo set \'{xo_set}\' not available'

    def get_drc_sets(self, *dummy):
        return '\n'.join( self.drc_sets)

    def get_xo_sets(self, *dummy):
        return '\n'.join( self.xo_sets)


# JCLI: THE CLIENT INTERFACE TO THE JACK SERVER ================================
# IMPORTANT: this module core.py needs JACK to be running.

try:
    JCLI = jack.Client('tmp', no_start_server=True)
except:
    print( '(core.py) ERROR cannot commuticate to the JACK SOUND SERVER.' )

# COMMON USE VARIABLES: ========================================================

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

