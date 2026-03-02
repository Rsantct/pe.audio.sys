#!/usr/bin/env python3

"""

$ journalctl -b | grep scsi

ago 18 16:41:12 salon64 kernel: scsi host6: usb-storage 2-1.2:1.0
ago 18 16:41:12 salon64 kernel: scsi host7: usb-storage 1-2:1.0
ago 18 16:41:12 salon64 kernel: scsi 0:0:0:0: Direct-Access     ATA      KINGSTON SV300S3 BBF0 PQ: 0 ANSI: 5
ago 18 16:41:12 salon64 kernel: sd 0:0:0:0: Attached scsi generic sg0 type 0
ago 18 16:41:12 salon64 kernel: scsi 6:0:0:0: CD-ROM            Apple    SuperDrive       2.00 PQ: 0 ANSI: 0
ago 18 16:41:12 salon64 kernel: sr 6:0:0:0: [sr0] scsi3-mmc drive: 24x/24x writer cd/rw xa/form2 cdda tray
ago 18 16:41:12 salon64 kernel: sr 6:0:0:0: Attached scsi CD-ROM sr0
ago 18 16:41:12 salon64 kernel: sr 6:0:0:0: Attached scsi generic sg1 type 5
ago 18 16:41:12 salon64 kernel: scsi 7:0:0:0: CD-ROM            PIONEER  BD-RW   BDR-TD04 1.01 PQ: 0 ANSI: 0
ago 18 16:41:12 salon64 kernel: sr 7:0:0:0: [sr1] scsi3-mmc drive: 62x/62x writer dvd-ram cd/rw xa/form2 cdda tray
ago 18 16:41:12 salon64 kernel: sr 7:0:0:0: Attached scsi CD-ROM sr1
ago 18 16:41:12 salon64 kernel: sr 7:0:0:0: Attached scsi generic sg2 type 5


BUT SOMETIMES the SuperDrive appears as follow:
ago 18 22:36:41 salon64 kernel: scsi 6:0:0:0: CD-ROM            HL-DT-ST DVDRW  GX40N     RQ00 PQ: 0 ANSI: 0

"""

import sys
import subprocess as sp


def get_journal_scsi():
    try:
        cmd = 'journalctl -b | grep scsi'
        return sp.check_output(cmd, shell=True).decode().split('\n')

    except:
        if VERBOSE:
            print(f'ERROR with journalctl')
        return []


def get_device():

    dev = ''

    lines = get_journal_scsi()

    if not lines:
        return dev

    scsi = ''
    for line in lines:

        if 'SuperDrive' in line or 'GX40N' in line:
            scsi = line.split(' scsi ')[-1].split()[0][:-1]

        if scsi:
            if scsi in line and 'Attached' in line and 'CD-ROM' in line:
                dev = f'/dev/{line.split()[-1]}'
                break

    if not '/dev/sr' in dev:
        if VERBOSE:
            print(f'WEIRD device: {dev}')

    return dev


def link2cdrom():
    """ needs sudo
    """
    superdrive = get_device()
    if superdrive:
        cmdline = f'sudo ln -s -f {superdrive} /dev/cdrom'
        sp.Popen(cmdline, shell=True)


if __name__ == "__main__":

    VERBOSE = False
    mode = 'get_devide'

    for opc in sys.argv[1:]:

        if 'eject' in opc:
            mode = 'eject'

        if 'link' in opc:
            link2cdrom()
            sys.exit()

        elif '-v' in opc:
            VERBOSE = True

    device = get_device()

    if device:

        if mode == 'eject':
            if VERBOSE:
                print(f'ejecting {device}')
            sp.Popen(f'eject {device}', shell=True)
        else:
            print(device)

    else:
        if VERBOSE:
            print('Apple SuperDrive NOT FOUND')
