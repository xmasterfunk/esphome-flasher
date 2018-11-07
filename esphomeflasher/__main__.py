from __future__ import print_function

import argparse
from datetime import datetime
import re
import sys

import esptool
import serial

from esphomeflasher import const
from esphomeflasher.common import ESP32ChipInfo, EsphomeflasherError, chip_run_stub, \
    configure_write_flash_args, detect_chip, detect_flash_size, read_chip_info
from esphomeflasher.const import ESP32_DEFAULT_BOOTLOADER_FORMAT, ESP32_DEFAULT_OTA_DATA, \
    ESP32_DEFAULT_PARTITIONS
from esphomeflasher.helpers import list_serial_ports


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='esphomeflasher {}'.format(const.__version__))
    parser.add_argument('-p', '--port',
                        help="Select the USB/COM port for uploading.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--esp8266', action='store_true')
    group.add_argument('--esp32', action='store_true')
    parser.add_argument('--bootloader',
                        help="(ESP32-only) The bootloader to flash.",
                        default=ESP32_DEFAULT_BOOTLOADER_FORMAT)
    parser.add_argument('--partitions',
                        help="(ESP32-only) The partitions to flash.",
                        default=ESP32_DEFAULT_PARTITIONS)
    parser.add_argument('--otadata',
                        help="(ESP32-only) The otadata file to flash.",
                        default=ESP32_DEFAULT_OTA_DATA)
    parser.add_argument('--no-erase',
                        help="Do not erase flash before flashing",
                        action='store_true')
    parser.add_argument('binary', help="The binary image to flash.")

    return parser.parse_args(argv[1:])


def select_port(args):
    if args.port is not None:
        print(u"Using '{}' as serial port.".format(args.port))
        return args.port
    ports = list_serial_ports()
    if not ports:
        raise EsphomeflasherError("No serial port found!")
    if len(ports) != 1:
        print("Found more than one serial port:")
        for port, desc in ports:
            print(u" * {} ({})".format(port, desc))
        print("Please choose one with the --port argument.")
        raise EsphomeflasherError
    print(u"Auto-detected serial port: {}".format(ports[0][0]))
    return ports[0][0]


ANSI_REGEX = re.compile(r"\033\[[0-9;]*m")


def run_esphomeflasher(argv):
    args = parse_args(argv)
    try:
        firmware = open(args.binary, 'rb')
    except IOError as err:
        raise EsphomeflasherError("Error opening binary: {}".format(err))
    port = select_port(args)
    chip = detect_chip(port, args.esp8266, args.esp32)
    info = read_chip_info(chip)

    print()
    print("Chip Info:")
    print(" - Chip Family: {}".format(info.family))
    print(" - Chip Model: {}".format(info.model))
    if isinstance(info, ESP32ChipInfo):
        print(" - Number of Cores: {}".format(info.num_cores))
        print(" - Max CPU Frequency: {}".format(info.cpu_frequency))
        print(" - Has Bluetooth: {}".format('YES' if info.has_bluetooth else 'NO'))
        print(" - Has Embedded Flash: {}".format('YES' if info.has_embedded_flash else 'NO'))
        print(" - Has Factory-Calibrated ADC: {}".format(
            'YES' if info.has_factory_calibrated_adc else 'NO'))
    else:
        print(" - Chip ID: {:08X}".format(info.chip_id))

    print(" - MAC Address: {}".format(info.mac))

    stub_chip = chip_run_stub(chip)

    flash_size = detect_flash_size(stub_chip)
    print(" - Flash Size: {}".format(flash_size))

    try:
        stub_chip.flash_set_parameters(esptool.flash_size_bytes(flash_size))
    except esptool.FatalError as err:
        raise EsphomeflasherError("Error setting flash parameters: {}".format(err))

    mock_args = configure_write_flash_args(info, firmware, flash_size,
                                           args.bootloader, args.partitions,
                                           args.otadata)

    if not args.no_erase:
        try:
            esptool.erase_flash(stub_chip, mock_args)
        except esptool.FatalError as err:
            raise EsphomeflasherError("Error while erasing flash: {}".format(err))

    try:
        esptool.write_flash(stub_chip, mock_args)
    except esptool.FatalError as err:
        raise EsphomeflasherError("Error while writing flash: {}".format(err))

    print("Hard Resetting...")
    stub_chip.hard_reset()

    print("Done! Flashing is complete!")
    print()

    print("Showing logs:")
    with stub_chip._port as ser:
        while True:
            try:
                raw = ser.readline()
            except serial.SerialException:
                print("Serial port closed!")
                return
            text = raw.decode(errors='ignore')
            ANSI_REGEX.sub('', text)
            line = text.replace('\r', '').replace('\n', '')
            time = datetime.now().time().strftime('[%H:%M:%S]')
            message = time + line
            try:
                print(message)
            except UnicodeEncodeError:
                print(message.encode('ascii', 'backslashreplace'))


def main():
    try:
        if len(sys.argv) <= 1:
            from esphomeflasher import gui

            return gui.main() or 0
        return run_esphomeflasher(sys.argv) or 0
    except EsphomeflasherError as err:
        msg = str(err)
        if msg:
            print(msg)
        return 1
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())
