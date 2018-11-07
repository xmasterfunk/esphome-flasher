import re

__version__ = "1.0.0"

ESP32_DEFAULT_OTA_DATA = 'https://github.com/espressif/arduino-esp32/blob/1.0.0/tools/partitions/boot_app0.bin'
# The latest bootloader image seems to work with older firmwares, but the "stable" bootloader
# doesn't work with firmwares generated with the latest esp-idf
ESP32_DEFAULT_BOOTLOADER_FORMAT = 'https://github.com/espressif/arduino-esp32/raw/' \
                                  '96822d783f3ab6a56a69b227ba4d1a1a36c66268/tools/sdk/' \
                                  'bin/bootloader_$FLASH_MODE$_$FLASH_FREQ$.bin'
ESP32_DEFAULT_PARTITIONS = 'https://github.com/OttoWinter/esphomeflasher/blob/master/partitions.bin'

# https://stackoverflow.com/a/3809435/8924614
HTTP_REGEX = re.compile(r'https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)')
