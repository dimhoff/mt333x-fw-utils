# MT333x GPS receiver firmware tools
These tools can be used for updating and dumping firmware to/from GPS receivers
utilizing the MT3333 or MT3339 chipset.

 - mt333x_fw_dump.py: Dump the current firmware from a GPS device to file
 - mt333x_fw_update.py: Load a new firmware into a GPS device
 - mt333x_fw_file_info.py: Dispays the customization settings of a MT333x
   firmware file

The tools currently only work with Python 2.x.

**Note**: Most of the tools are written based on observing and trial-and-error.
Especially for mt333x_fw_file_info.py there is no guarantee that the
information is correct.

**Note2**: These tools aren't production ready code. They are more ment as
example code for people who want to build upon it.

## Firmware updates + MTK download agent
To be able to update the firmware you need a MTK download agent. These are part
of the 'GlobalTop FlashTool'. Make sure you use the correct download agent for
your device.

Example filenames of download agents:

- MTK_AllInOne_DA_MT3318_v4.01.bin (md5: 7e6bd13492293cf1efb4e8b25caa8c80)
- MTK_AllInOne_DA_MT3329_v4.02.bin (md5: 52724a12c7186bdede40ce65e0d81c5e)
- MTK_AllInOne_DA_MT3333_MP.BIN (md5: 028a2c42d1e39623c8aa148d8a0e6709)
- MTK_AllInOne_DA_MT3339_E3.bin (md5: 973d91e32b1cc37a332bfc9e235bc372)

## Firmware file names
The firmware files from GlobalTop follow a strict nameing scheme. For example:

AXN3.20_8033_3333_96.1151100.1.bin
- AXN: Fixed Prefix
- 3.20: Firmware Version
- 8033: Build number
- 3333: Target chipset, in this case MTK3333
- 96: Baud rate / 100, in this case 9600 Baud
- 1151100: NMEA sentence rate: { GGA, GSA, GSV, RMC, VTG, ?GLL?, ?ZDA? }
- 1: Update rate, ie. 1 Hz

Note: NMEA sentence rate can be 10. This gives a rather hard to decode filename
like: AXN2.31_5657_3339_1152.101010101000.10.bin
