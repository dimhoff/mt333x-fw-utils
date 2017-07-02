# mt333x_helpers.py - Helper classes for MT333x GPS BRom and DA
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
import serial
import struct
import time

# 0x00000c00 scratchpad/RAM???
# 0x20000000 Firmware(/spi flash)
# 0x80000000 Regs
# 0xA0000000 ROM
BASE_ADDR_FIRMWARE = 0x20000000
BASE_ADDR_DA = 0xc00

def checksum_xor16(data):
    """ Calculate 16-bit XOR checksum over 'data' """
    cksum = 0
    for i in xrange(0, len(data), 2):
        cksum = cksum ^ struct.unpack_from(">H", data, i)[0]

    if len(data) % 2 != 0:
        cksum = cksum ^ (ord(data[-1]) << 8)

    return cksum


class MtkGpsBRom:
    """ MTK Boot ROM interface class """

    def __init__(self, serial_port, baud=115200, nmea_baud=None, dtr_reset=False):
        """ Initialize class and open serial port 'serial_port' """
        self._ser = serial.Serial(serial_port, baud, timeout=1,
                                 xonxoff=False, rtscts=False, dsrdtr=False)
        if baud > 115200:
            # Boot Rom doesn't seem to support baud rates above 115200, only DA does
            self._baud = 115200
        else:
            self._baud = baud
        self._nmea_baud = nmea_baud
        self._dtr_reset = dtr_reset

    def start(self):
        """ Restart module into boot rom mode """
        # Restart into Boot Rom mode
        if self._dtr_reset:
            self._ser.setDTR(1)
            self._ser.setDTR(0)
        else:
            if self._nmea_baud:
                self._ser.apply_settings({ 'baudrate': self._nmea_baud })
                self._ser.write("$PMTK180*3B\r\n")
                self._ser.flush()
                time.sleep(0.1)
            else:
                for baudrate in (115200, 57600, 38400, 19200, 14400, 9600, 4800):
                    try:
                        self._ser.apply_settings({ 'baudrate': baudrate })
                        self._ser.write("$PMTK180*3B\r\n")
                        self._ser.flush()
                        time.sleep(0.1)
                    except:
                        pass

        self._ser.apply_settings({
            'baudrate': self._baud,
            'timeout': 0.005
        })

        # BOOT_ROM_START_CMD1
        c = ''
        start_time = time.time()
        timeout = False
        while (len(c) == 0 or ord(c) != 0x5F) and not timeout:
            self._ser.write("\xa0")
            self._ser.flush()
            c = self._ser.read()

            if time.time() >= start_time + 10:
                timeout = True

        if timeout:
            raise RuntimeError("Timeout @ BOOT_ROM_START_CMD1")

        self._ser.apply_settings({ 'timeout': 1 })

        # BOOT_ROM_START_CMD2
        self._ser.write("\x0a")
        c = self._ser.read()
        if len(c) == 0:
            raise RuntimeError("TIMEOUT @ BOOT_ROM_START_CMD2")

        if ord(c) != 0xF5:
            raise RuntimeError("incorrect response at BOOT_ROM_START_CMD2: "
                                "0x{:02x}".format(ord(c)))

        # BOOT_ROM_START_CMD3
        self._ser.write("\x50")
        c = self._ser.read()
        if len(c) == 0:
            raise RuntimeError("TIMEOUT @ BOOT_ROM_START_CMD3")

        if ord(c) != 0xAF:
            raise RuntimeError("incorrect response at BOOT_ROM_START_CMD3: "
                                "0x{:02x}".format(ord(c)))

        # BOOT_ROM_START_CMD4
        self._ser.write("\x05")
        c = self._ser.read()
        if len(c) == 0:
            raise RuntimeError("TIMEOUT @ BOOT_ROM_START_CMD4")

        if ord(c) != 0xFA:
            raise RuntimeError("incorrect response at BOOT_ROM_START_CMD4: "
                                "0x{:02x}".format(ord(c)))

    def read(self, address, length, byteSwap=False):
        """ Read data from device memory starting at 'address', reading
        'length' amount of bytes"""
        data = ""

        # Align start address
        if address % 4 != 0:
            buf = self.read32(address & ~0x3, 4, byteSwap)

            data = buf[(address % 4) - 4 :]
            if len(data) > length:
                data = buf[:length]

            address += len(data)
            length -= len(data)

        # Read in multiples of 32-bit, aligned
        while length > 4:
            blen = min(length & ~0x3, 0x100)

            buf = self.read32(address, blen, byteSwap)

            data += buf
            address += blen
            length -= blen

        # Read remaining bytes
        if length != 0:
            buf = self.read32(address, 4, byteSwap)
            data += buf[:length]

        return data

    def read16(self, address, length, byteSwap=False):
        """ Read data in 16-bit chunks starting at 'address', reading
        'length' amount of bytes. If 'byteSwap' is True a byte swapped read
        is used """
        if address % 2 != 0:
            raise RuntimeError("Misaligned reads not supported")

        if length % 2 != 0:
            raise RuntimeError("length should be a multiple of 2")

        self._checked_write("\xa2")
        self._checked_write(struct.pack(">L", address))
        self._checked_write(struct.pack(">L", int(length/2)))
        resp = ""
        while len(resp) < length:
            c = self._ser.read()
            if len(c) == 0:
                raise RuntimeError("Timeout during boot rom READ command")
            resp += c

        cksum = self.checksum(address, length)
        if cksum != checksum_xor16(resp):
            # TODO: retry and bail after multiple failures
            print("checksum error: {:04x} != {:04x}".format(cksum, checksum_xor16(resp)))

        # Fix byte order
        if byteSwap:
            resp_bs = ''
            for i in xrange(0, len(resp), 2):
                resp_bs += resp[i+1] + resp[i]
            resp = resp_bs

        return resp

    def read32(self, address, length, byteSwap=False):
        """ Read data in 32-bit chunks starting at 'address', reading
        'length' amount of bytes. If 'byteSwap' is True a byte swapped read
        is used """
        if address % 4 != 0:
            raise RuntimeError("Misaligned reads not supported")

        if length % 4 != 0:
            raise RuntimeError("length should be a multiple of 4")

        self._checked_write("\xaf")
        self._checked_write(struct.pack(">L", address))
        self._checked_write(struct.pack(">L", int(length/4)))
        resp = ""
        while len(resp) < length:
            c = self._ser.read()
            if len(c) == 0:
                raise RuntimeError("Timeout during boot rom READ command")
            resp += c

        cksum = self.checksum(address, length)
        if cksum != checksum_xor16(resp):
            # TODO: retry and bail after multiple failures
            print("checksum error: {:04x} != {:04x}".format(cksum, checksum_xor16(resp)))

        # Fix byte order
        if byteSwap:
            resp_bs = ''
            for i in xrange(0, len(resp), 4):
                resp_bs += resp[i+3] + resp[i+2] + resp[i+1] + resp[i]
            resp = resp_bs

        return resp

    def write(self, address, data, byteSwap=False):
        """ Read data from device memory starting at 'address', reading
        'length' amount of bytes"""

        # Align start address
        if address % 2 != 0:
            address -= 1;
            data = "\x00" + data

        if len(data) % 2 != 0:
            data = data + "\x00"

        # Write data
        # Note: Don't split in small chunks. This does mean the checksum is
        # worthless for big data blocks. But all written data is echoed back
        # anyway...
        buf = self.write16(address, data, byteSwap)

        return data

    def write16(self, address, data, byteSwap=False):
        """ Write 'data' in 16-bit chunks starting at 'address'. If 'byteSwap'
        is True a byte swapped write is used """
        if address % 2 != 0:
            raise RuntimeError("Misaligned reads not supported")

        if len(data) % 2 != 0:
            raise RuntimeError("Data length should be a multiple of 2")

        # Fix byte order
        if byteSwap:
            data_bs = ''
            for i in xrange(0, len(data), 2):
                data_bs += data[i+1] + data[i]
            data = data_bs

        self._checked_write("\xa1")
        self._checked_write(struct.pack(">L", address))
        self._checked_write(struct.pack(">L", len(data)/2))

        bytes_send = 0
        while bytes_send < len(data):
            data_to_send = data[bytes_send:bytes_send + 10]
            self._ser.write(data_to_send)
            resp = self._ser.read(len(data_to_send))
            if resp != data_to_send:
                raise RuntimeError("Response doesn't match send data")
            bytes_send += len(data_to_send)

        cksum = self.checksum(address, len(data))
        if cksum != checksum_xor16(data):
            # TODO: retry and bail after multiple failures
            print("checksum error: {:04x} != {:04x}".format(cksum, checksum_xor16(data)))

    def jump(self, address):
        """ Cause the boot ROM to start executing code at address """
        if address % 4 != 0:
            raise RuntimeError("Code must be 32-bit aligned")

        self._checked_write("\xa8")
        self._checked_write(struct.pack(">L", address))

    def checksum(self, address, length, byteSwap=False):
        """ Get 16-bit XOR checksum of memory region starting at 'address' with
        'length' bytes. 'address' must be 16-bit aligned and 'length' must be a
        multiple of 2. """
        if address % 2 != 0:
            raise RuntimeError("Misaligned reads not supported")

        if length % 2 != 0:
            raise RuntimeError("length should be a multiple of 2")

        self._checked_write("\xa4")
        self._checked_write(struct.pack(">L", address))
        self._checked_write(struct.pack(">L", int(length/2)))
        resp = ""
        while len(resp) < 2:
            c = self._ser.read()
            if len(c) == 0:
                raise RuntimeError("Timeout during boot rom READ command")
            resp += c

        if byteSwap:
            return struct.unpack("<H", resp)[0]
        else:
            return struct.unpack(">H", resp)[0]

    def _checked_write(self, data):
        """ Write 'data' to device and verify that it is echoed back """
        for b in data:
            self._ser.write(b)

        for b in data:
            c = self._ser.read()
            if len(c) == 0:
                raise RuntimeError("Timeout in checked_write")

            if c != b:
                raise RuntimeError("checked_write: incorrect response: "  
                        "0x{:02x} != 0x{:02x}".format(ord(b), ord(c)))

class DownloadAgent():
    """MTK DownloadAgent interface class"""

    OPCODE_DA_SET_BAUD = 0xd2
    OPCODE_DA_MEM_CMD = 0xd3
    OPCODE_DA_WRITE_CMD = 0xd5

    DA_WRITE_PACKET_LEN = 0x100

    DA_ACK = '\x5a'
    DA_NAK = '\xa5'
    DA_CONT_CHAR = '\x69'
    DA_SYNC_CHAR = '\xc0'

    DA_INFO_REPORT_LEN = 20

    def __init__(self, brom):
        self._brom = brom
        # FIXME: fix how serial device is passed
        self._ser = brom._ser
        self._progress_cb = lambda cnt, total: None

    def set_progress_callback(self, cb):
        """ Set a function to be called for progress reports when flashing
        firmware or loading the DA. 'cb' must be a function with the following
        definition 'callback(cnt, total)' """
        if cb is None:
            self._progress_cb = lambda cnt, total: None
        else:
            self._progress_cb = cb

    def start(self, da_path):
        """ Upload DA availiable at 'da_path' to the device and run it. The
        progress callback is called while uploading the DA to the target. """
        with open(da_path, "rb") as infile:
            da_code = infile.read()

        # Uploading DA
        for offset in xrange(0, len(da_code), self.DA_WRITE_PACKET_LEN):
            self._progress_cb(offset, len(da_code))

            end = offset + self.DA_WRITE_PACKET_LEN
            if end > len(da_code):
                end = len(da_code)

            self._brom.write(BASE_ADDR_DA + offset, da_code[offset:end], byteSwap=True)

        self._progress_cb(len(da_code), len(da_code))

        self._brom.jump(BASE_ADDR_DA)
        da_info_resp = self._ser.read(self.DA_INFO_REPORT_LEN)
        if len(da_info_resp) != self.DA_INFO_REPORT_LEN:
            raise RuntimeError("Could not read full DA info report")

        da_info_fields = (
                'sync_char',
                'da_version',
                'flash_device_id',
                'flash_size',
                'flash_manufacturer_code',
                'flash_device_code',
                'flash_ext_device_code1',
                'flash_ext_device_code2',
                'ext_sram_size'
            )
        self._da_info = dict(zip(da_info_fields, struct.unpack(">BHBLHHHHL", da_info_resp)))

        if self._da_info['sync_char'] != ord(self.DA_SYNC_CHAR):
            raise RuntimeError("DA info SYNC_CHAR incorrect(0x{:x})".format(self._da_info['sync_char']))

        if self._da_info['da_version'] != 0x0400:
            raise RuntimeError("Unsupported DA version: 0x{:x}".format(self._da_info['da_version']))

        if self._da_info['flash_device_id'] == 0xff:
            raise RuntimeError("Unsupported flash type")

    def set_baud_rate(self, baudrate):
        """ Switch to a baud rate > 115200 """
        RATE_TO_NUMBER = {
                912600: 1,
                460800: 2,
                230400: 3,
                }

        if baudrate not in RATE_TO_NUMBER:
            raise RuntimeError("Invalid baud rate")

        check_cnt = 0

        self._ser.write(struct.pack(">BBB",
                                    self.OPCODE_DA_SET_BAUD,
                                    RATE_TO_NUMBER[baudrate],
                                    check_cnt))

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge command")

        resp = self._ser.read(1)
        if resp != '\xcc':
            raise RuntimeError("Baud rate change start not received")

        self._ser.apply_settings({ 'baudrate': baudrate })

        resp = self._ser.read(1)
        if resp != "\xaa":
            raise RuntimeError("Baud rate change done not received")

        self._ser.write(self.DA_SYNC_CHAR)
        resp = self._ser.read(1)
        if resp != self.DA_SYNC_CHAR:
            raise RuntimeError("Unexpected response")

        self._ser.write(self.DA_ACK)
        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge command")

        # TODO: implement comm. check and enable
        #for i in xrange(0, 0xff):
        #    self._ser.write(chr(i))
        #    resp = self._ser.read(1)

    def _set_mem_block(self, start, length):
        """ Run the CmdSetMemBlock command to prepare a write. NOTE: the second
        argument to this function is the length instead of the end address."""

        if length % 2 != 0:
            raise RuntimeError("data length must be a multiple of two")

        end = start + length - 1 # end is the index of the last byte, therefor substract 1

        mem_block_count = 1

        self._ser.write(struct.pack(">BBLL", self.OPCODE_DA_MEM_CMD, mem_block_count, start, end))

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge command")

        resp = self._ser.read(1)
        #TODO: how to interpret this?

    def _write_data(self, data):
        #if len(data) % self.DA_WRITE_PACKET_LEN != 0:
        #    raise RuntimeError("data length must be a multiple of packet size(=256)")

        self._ser.write(struct.pack(">BL", self.OPCODE_DA_WRITE_CMD, self.DA_WRITE_PACKET_LEN))

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge command")

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge erase")

        for block_idx in xrange(0, len(data), self.DA_WRITE_PACKET_LEN):
            self._progress_cb(block_idx, len(data))

            end = block_idx + self.DA_WRITE_PACKET_LEN
            if end > len(data):
                end = len(data)

            chksum = 0
            for byte_idx in xrange(block_idx, end):
                self._ser.write(data[byte_idx])
                chksum += ord(data[byte_idx])

            self._ser.write(struct.pack(">H", chksum & 0xffff))

            resp = self._ser.read(1)
            if resp != self.DA_CONT_CHAR:
                raise RuntimeError("Did not receive a continue character from DA(0x{:x})".format(ord(resp)))

        self._progress_cb(len(data), len(data))

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge")

        resp = self._ser.read(1)
        if resp != self.DA_ACK:
            raise RuntimeError("DA did not acknowledge")

    def restart(self):
        self._ser.write('\xd9')

    def print_info(self):
        """ Print to stdout the information reported by the DA at start """
        print("DA version: 0x{:04x}".format(self._da_info['da_version']))
        print("Ext. SRAM size: {}".format(self._da_info['ext_sram_size']))
        print("Flash:")
        print(" - Device ID: 0x{:02x}".format(self._da_info['flash_device_id']))
        print(" - Size: {}".format(self._da_info['flash_size']))
        print(" - HW ID: 0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x}".format(
                self._da_info['flash_manufacturer_code'],
                self._da_info['flash_device_code'],
                self._da_info['flash_ext_device_code1'],
                self._da_info['flash_ext_device_code2']
            ))


