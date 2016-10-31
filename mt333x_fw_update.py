#!/usr/bin/env python
# mt333x_fw_update.py - Tool to update firmware of MT333x based GPS device
#
# Copyright (c) 2016, David Imhoff <dimhoff.devel@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the author nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# NOTE: This has only been tested with MT3339 based module from GlobalTop.
# I also don't know if it works for the broader MT33xx range of products(ie.
# MT3329).
#
import argparse
import os.path
import sys

from mt333x_helpers import MtkGpsBRom, DownloadAgent

VERSION_MAJOR=0
VERSION_MINOR=1

def report_progress(cnt, total):
    """Display progress to stdout"""
    sys.stdout.write("{:3}% {}/{}\r".format(cnt * 100 / total, cnt, total))
    sys.stdout.flush()
    if cnt == total:
        print('')

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
            description='Update firmware of a MT333x based GPS chip.',
            epilog="Note: Baud rate detection and switching isn't always "
            "working properly. In case the device can not be restarted into "
            "boot ROM mode then set the --baud and --nmea-baud options to "
            "the default baud rate of the current firmware")
    parser.add_argument('serial_port', help='path of serial port device')
    parser.add_argument('da_file', help='Path to MTK Download Agent')
    parser.add_argument('firmware_file', help='path to firmware to flash')

    parser.add_argument('-b', '--baud',
            dest="baud", type=int, choices=(912600, 460800, 230400, 115200, 57600,
                38400, 19200, 14400, 9600, 4800), default=115200,
            help='Use given baud rate for Boot ROM communication.'
                 'Default: 115200')
    parser.add_argument('--nmea-baud',
            dest="nmea_baud", type=int, choices=(115200, 57600, 38400, 19200, 14400,
                9600, 4800),
            help='Use given baud rate for NMEA communication. '
                 'Default: auto detect')
    parser.add_argument('--dtr-reset',
            dest="dtr_reset", default=False, action="store_true",
            help='Use serial DTR signal to toggle NReset line to reset target.')
    parser.add_argument('--version',
            action='version',
            version='%(prog)s {}.{}'.format(VERSION_MAJOR, VERSION_MINOR))

    args = parser.parse_args()

    if not os.path.isfile(args.da_file):
        raise RuntimeError("Unable to find DownloadAgent file")

    # Read in firmware file
    with open(args.firmware_file, "rb") as fw_file:
        fw_data = fw_file.read()

    # Connect to Boot Rom
    brom = MtkGpsBRom(args.serial_port, baud=args.baud,
            nmea_baud=args.nmea_baud,
            dtr_reset=args.dtr_reset)
    da = DownloadAgent(brom)
    da.set_progress_callback(report_progress)

    print("Starting Boot ROM")
    brom.start()

    print('')
    print("Loading DA:")
    da.start(args.da_file)

    print('')
    print("DA Info:")
    print('--------')
    da.print_info()

    if args.baud > 115200:
        da.set_baud_rate(args.baud)

    da._set_mem_block(0, len(fw_data))

    print('')
    print("Writing new firmware:")
    da._write_data(fw_data)

    da.restart()

if __name__ == '__main__':
    main()
