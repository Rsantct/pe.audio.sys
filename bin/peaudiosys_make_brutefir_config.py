#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A script to make a Brutefir config file from the
    pcm files found in the loudspeaker folder.

    Usage:

     peaudiosys_make_brutefir_config.py <YOUR_LSPK> [ options ]

        -fs=N         Sampling rate, default 44100 Hz

        -flength=N    Filter length, default '16384'
                      (Also as partitioned form: '4096,4')

        -dither=X     Output dither  true (default) | false

        -nodumpeq     Disables dumping rendering eq logic

        -subsonic     Includes a subsonic filter

        -force        Force to overwrite brutefir_config


    OPTIONAL CONFIG FILE 'loudspeakers/YOUR_LSPK/config.yml'

        Example:

            DRCs:
                sofa:
                    flat_region_dB: -3.5

            XOs:
                fr:
                    gain:       0.0
                    polarity:   +

"""

import pathlib
import yaml
import sys
import os

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

EQ_BANDS = """
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
filter_length:      FLENSTR ;
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

COEFF_SUBSONIC = \
"""
# COEFFs for SUBSONIC
# (i) If partitioned <filter_length>, set <blocks> to cover
#     the 4096 taps from the subsonic.xx.pcm files

coeff "subsonic.mp" {
    filename:    "SUBSONIC_MP";
    format:      "FLOAT_LE";
    shared_mem:  false;
    attenuation: 0;
    blocks:      BLOCKS;
};

coeff "subsonic.lp" {
    filename:    "SUBSONIC_LP";
    format:      "FLOAT_LE";
    shared_mem:  false;
    attenuation: 0;
    blocks:      BLOCKS;
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
    attenuation: ATTEN;
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


def update_eq_bands():
    """ get freqs from the share/eq folder
    """

    global EQ_BANDS

    try:
        with open(FREQPATH, 'r') as f:
            tmp = f.read()

        freqs = [round(float(f),3) for f in tmp.split() if f]
        EQ_BANDS = make_bands_str(freqs)
        print(f'(i) Using eq bands from: {FREQPATH}\n')

    except Exception as e:
        print(f'(!) ERROR reading: {FREQPATH}, using predefined eq R20 bands.\n')


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

    global PSIZE, NUMPA, FLEN

    if not int(FS) in (44100, 48000, 96000):
        print(f'ERROR: Bad fs: {FS} must be in 44100, 48000, 96000')
        sys.exit()

    # Partition size number of partitions and filter length
    if ',' in FLENSTR:
        NUMPA = int( FLENSTR.split(',')[-1].strip() )
    else:
        NUMPA = 1
    PSIZE = int( FLENSTR.split(',')[0].strip() )
    FLEN  = PSIZE * NUMPA


    if not FLEN in (1024, 2048, 4096, 8192, 16384, 32768):
        print(f'ERROR: Bad filter length {FLEN} must be power of 2 and >= 1024')
        sys.exit()

    tmp = GENERAL_SETTINGS
    tmp = tmp.replace('FS', FS)
    tmp = tmp.replace('FLENSTR', FLENSTR)
    return tmp


def do_IO():

    if not DITHER in ('true', 'false'):
        print('ERROR: Bad dither must be true or false')
        sys.exit()

    IO_tmp  = IO.replace('DITHER', DITHER)

    if 'fr' in WAYS and ('lo' in WAYS or 'hi' in WAYS or 'mi' in WAYS):
        print('ERROR: Bad xo.xx FILES')
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

    def get_atten(drc):
        ch, Id = drc.split('.')
        try:
            atten = round( float(CONFIG["DRCs"][Id]["flat_region_dB"]), 1)
        except:
            atten = 0.0
        return atten


    tmp = COEFF_DRC_HEADER

    drcs = []
    for fname in LSPKFILES:
        if fname.startswith('drc.'):
            drc = fname[4:-4]
            if drc not in drcs:
                drcs.append( drc )

    drcs.sort()


    for drc in drcs:
        atten = get_atten(drc)
        tmp += COEFF_DRC.replace('C.NAME', drc).replace('ATTEN', str(atten))

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
        ms = round(d / int(FS) * 1000, 1)
        tmp += f'{ms}, '
    tmp = tmp.rstrip()[:-1]

    notice = notice.replace('xxx', tmp)
    return notice


def do_subsonic():

    global COEFF_SUBSONIC

    SUBSONIC_MP = f'{UHOME}/pe.audio.sys/share/eq/{FS}/subsonic.mp.pcm'
    SUBSONIC_LP = f'{UHOME}/pe.audio.sys/share/eq/{FS}/subsonic.lp.pcm'

    for fname in (SUBSONIC_MP, SUBSONIC_LP):
        if not pathlib.Path(fname).is_file():
            print(f'ERROR: cannot access to: {fname}')
            sys.exit()

    COEFF_SUBSONIC = COEFF_SUBSONIC.replace('SUBSONIC_MP', SUBSONIC_MP)
    COEFF_SUBSONIC = COEFF_SUBSONIC.replace('SUBSONIC_LP', SUBSONIC_LP)

    # Taps for a FLOAT32 pcm file
    filesize = pathlib.Path(SUBSONIC_MP).stat().st_size
    taps = int(filesize / 4)

    nblocks = 1

    if FLEN >= taps:
        while True:
            if nblocks * PSIZE >= taps:
                break
            else:
                nblocks += 1
    else:
        print(f'WARNING: Subsonic {taps} taps < {FLENSTR} filter_length\n')

    COEFF_SUBSONIC = COEFF_SUBSONIC.replace('BLOCKS', str(nblocks))

    return COEFF_SUBSONIC


def read_config():
    """ PENDING to improve
    """

    global CONFIG

    try:
        with open(CONFIGPATH, 'r') as f:
            CONFIG = yaml.safe_load(f)

    except:
        print(f'(i) {LSPKNAME}/config.yml NOT found, using defaults.\n' )


def main():

    tmp = EQ_CLI.replace('BANDS', EQ_BANDS[1:-1]).lstrip()

    if disable_dump:
        tmp = tmp.replace('debug_dump_filter', '#debug_dump_filter')

    tmp += do_GENERAL_SETTINGS()
    tmp += do_IO()
    tmp += COEFF_EQ
    if subsonic:
        tmp += do_subsonic()
    tmp += do_DRC_COEFFS()
    tmp += do_XO_COEFFS()
    tmp += do_FILTERS_LEV_EQ_DRC()
    tmp += do_FILTERS()

    if not force:
        bf_file = 'brutefir_config_draft'
    else:
        bf_file = 'brutefir_config'

    print()
    print(f'(i) \'{bf_file}\' is about to be saved to:')
    print(f'    {LSPKFOLDER}' )
    print()
    print(f'    Fs:                 {FS}')
    print(f'    Filter lenght:      {FLENSTR}')
    print(f'    Output dither:      {DITHER}')
    print(f'    Outputs delay:      {delay_list} {notice_delay2ms(delay_list)}')
    print(f'    Subsonic filter:    {"enabled" if subsonic else "disabled"}')
    print()
    print(f'(!) Check carefully:')
    print(f'    - The sampling rate match the one from your .pcm files')
    print(f'    - Soundcard channels mapping and delays')
    print(f'    - Attenuation for each coefficent if needed.')
    print(f'    - \'to_outputs\': polarity and attenuation for each way.')
    print()

    fout = f'{LSPKFOLDER}/{bf_file}'

    if force:
        ans = input(f'ARE YOU SURE TO OVERWRITE {bf_file}? (y/N) ')
        if ans.lower() != 'y' and ans.lower() != 's':
            print('NOT saved')
            sys.exit()

    with open(fout, 'w') as f:
        f.write(tmp)

    print(f'SAVED to: {fout}')

if __name__ == '__main__':

    FS              = '44100'
    FLENSTR         = '16384'
    DITHER          = 'true'
    subsonic        = False
    disable_dump    = False
    fr_is_dummy     = False
    force           = False


    if len( sys.argv ) > 1:
        LSPKNAME = sys.argv[1]
    else:
        print(__doc__)
        sys.exit()

    for opc in sys.argv[2:]:

        if '-fs=' in opc:
            FS = opc[4:]

        elif '-flength=' in opc:
            FLENSTR = opc.split('=')[-1]

        elif '-dither=' in opc:
            DITHER = opc.split('=')[-1]

        elif '-nodump' in opc:
            disable_dump = True

        elif '-subsonic' in opc:
            subsonic = True

        elif '-force' in opc:
            force = True

        else:
            print(__doc__)
            sys.exit()

    print()


    LSPKFOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{LSPKNAME}'

    CONFIGPATH = f'{UHOME}/pe.audio.sys/loudspeakers/{LSPKNAME}/configx.yml'

    update_eq_bands()

    read_config()

    LSPKFILES = []
    entries = pathlib.Path(LSPKFOLDER)
    for entry in entries.iterdir():
        LSPKFILES.append(entry.name)

    WAYS = get_ways()

    main()
