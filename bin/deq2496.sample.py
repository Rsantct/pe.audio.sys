#!/usr/bin/env python3
"""
    usage: deq2496.py cmd args*

    commands available:

            show        rta | vu | peak
            contrast    0...15
            request     device_id

"""
import sys
import rtmidi
import mido

### (i) USER CONFIG, provide a string to identify your midi interface,
#       see an example:
#   $ python3
#   Python 3.6.9 (default, Apr 18 2020, 01:56:04)
#   [GCC 8.4.0] on linux
#   Type "help", "copyright", "credits" or "license" for more information.
#   >>> import mido
#   >>> mido.get_output_names()
#   ['ESI-ROMIO:ESI-ROMIO MIDI 1 28:0', ...]
myMIDIstr = 'ESI-ROMIO'

#   See write single value table at
#   DEQ2496_MIDI_Implementation_V1_4.pdf
#                   [modnr, lrmode, offset, datalen, data]
wsv_table = {
    'rta':                  [127, 0,  0, 1,  9],
    'rta_page3_fullscreen': [9,   0,  0, 1,  3],
    'rta_channel_l':        [9,   0,  1, 1,  0],
    'rta_channel_r':        [9,   0,  1, 1,  1],
    'rta_channel_l+r':      [9,   0,  1, 1,  2],
    'rta_max-5dB':          [9,   0,  2, 1,  1],
    'rta_range_60dB':       [9,   0,  4, 1,  2],
    'rta_rate_mid':         [9,   0,  9, 1,  1],
    'rta_peak_mid':         [9,   0, 10, 1,  2],

    'meter':                [127, 0,  0, 1, 12],
    'meter_page1_peak_rms': [12,  0,  0, 1,  1],
    'meter_page2_spl':      [12,  0,  0, 1,  2],
    'meter_page3_vumeter':  [12,  0,  0, 1,  3],

    'contrast_8':           [  8, 0,  1, 1,  8]
    }


def get_midi_interface(devName):
    ifces = mido.get_output_names()
    result = ''
    for i in ifces:
        if devName in i:
            result = i
            break
    if result:
        return result
    else:
        raise Exception(f'No midi matching {devName}')


def send_SysEx(x):
    #print(x)
    deq_header = [0x00, 0x20, 0x32, 0x00, 0x12]
    msg = mido.Message('sysex', data=deq_header + x)
    outport.send(msg)


def write_single_value(sv):
    #  0x22: write single value (see table)
    #  Format: 0xF0, 0x00, 0x20, 0x32, DeviceID, ModelID,
    #          0x22, modnr, lrmode, offset, datalen, data*, 0xF7
    #      modnr: number of module (0-12)
    #      lrmode: channel mode: dual mono or stereo (0,1)
    #      offset: offset to first value
    #      datalen: size of data* (1 or 2)
    #      data*: value
    #
    # sv must be a list: [modnr, lrmode, offset, datalen, data]
    sv = [0x22] + sv
    send_SysEx(sv)


def get_identity_device():
    # 0x01: identify device
    # Format: 0xF0, 0x00, 0x20, 0x32, DeviceID, ModelID, 0x01, 0xF7
    # Response: 0xF0, 0x00, 0x20, 0x32, 0x00, 0x12, 0x02, asciidata*, 0xF7
    # asciidata*: n ascii characters identifying the product and software version
    #             also a tail 0x00 char is includes at the end
    send_SysEx([0x01])
    ans = inport.receive().data[6:-1]  # data excludes 0xF0 head and 0xF7 tail
    result = ''
    for c in ans:
        result += chr(c)
    return result


def show_screen(scr_name):
    # a short name alias
    wsv = write_single_value

    if scr_name == 'rta':
        wsv( wsv_table['rta'] )
        wsv( wsv_table['rta_channel_l+r'] )
        wsv( wsv_table['rta_max-5dB'] )
        wsv( wsv_table['rta_range_60dB'] )
        wsv( wsv_table['rta_rate_mid'] )
        wsv( wsv_table['rta_peak_mid'] )
        wsv( wsv_table['rta_page3_fullscreen'] )

    elif scr_name == 'vu':
        wsv( wsv_table['meter'] )
        wsv( wsv_table['meter_page3_vumeter'] )

    elif scr_name == 'peak':
        wsv( wsv_table['meter'] )
        wsv( wsv_table['meter_page1_peak_rms'] )

def contrast(c):
    # a short name alias
    wsv = write_single_value

    ncontrast = wsv_table['contrast_8']
    ncontrast[-1] = c
    wsv( ncontrast )

if __name__ == '__main__':

    inport  = mido.open_input( get_midi_interface( myMIDIstr ) )
    outport = mido.open_output( get_midi_interface( myMIDIstr ) )

    # Read command line
    cmd = ''
    args = []
    if sys.argv[1:]:
        cmd = sys.argv[1]
        if sys.argv[2:]:
            args = sys.argv[2:]
    else:
        print(__doc__)

    if cmd == 'show':
        show_screen( args[0] )

    if cmd == 'contrast':
        contrast( int(args[0]) )

    if cmd == 'request':
        if args[0] == 'device_id':
            print( get_identity_device() )
