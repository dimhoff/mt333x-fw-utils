#!/usr/bin/env python
# mt333x_fw_dump.py - Tool to dump firmware from MT333x based device
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
import argparse
import struct
import sys

from mt333x_helpers import MtkGpsBRom, BASE_ADDR_FIRMWARE

VERSION_MAJOR=0
VERSION_MINOR=1

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
            description='Dump firmware from a MT333x based GPS chip.',
            epilog="After using this tool a reset of the chip is "
            "required to get out of Boot ROM mode. "
            "KNOWN ISSUE: If the device doesn't go into Boot ROM mode, try to "
            "set --baud and --nmea-baud to the default baud rate of the "
            "current firmware")
    parser.add_argument('serial_port', help='path of serial port device')
    parser.add_argument('output_file', help='path to write firmware file')
    parser.add_argument('--header-only',
            dest="header_only", default=False, action="store_true",
            help='dump firmware header only, for use with mt333x_fw_file_info.py')
    parser.add_argument('--first-block-only',
            dest="first_block_only", default=False, action="store_true",
            help='dump first block of firmware flash memory only. This block can be written back to flash with mt333x_fw_update.py')
    parser.add_argument('-l', '--length', metavar='N',
            type=lambda x: int(x, 0), dest="length",
            help='Read N bytes instead of automatically trying to determine '
                 'firmware size')
    parser.add_argument('--remove-magic',
            dest="remove_magic", default=False, action="store_true",
            help='A magic value is added to the header upon programming. '
                 'Remove this value.')
    parser.add_argument('-b', '--baud',
            dest="baud", type=int, choices=(115200, 57600, 38400, 19200, 14400,
                9600, 4800), default=115200,
            help='Use given baud rate for Boot ROM communication. '
                 'Default: 115200')
    parser.add_argument('--nmea-baud',
            dest="nmea_baud", type=int, choices=(115200, 57600, 38400, 19200,
                14400, 9600, 4800),
            help='Use given baud rate for NMEA communication. '
                 'Default: auto detect')
    parser.add_argument('--dtr-reset',
            dest="dtr_reset", default=False, action="store_true",
            help='Use serial DTR signal to toggle NReset line to reset target.')
    parser.add_argument('--version',
            action='version',
            version='%(prog)s {}.{}'.format(VERSION_MAJOR, VERSION_MINOR))

    args = parser.parse_args()

    # Connect to Boot Rom
    brom = MtkGpsBRom(args.serial_port, baud=args.baud,
            nmea_baud=args.nmea_baud,
            dtr_reset=args.dtr_reset)

    brom.start()

    if args.length:
        fw_size = args.length
    elif args.first_block_only:
        # Dump 64K. This makes it easy to write back the header to the device.
        # Since the flash has 64k erase blocks and thus 64k is the minimum
        fw_size = 0x10000
    elif args.header_only:
        fw_size = 0x200
    else:
        # Try to determine fw size from header. This doesn't always work, in
        # some firmwares this field is 0. In that case the user just has to
        # guess the size.
        fw_size = brom.read32(BASE_ADDR_FIRMWARE + 0xf4, 4)
        fw_size = struct.unpack(">L", fw_size)[0]

        if fw_size == 0:
            print("Failed to automatically determine Firmware size, use '-l' option")
            exit(1)

    print("Reading firmware:")
    sys.stdout.write("  0% 0/{}\r".format(fw_size))
    sys.stdout.flush()
    with open(args.output_file, "wb") as outf:
        addr = BASE_ADDR_FIRMWARE

        bytes_left = fw_size
        while bytes_left != 0:
            read_size = min(0x100, bytes_left)

            data = brom.read(addr, read_size, byteSwap=True)

            outf.write(data)

            addr += read_size
            bytes_left -= read_size

            sys.stdout.write("{:3}% {}/{}\r".format(
                int((addr - BASE_ADDR_FIRMWARE) * 100 / fw_size),
                addr - BASE_ADDR_FIRMWARE,
                fw_size))
            sys.stdout.flush()
        print("")

        if args.remove_magic:
            if fw_size < (0x5c + 4):
                print("Warning: Unable to remove magic, Firmware to small")
            else:
                outf.seek(0x5c)
                outf.write("\xff\xff\xff\xff")

    #TODO: reset the device somehow
    print("Please reset the device manually.")

    print("Done.")


if __name__ == '__main__':
    main()
