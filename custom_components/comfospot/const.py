"""Constants for the ComfoSpot integration."""
from __future__ import annotations

DOMAIN = "comfospot"

# Network
DISCOVERY_PORT = 9987
CONTROL_PORT = 9986
DEFAULT_PORT = CONTROL_PORT

# Continuous fan speed range; 0.0 is reserved for off.
MIN_STAGE = 0.5
MAX_STAGE = 4.0
DEFAULT_STAGE = 2.0

# Timed manufacturer modes use an absolute UNIX timestamp (type 10).  The
# captured vendor app starts both modes with a default duration of 60 minutes.
CONF_NIGHT_DURATION = "night_duration"
CONF_BOOST_DURATION = "boost_duration"
DEFAULT_NIGHT_DURATION = 60
DEFAULT_BOOST_DURATION = 60
MIN_PRESET_DURATION = 5
MAX_PRESET_DURATION = 1440

# Zone property IDs (FlakeVentilationZone, abbc9241-...-776d)
PID_SPEED = 0x2011        # float, fan speed 0.5..4.0; 0.0 means off
PID_MODE = 0x2020         # uint8: operating preset (high), direction (low)
PID_MODE_UNTIL = 0x2021   # uint32 UNIX timestamp for night/boost mode expiry
PID_TARGET_TEMP = 0x2030  # float, target temperature
PID_NAME = 0x2004         # string, user-given zone name (e.g. "Zone 1")
PID_HUMIDITY = 0x1040     # float, indoor relative humidity (%)
PID_TEMPERATURE = 0x1042  # float, indoor temperature (degC)

# Object framework property IDs
PID_OBJ_UUID = 0x1001     # query key (uuid)
PID_OBJ_ADDR = 0x1002     # assigned object/client address

# System object property IDs (FlakeVentilationSystem, abbc9241-...-776c)
PID_SYS_RUN_HOURS = 0x1005  # uint32, system operating hours
PID_SYS_FIRMWARE = 0x2101   # string, firmware version

# The 0x1040-0x1044 block mirrors the app domain properties 8256-8260
# (0x2040-0x2044): a BME680-style environmental sensor running Bosch BSEC.
PID_SYS_PRESSURE = 0x1041      # float, barometric pressure (hPa)
PID_SYS_AIR_QUALITY = 0x1043   # float, BSEC IAQ index (0-500, lower = better)
PID_SYS_IAQ_ACCURACY = 0x1044  # uint8, BSEC calibration state, see below

# BSEC IAQ accuracy levels (AirQualityAccuracy enum in the vendor app)
IAQ_ACCURACY_STATES: dict[int, str] = {
    0: "run_in",
    1: "calibration_required",
    2: "calibrating",
    3: "calibrated",
}

# PID_MODE stores the manufacturer preset in the high nibble and the current
# ventilation direction in the low nibble. The hub may update the low nibble
# automatically; e.g. automatic alternating ventilation is reported as 0x32.
MODE_PRESET_MASK = 0xF0
MODE_DIRECTION_MASK = 0x0F

PRESET_NORMAL = "normal"
PRESET_NIGHT = "night"
PRESET_BOOST = "boost"
PRESET_AUTOMATIC = "automatic"

PRESET_MODES: dict[str, int] = {
    PRESET_NORMAL: 0x00,
    PRESET_NIGHT: 0x10,
    PRESET_BOOST: 0x20,
    PRESET_AUTOMATIC: 0x30,
}
PRESET_MODES_INV: dict[int, str] = {
    value: key for key, value in PRESET_MODES.items()
}

# Ventilation direction values for the low nibble of PID_MODE.
# 0x00 = Abluft  – both fans extract  (2 arrows left)
# 0x01 = Zuluft  – both fans supply   (2 arrows right)
# 0x02 = Wechsel – alternating supply/exhaust (crossing arrows)
MODES: dict[str, int] = {
    "exhaust":     0x00,
    "supply":      0x01,
    "alternating": 0x02,
}
MODES_INV: dict[int, str] = {v: k for k, v in MODES.items()}

# Zone FlakeObject UUID base (last byte varies per zone/system object)
ZONE_UUID_BASE = bytes.fromhex("abbc92414886407f8e36e26d0b6477")  # 15 bytes
ZONE_UUID_LAST_RANGE = range(0x6C, 0x74)
