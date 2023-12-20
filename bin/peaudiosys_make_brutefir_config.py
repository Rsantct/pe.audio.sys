#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A script to make a Brutefir config file from the
    files found in the loudspeaker folder.

    Usage:

     peaudiosys_make_brutefir_config.py <loudspeaker_name> [ options ]

        -fs=N         Sampling rate, default 44100 Hz
        -flength=N    Filter length, default 16384 taps
        -dither=X     Output dither  true (default) | false
        -nodumpeq     Disables dumping rendering eq logic


"""

import sys, os
import pathlib
UHOME = os.path.expanduser("~")

FREQPATH = f'{UHOME}/pe.audio.sys/share/eq/freq.dat'


EQ_CLI = \
'''
# THE EQ & CLI MODULES
logic:

# The Command Line Interface server TCP port
"cli" { port: 3000; },

# The eq module provides a filter coeff to render a run-time EQ.
# (i) Bands here must match with the ones in your xxxxfreq.dat file.
"eq" {
    debug_dump_filter: "/tmp/brutefir-rendered-%d";
    {
        coeff: "c.eq";

        bands:
BANDS
    };
};

'''

R20_BANDS = """
            10, 11.2, 12.5, 14, 16, 18, 20, 22.4, 25, 28, 31.5,
            35.5, 40, 45, 50, 56, 63, 71, 80, 90, 100, 112,
            125, 140, 160, 180, 200, 224, 250, 280, 315, 355,
            400, 450, 500, 560, 630, 710, 800, 900, 1000,
            1120, 1250, 1400, 1600, 1800, 2000, 2240, 2500,
            2800, 3150, 3550, 4000, 4500, 5000, 5600, 6300,
            7100, 8000, 9000, 10000, 11200, 12500, 14000, 16000,
            18000, 20000;
"""

GENERAL_SETTINGS = \
'''
# GENERAL SETTINGS

sampling_rate:      FS ;
filter_length:      FLENGTH ;
float_bits:         32 ;
overflow_warnings:  true ;
allow_poll_mode:    false ;
monitor_rate:       true ;
powersave:          -80 ;
lock_memory:        true ;
show_progress:      false ;

'''

IO = \
'''
# I/O

input "in.L", "in.R" {
    # does not connect inputs in jack:
    device:   "jack" { clientname: "brutefir";
                       ports: ""/"in.L", ""/"in.R"; };
    sample:   "AUTO";
    channels: 2/0,1;
};

output OUTPUTS_LIST {
    # hardwire to Jack sound card:
    device: "jack" { ports:
        PORTS_MAP;
    };
    sample:   "AUTO";
    channels: CHANNELS_LIST;
    maxdelay: 10000; # about 200 ms for multiroom compensation
    dither:   DITHER;
    delay:    DELAY_LIST
};

'''

COEFF_EQ = \
"""
# COEFFs for EQ & LOUDNESS
# 1 block length is enough because smooth eq curves

coeff "c.eq" {
    filename: "dirac pulse";
    shared_mem: true;
    blocks: 1;
};

"""

COEFF_DRC_HEADER = \
'''
# COEFFs for DRC
# PCMs found under the loudspeaker folder
'''

COEFF_DRC = \
'''
coeff "drc.C.NAME" {
    filename:    "drc.C.NAME.pcm";
    format:      "FLOAT_LE";
    shared_mem:  false;
    attenuation: 0;
};

'''

COEFF_XO_HEADER = \
'''
# COEFFs for XO
# PCMs found under the loudspeaker folder
'''

COEFF_XO = \
'''
coeff "xo.XONAME" {
    filename:    "xo.XONAME.pcm";
    format:      "FLOAT_LE";
    shared_mem:  false;
    attenuation: 0;
};

'''

FILTERS_LEV_EQ_DRC = \
'''
# CONVOLVER:  level filter
# Not a filter just for level and channel routing purposes
# (i) Initial 50 dB atten for a safe startup

filter "f.lev.L" {
    from_inputs:  "in.L"/50.0/1, "in.R"//0;
    to_filters:   "f.eq.L";
    coeff:        -1;
};

filter "f.lev.R" {
    from_inputs:  "in.L"//0, "in.R"/50.0/1;
    to_filters:   "f.eq.R";
    coeff:        -1;
};


# CONVOLVER:  EQ filters

filter "f.eq.L" {
    from_filters: "f.lev.L";
    to_filters:   "f.drc.L";
    coeff:        "c.eq";
};

filter "f.eq.R" {
    from_filters: "f.lev.R";
    to_filters:   "f.drc.R";
    coeff:        "c.eq";
};

# CONVOLVER: DRC filters

filter "f.drc.L" {
    from_filters: "f.eq.L";
    to_filters:   LFILTERS;
    coeff:        -1;
};

filter "f.drc.R" {
    from_filters: "f.eq.R";
    to_filters:   RFILTERS;
    coeff:        -1;
};

'''

FILTERS_HEADER = \
'''
# CONVOLVER: XOVER filters
'''

FILTER_STEREO = \
'''
filter "f.WAY.CH" {
    from_filters: "f.drc.CH";
    to_outputs:   "WAY.CH"/0.0/+1;
    coeff:        "xo.WAY.mp";
};
'''

FILTER_SUB = \
'''
filter "f.sw" {
    from_filters: "f.drc.L"/3.0, "f.drc.R"/3.0;
    to_outputs:   "sw"/0/+1;
    coeff:        "xo.sw.mp";
};
'''


def get_freqs():
    """ get freqs from the share/eq folder
    """

    try:
        with open(FREQPATH, 'r') as f:
            tmp = f.read()

        freqs = [round(float(f),3) for f in tmp.split() if f]

    except Exception as e:
        freqs = []
        print(f'ERROR reading: {FREQPATH}')

    return freqs


def make_bands_str(freqs):

    maxlen = 9

    lines = '\n'
    i = 0
    while True:
        line = [ x for x in freqs[i: i + maxlen] ]
        line = ', '.join( [ str(x).replace('.0', '') for x in line ] )
        if line:
            line = ' ' * 12 + line  + ',\n'
            lines += line
        else:
            break
        i += maxlen

    return lines[:-2] + ';\n'


def get_ways():
    """ get WAYS from loudspeaker's folder files
    """

    WAYS = []

    for fname in LSPKFILES:
        if fname.startswith('xo.'):
            way = fname[3:5]
            if way not in WAYS:
                WAYS.append( way )

    WAYS.sort( key=lambda x: ('lo', 'mi', 'hi', 'sw').index(x) )

    if not WAYS:
        WAYS = ['fr']
        global fr_is_dummy
        fr_is_dummy = True

    return WAYS


def do_GENERAL_SETTINGS():
    tmp = GENERAL_SETTINGS
    tmp = tmp.replace('FS', fs)
    tmp = tmp.replace('FLENGTH', flength)
    return tmp


def do_IO():

    if not dither in ('true', 'false'):
        print('Bad dither must be true or false')
        sys.exit()

    IO_tmp  = IO.replace('DITHER', dither)

    if 'fr' in WAYS and ('lo' in WAYS or 'hi' in WAYS or 'mi' in WAYS):
        print('BAD xo.xx FILES')
        sys.exit()

    outs_list   = ''
    ports_map   = ''
    pcounter    = 1

    # the order matters
    for wname in 'fr', 'lo', 'mi', 'hi':
        if wname in WAYS:
            outs_list += f'"{wname}.L", "{wname}.R", '
            ports_map += f'"system:playback_{pcounter}"/"{wname}.L", '
            pcounter += 1
            ports_map += f'"system:playback_{pcounter}"/"{wname}.R", '
            pcounter += 1
            ports_map += '\n        '

    for wname in WAYS:
        if 'sw' in wname:
            outs_list += f'"{wname}", '
            ports_map += f'"system:playback_{pcounter}"/"{wname}", '
            pcounter += 1

    outs_list = outs_list.rstrip()[:-1]
    ports_map = ports_map.rstrip()[:-1]

    IO_tmp = IO_tmp.replace('OUTPUTS_LIST', outs_list)
    IO_tmp = IO_tmp.replace('PORTS_MAP',    ports_map)

    global delay_list

    delay_list  = f''
    chann_list  = f'{pcounter - 1}/'

    for i in range( pcounter - 1 ):
        chann_list += f'{i}, '
        delay_list += '0, '

    chann_list = chann_list.rstrip()[:-1]
    delay_list = delay_list.rstrip()[:-1]
    tmp = delay_list + f'; {notice_delay2ms(delay_list)}'

    IO_tmp = IO_tmp.replace('CHANNELS_LIST', chann_list)
    IO_tmp = IO_tmp.replace('DELAY_LIST',    tmp)

    return IO_tmp


def do_DRC_COEFFS():

    tmp = COEFF_DRC_HEADER

    drcs = []
    for fname in LSPKFILES:
        if fname.startswith('drc.'):
            drc = fname[4:-4]
            if drc not in drcs:
                drcs.append( drc )

    drcs.sort()

    for drc in drcs:
        tmp += COEFF_DRC.replace('C.NAME', drc)

    return tmp


def do_XO_COEFFS():
    """
        xo.XX[.C].XOSETNAME.pcm   where XX must be:  fr | lo | mi | hi | sw
                                  and channel C is OPTIONAL, can be: L | R
    """
    tmp = COEFF_XO_HEADER

    xos = []
    for fname in LSPKFILES:
        if fname.startswith('xo.'):
            xo = fname[3:-4]
            if xo not in xos:
                xos.append( xo )

    xos.sort()

    for xo in xos:
        tmp += COEFF_XO.replace('XONAME', xo)

    return tmp


def do_FILTERS_LEV_EQ_DRC():

    tmp = FILTERS_LEV_EQ_DRC;
    lfilters = ''
    rfilters = ''

    for way in WAYS:
        if 'sw' not in way:
            lfilters += f'"f.{way}.L", '
            rfilters += f'"f.{way}.R", '
        else:
            lfilters += f'"f.{way}", '
            rfilters += f'"f.{way}", '

    tmp = tmp.replace( 'LFILTERS', lfilters[:-2] )
    tmp = tmp.replace( 'RFILTERS', rfilters[:-2] )

    return tmp


def do_FILTERS():

    tmp = FILTERS_HEADER

    for way in WAYS:

        if not 'sw' in way:
            for ch in 'L', 'R':
                tmp += FILTER_STEREO.replace('CH', ch).replace('WAY', way)
        else:
            tmp += FILTER_SUB

    if fr_is_dummy:
        tmp = tmp.replace('"xo.fr.mp"', '-1')

    return tmp


def notice_delay2ms(delay_list):
    """ Translates samples to ms
    """
    delays = [ int(x) for x in delay_list.split(',') ]
    notice = '# samples ~ xxx ms'

    tmp = ''
    for d in delays:
        ms = round(d / int(fs) * 1000, 1)
        tmp += f'{ms}, '
    tmp = tmp.rstrip()[:-1]

    notice = notice.replace('xxx', tmp)
    return notice


def main():

    tmp = EQ_CLI.replace('BANDS', R20_BANDS[1:-1]).lstrip()

    if disable_dump:
        tmp = tmp.replace('debug_dump_filter', '#debug_dump_filter')

    tmp += do_GENERAL_SETTINGS()
    tmp += do_IO()
    tmp += COEFF_EQ
    tmp += do_DRC_COEFFS()
    tmp += do_XO_COEFFS()
    tmp += do_FILTERS_LEV_EQ_DRC()
    tmp += do_FILTERS()

    out_fname = f'{LSPKFOLDER}/brutefir_config_draft'
    with open(out_fname, 'w') as f:
        f.write(tmp)

    print()
    print(f'(i) \'brutefir_config_draft\' has been saved to:')
    print(f'    {LSPKFOLDER}/\n' )

    print(f'    Fs:             {fs}')
    print(f'    Filter lenght:  {flength}')
    print(f'    Output dither:  {dither}')
    print(f'    Outputs delay:  {delay_list} {notice_delay2ms(delay_list)}\n')

    print(f'(!) Check carefully:')
    print(f'    - The sampling rate match the one from your .pcm files')
    print(f'    - Soundcard channels mapping and delays')
    print(f'    - Attenuation for each coefficent if needed.')
    print(f'    - \'to_outputs\': polarity and attenuation for each way.\n')


if __name__ == '__main__':

    fs              = '44100'
    flength         = '16384'
    dither          = 'true'
    disable_dump    = False
    fr_is_dummy     = False


    if len( sys.argv ) > 1:
        lspkName = sys.argv[1]
    else:
        print(__doc__)
        sys.exit()

    for opc in sys.argv[2:]:

        if '-fs=' in opc:
            fs = opc[4:]

        elif '-flen' in opc:
            flength = opc.split('=')[-1]

        elif '-dither' in opc:
            dither = opc.split('=')[-1]

        elif '-nodump' in opc:
            disable_dump = True


    freqs = get_freqs()
    if freqs:
        R20_BANDS = make_bands_str(freqs)
        print(f'(i) Using eq bands from: {FREQPATH}')
    else:
        print(f'(i) Using eq bands from predefined R20 bands.')


    LSPKFOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{lspkName}'

    LSPKFILES = []
    entries = pathlib.Path(LSPKFOLDER)
    for entry in entries.iterdir():
        LSPKFILES.append(entry.name)

    WAYS = get_ways()

    main()
