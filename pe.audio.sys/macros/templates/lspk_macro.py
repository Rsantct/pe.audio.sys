#!/usr/bin/env python3
"""
    ACHTUNG: this is a purely geek template  :-P

    A module to load a new loudspeaker always attached to the same
    sound card audio interface, so JACK process will keep untouch.

    Just will load a new config.yml and restarting Brutefir accordingly
    as per loudspeakers/XXXXX/brutefir_config

    You need to define MY_LSPK before calling main(), for example:

        MY_LSPK = { 'name':     'cardiojorns',
                    'drc_set':  'sofa',
                    'xo_set':   'lp'            }

"""

#### DETAILS:
#
#    (i) FOA please prepare a set of copies of config.yml,
#        appropriately configured and named "config.yml.YOURLSPK",
#        for example:
#
#           config.yml.dipocardiojorns
#           config.yml.DynC5+AMRsub
#
#       Example in differences::
#           > loudspeaker:      dipocardiojorns         DynC5+AMRsub
#           > init_xo:          mp                      mp_60Hz
#           < init_drc:         estant_mp               lp_c5+sub_multip
#           > ecasound_peq.py:  dj_estant.ecs           -not set-
#
#    Macro procedure:
#
#       1-  Stop preamp.py service to release .state
#       2-  Stop ecasound plugin
#       3-  Stop Brutefir process
#       4-  Copy config.yml.YOURLSPK --> config.yml
#       5-  Adjust .state so that resuming audio settings later works properly.
#       5a- Redrawing drc.png for web page
#       6-  Restart Brutefir (cd to your lspk folder)
#            (!) be SURE that your brutefir_config has a 50 dB initial level atten.
#       7-  Restart ecasound plugin if necessary
#       8-  Restart the server
#       9-  If config.yml 'on_init:' section indicates any drc or xo ,
#           we still need to set the wanted here lspk_A/B
#      10-  Restoring the source
#      11-  Restoring audio settings


import  os
import  sys
from    subprocess  import Popen, call
import  yaml
import  json
from    time        import sleep
from    shutil      import copyfile


ME = __file__.split('/')[-1]

UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'
SERVERPATH = f'{MAINFOLDER}/share/miscel/server.py'
CONFIGPATH = f'{MAINFOLDER}/config/config.yml'

sys.path.append( f'{MAINFOLDER}/share/miscel' )

from    miscel import   CONFIG, STATE_PATH, Fmt, kill_bill, \
                        send_cmd, read_state_from_disk


def main(verbose=False):

    # Kill any previous process of this
    kill_bill( os.getpid() )


    # Turning on AMPS if needed
    #   regleta OUTLETS:
    #   {1: 'DAC', 2: 'AmpLO+HI+SUB', 3: 'DEQ2496', 4: 'N-Core'}
    if 'DynC5' in MY_LSPK["name"]:
        Popen( f'{UHOME}/bin/regleta.py on 1 4'.split() )
    elif 'jorns' in MY_LSPK["name"]:
        Popen( f'{UHOME}/bin/regleta.py on 2'.split() )


    #  Macro procedure:

    # 0- Reading pe.audio.sys configuration
    OLD_CONFIG  = yaml.safe_load( open(CONFIGPATH, 'r') )

    # 1- Stop pe.audio.sys server (the owner of .state)
    Popen( f'{UHOME}/bin/peaudiosys_server_restart.sh stop'.split() )


    # 2- Stop ecasound plugin
    ecasound_in_use = False
    for item in OLD_CONFIG["plugins"]:
        if 'ecasound_peq.py' in item:
            ecasound_in_use = True
    if ecasound_in_use:
        Popen( f'{MAINFOLDER}/share/plugins/ecasound_peq.py stop'.split() )


    # 3- Stop Brutefir process, previously will keep the current
    #    extra delay in case of any multiroom listener had set it up.
    extra_delay = read_state_from_disk()["extra_delay"]
    Popen( f'pkill -f -KILL brutefir'.split() )
    sleep(.25)


    # 4- Copy config.yml.YOURLSPK --> config.yml
    copyfile( f'{MAINFOLDER}/config/config.yml.{MY_LSPK["name"]}',
              f'{MAINFOLDER}/config/config.yml')
    NEW_CONFIG = yaml.safe_load( open(CONFIGPATH,'r') )


    # 5- Adjust .state so that resuming audio settings later works properly.
    new_state = read_state_from_disk()
    new_state["drc_set"] = MY_LSPK["drc_set"]
    new_state["xo_set"]  = MY_LSPK["xo_set"]
    new_state["target"]  = NEW_CONFIG["on_init"]["target"]
    with open(STATE_PATH, 'w') as f:
        f.write( json.dumps(new_state) )


    # 5a- Forcing to redraw drcXXX.pngs for web page in background.
    #     OBSOLETE Must remove previous because loudspeakers might share drc set names)
    #              Popen("rm ~/pe.audio.sys/share/www/images/drc*", shell=True)
    Popen("python3 ~/pe.audio.sys/share/www/scripts/drc2png.py", shell=True)

    # 6- Restart Brutefir (needs cd to your lspk folder)
    #    (!!!) BE SURE that your brutefir_config has 50dB initial level atten.
    os.chdir( f'{MAINFOLDER}/loudspeakers/{MY_LSPK["name"]}' )
    Popen( 'brutefir brutefir_config'.split() )
    os.chdir( UHOME )
    sleep(.33)
    Popen( 'jack_connect pre_in_loop:output_1 brutefir:in.L'.split() )
    Popen( 'jack_connect pre_in_loop:output_2 brutefir:in.R'.split() )


    # 7- Restart ecasound plugin if necessary
    #    ( ecasound_eq.py will automagically insert it before Brutefir ports )
    ecasound_wanted = False
    for item in NEW_CONFIG["plugins"]:
        if 'ecasound_peq.py' in item:
            ecasound_wanted = True
    if ecasound_wanted:
        Popen( f'{MAINFOLDER}/share/plugins/ecasound_peq.py start'.split() )


    # 8- Restart the server
    call( f'pkill -KILL -f "server.py\ peaudiosys"', shell=True)  # call is blocking
    SRV_HOST = CONFIG['peaudiosys_address']
    SRV_PORT = CONFIG['peaudiosys_port']
    Popen( f'python3 {SERVERPATH} peaudiosys {SRV_HOST} {SRV_PORT} >/dev/null 2>&1',
           shell=True)
    ans = ''
    times = 50      # 50 * 0.2 s = 10 s
    while times:
        ans = send_cmd('state')
        try:
            if 'level' in ans:
                sleep(.2)
                break
        except:
            pass
        sleep(.2)
        times -= 1
    if not times:
        print( f'{Fmt.BOLD}({ME}) ERROR with pe.audio.sys server :-/{Fmt.END}' )
        sys.exit()
    else:
        print( f'{Fmt.BLUE}({ME}) pe.audio.sys server restarted.{Fmt.END}' )


    # 9- If config.yml 'on_init:' section indicates any drc or xo ,
    #     we still need to set the wanted here at the very beginning
    #     for lspk_A or lspk_B
    send_cmd( f'preamp set_drc  {MY_LSPK["drc_set"]}',         verbose=verbose )
    send_cmd( f'preamp set_xo   {MY_LSPK["xo_set"]}',          verbose=verbose )
    send_cmd( f'preamp subsonic {NEW_CONFIG["on_init"]["subsonic"]}',
                                                                verbose=verbose )

    # 10- Restoring the source
    send_cmd( f'preamp input  {new_state["input"]}',   verbose=verbose )

    # 11- Restoring audio settings
    #     NOTICE: extra delay can be wrong if remote expects a different xo (mp/lp),
    #             so remote listener may need to to recall its own macro.
    send_cmd( f'preamp add_delay    {extra_delay}',                 verbose=verbose )
    send_cmd( f'preamp level        {new_state["level"]}',          verbose=verbose )
    send_cmd( f'preamp lu_offset    {new_state["lu_offset"]}',      verbose=verbose )
    send_cmd( f'preamp loudness     {new_state["equal_loudness"]}', verbose=verbose )
    send_cmd( f'preamp midside      {new_state["midside"]}',        verbose=verbose )
    send_cmd( f'preamp bass         {new_state["bass"]}',           verbose=verbose )
    send_cmd( f'preamp treble       {new_state["treble"]}',         verbose=verbose )
    send_cmd( f'preamp balance      {new_state["balance"]}',        verbose=verbose )
    send_cmd( f'preamp set_target   {new_state["target"]}',         verbose=verbose )

    # 12- Display warning
    send_cmd( f'aux warning set LSPK: {MY_LSPK["name"]}' )
    send_cmd(  'aux warning expire 5' )

