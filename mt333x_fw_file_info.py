#!/usr/bin/env python
# mt333x_fw_file_info.py - Dump customization settings of a MT333x firmware file
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
# **WARNING**: Most of this work is based on guessing and trail-and-error. So
# there is absolutely no guarantee that the provided information is correct.
#
import struct
import argparse

VERSION_MAJOR=0
VERSION_MINOR=1

# Following defines are taken from LocusParser.cpp example
LOCUS_CONTENT_UTC   =  (1 << 0)   # 4-byte
LOCUS_CONTENT_VALID =  (1 << 1)   # 1-byte // Modified
LOCUS_CONTENT_LAT   =  (1 << 2)   # 4-byte
LOCUS_CONTENT_LON   =  (1 << 3)   # 4-byte
LOCUS_CONTENT_HGT   =  (1 << 4)   # 2-byte // Modified
LOCUS_CONTENT_SPD   =  (1 << 5)   # 2-byte // Modified
LOCUS_CONTENT_TRK   =  (1 << 6)   # 2-byte // Modified
LOCUS_CONTENT_HDOP  =  (1 << 10)  # 2-byte
LOCUS_CONTENT_NSAT  =  (1 << 12)  # 1-byte // Modified

# Locus modes as defined in 'GTop LOCUS Library User Manual-v13.pdf'
LOCUS_MODE_AL       = (1 << 0)  # AlwaysLocate(tm) mode (logging with AlwaysLocate(tm) )
LOCUS_MODE_FIX_ONLY = (1 << 1)  # Fix only mode (logging when 3D-fix only)
LOCUS_MODE_NORM     = (1 << 2)  # Normal mode (logging per positioning, ex: 1sec)
LOCUS_MODE_IVAL     = (1 << 3)  # Interval mode (logging per pre-setting interval, ex: 15sec)
LOCUS_MODE_DST      = (1 << 4)  # Distance mode (logging by distance, ex: 50 meters)
LOCUS_MODE_SPD      = (1 << 5)  # Speed mode (logging by speed, ex:10 m/s)

# TODO: higher baud(>115200) rates are guesses
STRINGS_BAUD_RATES = ('115200', '912600?', '460800?', '230400?', '57600', '38400', '19200', '14400', '9600', '4800')

LED_DUTY_CYCLE = ( "OFF", "50ms", "100ms", "200ms", "1/8", "1/2", "7/8", "ON" )

STRINGS_DATUM = (
        'WGS 84',
        'Tokyo-M',
        'Tokyo-A',
        'User Setting',
        'Adindan',
        'Adindan',
        'Adindan',
        'Adindan',
        'Adindan',
        'Adindan',
        'Adindan',
        'Afgooye',
        'Ain EI Abd 1970',
        'Ain El Abd 1970',
        'American Samoa 1962',
        'Anna 1 Astro 1965',
        'Antigua Island Astro 1943',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1950',
        'Arc1960',
        'Arc1960',
        'Arc1960',
        'Ascension Island 1958',
        'Astro Beacon E 1945',
        'Astro Dos 71/4',
        'Astro Tern Island (FRIG) 1961',
        'Astronomical Station 1952',
        'Australian Geodetic 1966',
        'Australian Geodetic 1984',
        'Ayabelle Lighthouse',
        'Bellevue (IGN)',
        'Bermuda 1957',
        'Bissau',
        'Bogota Observatory',
        'Bukit Rimpah',
        'Camp Area Astro',
        'Campo Inchauspe',
        'Canton Astro 1966',
        'Cape',
        'Cape Canaveral',
        'Carthage',
        'Chatham Island Astro 1971',
        'Chua Astro',
        'Corrego Alegre',
        'Dabola',
        'Deception Island',
        'Djakarta',
        'Dos 1968',
        'Easter Island 1967 Easter Island',
        'Estonia Coordinate System 1937 Estonia',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1950',
        'European 1979',
        'Fort Thomas 1955',
        'Gan 1970',
        'Geodetic Datum 1970',
        'Graciosa Base SW1948',
        'Guam 1963',
        'Gunung Segara',
        'Gux I Astro',
        'Heart North',
        'Hermannskogel Datum',
        'Hjorsey 1955',
        'Hongkong 1963',
        'Hu Tzu Shan',
        'Indian',
        'Indian',
        'Indian',
        'Indian 1954',
        'Indian 1960',
        'Indian 1960',
        'Indian 1975',
        'Indonesian 1974',
        'Ireland 1965',
        'ISTS 061 Astro 1968',
        'ISTS 073 Astro 1969',
        'Johnston Island 1961',
        'Kandawala',
        'Kerguelen Island 1949',
        'Kertau 1948',
        'Kusaie Astro 1951',
        'Korean Geodetic System',
        'LC5 Astro 1961',
        'Leigon',
        'Liberia 1964',
        'Luzon',
        'Luzon',
        "M'Poraloko",
        'Mahe 1971',
        'Massawa',
        'Merchich',
        'Midway Astro 1961',
        'Minna',
        'Minna',
        'Montserrat Island Astro 1958',
        'Nahrwan',
        'Nahrwan',
        'Nahrwan',
        'Naparima BWI',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1927',
        'North American 1983',
        'North American 1983',
        'North American 1983',
        'North American 1983',
        'North American 1983',
        'North American 1983',
        'North Sahara 1959',
        'Observatorio Meteorologico 1939',
        'Old Egyptian 1907',
        'Old Hawaiian',
        'Old Hawaiian',
        'Old Hawaiian',
        'Old Hawaiian',
        'Old Hawaiian',
        'Oman',
        'Ordnance Survey Great Britain 1936',
        'Ordnance Survey Great Britain 1936',
        'Ordnance Survey Great Britain 1936',
        'Ordnance Survey Great Britain 1936',
        'Ordnance Survey Great Britain 1936',
        'Pico de las Nieves',
        'Pitcairn Astro 1967',
        'Point 58',
        'Pointe Noire 1948',
        'Porto Santo 1936',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South American 1956',
        'Provisional South Chilean 1963',
        'Puerto Rico',
        'Pulkovo 1942',
        'Qatar National',
        'Qornoq',
        'Reunion',
        'Rome 1940',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-42 (Pulkovo 1942)',
        'S-JTSK',
        'Santo (Dos) 1965',
        'Sao Braz',
        'Sapper Hill 1943',
        'Schwarzeck',
        'Selvagem Grande 1938',
        'Sierra Leone 1960',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South American 1969',
        'South Asia',
        'Tananarive Observatory 1925',
        'Timbalai 1948',
        'Tokyo',
        'Tokyo',
        'Tokyo',
        'Tokyo',
        'Tristan Astro 1968',
        'Viti Levu 1916',
        'Voirol 1960',
        'Wake Island Astro 1952',
        'Wake-Eniwetok 1960',
        'WGS 1972',
        'WGS 1984',
        'Yacare',
        'Zanderij'
    )

def enum_to_str(names, idx, default="Out-of-range"):
    if idx >= len(names):
        return default

    return names[idx]


# Parse command line argument
parser = argparse.ArgumentParser(description='Dump information about firmware file for GTop MT33xx based GPS modules.')
parser.add_argument('file', type=argparse.FileType('rb'), help='Path to firmware file to analyze')
parser.add_argument('--version', action='version', version='%(prog)s {}.{}'.format(VERSION_MAJOR, VERSION_MINOR))

args = parser.parse_args()

# Read header
header = args.file.read(0xa00)

# Dump header
print("(?) Firmware family: " + header[0x90:0xb0].strip('\x00'))
print("Device Type: " + header[0x1b0:0x1c0].strip('\x00'))

print("Release Name: {}".format(header[0x148:0x150].strip('\x00')))
(release_major, release_minor) = struct.unpack("BB", header[0x15A:0x15C])
print("Release Version: {}.{}".format(release_major, release_minor))
print("build number: {:x}".format(struct.unpack("<H", header[0x108:0x10a])[0]))
print("")
fw_size = struct.unpack("<L", header[0xf4:0xf8])[0]
print("(?)Firmware size: {}{}".format(fw_size, " (Unknown)" if fw_size == 0 else ""))
print("Serial port string: " + header[0x190:0x1a0].strip('\x00'))

# Generic config stuff
print("")

print("Baud Rate: " + enum_to_str(STRINGS_BAUD_RATES, ord(header[0x120])))
    
print("NMEA Coordinate Precision: {} digits".format(6 if (ord(header[0x162]) & 0x4 != 0) else 4))
print("Update Rate: {}".format(ord(header[0x11c])))
print("Sentence rates:")
print(" - GGA: {}".format(ord(header[0x128])))
print(" - GLL: {}".format(ord(header[0x129])))
print(" - ???: {}".format(ord(header[0x12a])))
print(" - GSV: {}".format(ord(header[0x12b])))
print(" - GSA: {}".format(ord(header[0x12c])))
print(" - VTG: {}".format(ord(header[0x12d])))
print(" - RMC: {}".format(ord(header[0x12e])))
print(" - GLL(2): {}".format(ord(header[0x12f])))
print(" - ZDA: {}".format(ord(header[0x138])))

print("")
print("GPS Datum: {}".format(enum_to_str(STRINGS_DATUM, ord(header[0x11b]))))
nav_threshold = ord(header[0x136])
if nav_threshold > 0xa:
    print("WARNING: Nav. Threshold > 0xa; unexpected")
print("Nav. Threshold: {:.2f}".format(0.2 * nav_threshold))

print("")
print("3d-fix LED:")
print(" - no fix: {}, {}".format(0.5 * ((ord(header[0x121]) & 0x1F) + 1),
         enum_to_str(LED_DUTY_CYCLE, ord(header[0x121]) >> 5)))
print(" - fix: {}, {}".format(0.5 * ((ord(header[0x122]) & 0x1F) + 1),
         enum_to_str(LED_DUTY_CYCLE, ord(header[0x122]) >> 5)))

# LOCUS stuff
if release_major > 1 or (release_major == 1 and release_minor > 51):
    print("")
    print("LOCUS settings:")

    locus_types = ( "Overlap", "Full-Stop", "unknown")
    print(" -  type: " + enum_to_str(locus_types, ord(header[0x182])))

    locus_mode = ord(header[0x183])
    modes = [] 
    if locus_mode & LOCUS_MODE_AL:
        modes.append("AlwaysLocate(TM)")
    if locus_mode & LOCUS_MODE_FIX_ONLY:
        modes.append("Fix Only")
    if locus_mode & LOCUS_MODE_NORM:
        modes.append("Normal")
    if locus_mode & LOCUS_MODE_IVAL:
        modes.append("Interval")
    if locus_mode & LOCUS_MODE_DST:
        modes.append("Distance")
    if locus_mode & LOCUS_MODE_SPD:
        modes.append("Speed")
    print(" -  mode: " + ", ".join(modes))

    record_content = struct.unpack_from("<L", header, 0x184)[0]
    record_fields = ""
    if record_content & LOCUS_CONTENT_UTC:
        record_fields += "Timestamp, "
    if record_content & LOCUS_CONTENT_VALID:
        record_fields += "Validity, "
    if record_content & LOCUS_CONTENT_LAT:
        record_fields += "Latitude, "
    if record_content & LOCUS_CONTENT_LON:
        record_fields += "Longitude, "
    if record_content & LOCUS_CONTENT_HGT:
        record_fields += "Height, "
    if record_content & LOCUS_CONTENT_SPD:
        record_fields += "Speed, "
    if record_content & LOCUS_CONTENT_TRK:
        record_fields += "Track, "
    if record_content & LOCUS_CONTENT_HDOP:
        record_fields += "HDOP, "
    if record_content & LOCUS_CONTENT_NSAT:
        record_fields += "# Satellites, "
    if len(record_fields) != 0:
        record_fields += "Checksum"
    print(" -  record content: " + record_fields)

    print(" -  interval: {}".format(struct.unpack_from("<H", header, 0x188)[0]))
    print(" -  distance: {}".format(struct.unpack_from("<H", header, 0x18a)[0]))
    print(" -  speed: {}".format(struct.unpack_from("<H", header, 0x18c)[0]))
