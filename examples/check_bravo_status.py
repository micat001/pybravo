"""
API Wrapper to query Bravo Status for all modes.
"""

import sys
import time
import yaml

from bravo_status import BravoStatus
from pybravo import PacketID, DeviceID
from utils import bcolors


REALTIME_DESIRED_PACKETS = [
    PacketID.MODE,
    PacketID.VELOCITY,
    PacketID.POSITION,
    PacketID.CURRENT,
    PacketID.TEMPERATURE,
]
STARTUP_DESIRED_PACKETS = [
    PacketID.SERIAL_NUMBER,
    PacketID.MODEL_NUMBER,
    PacketID.SOFTWARE_VERSION,
    PacketID.HEARTBEAT_FREQUENCY,
    PacketID.POSITION_LIMITS,
    PacketID.VELOCITY_LIMITS,
    PacketID.CURRENT_LIMITS,
]

BRAVO_LIMITS = "/home/marcmicatka/Documents/raven_manipulation/src/raven_manip_sw/params/bravo_limits.yaml"


if __name__ == "__main__":
    status = BravoStatus(REALTIME_DESIRED_PACKETS, STARTUP_DESIRED_PACKETS)
    current_properties = status.get_startup_status()

    while not status.compare_status(current_properties, BRAVO_LIMITS):
        print("Trying to set limits properly...")
        time.sleep(1.0)
    print(
        f"\n{bcolors.OKGREEN}{bcolors.BOLD}All Properties Set! Manipulate Away! {bcolors.ENDC}"
    )
