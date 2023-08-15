"""
API Wrapper to query Bravo Status for all modes.
"""

import atexit
import struct
import sys
import threading
import time

from bravo_status import BravoRequests, BravoStatus

from pybravo import PacketID


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


if __name__ == "__main__":
    status = BravoStatus(REALTIME_DESIRED_PACKETS, STARTUP_DESIRED_PACKETS)

    status.print_startup_status()

    # while True:
    #     try:
    #         time.sleep(0.1)
    #     except KeyboardInterrupt:
    #         status.stop()
    #         sys.exit()
