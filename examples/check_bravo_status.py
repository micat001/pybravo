"""
API Wrapper to query Bravo Status for all modes.
"""

import sys
import time
import yaml

from utils import compare_status
from bravo_status import BravoStatus
from pybravo import PacketID, DeviceID


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


BRAVO_XACRO = "/home/marcmicatka/Documents/raven_manipulation/src/bravo_ros/bravo_description/urdf/bravo/bravo_7_arm_only.xacro"
BRAVO_LIMITS = "/home/marcmicatka/Documents/raven_manipulation/src/raven_manip_sw/params/bravo_limits.yaml"


if __name__ == "__main__":
    status = BravoStatus(REALTIME_DESIRED_PACKETS, STARTUP_DESIRED_PACKETS)
    current_properties = status.get_startup_status()
    # status.print_startup_status()
    compare_status(current_properties, BRAVO_LIMITS)

    # while True:
    #     try:
    #         status.print_rt_status()
    #         time.sleep(0.1)
    #     except KeyboardInterrupt:
    #         # status.stop()
    #         sys.exit()
