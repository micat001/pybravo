import struct
import time
import threading
import atexit

from pybravo import BravoDriver, PacketID, DeviceID, Packet, ModeID

from utils import parse_data, requests


class BravoStatus:
    """Class to check and print out the bravo status"""

    def __init__(self, realtime_packets, startup_packets) -> None:
        # Create Bravo Driver:
        self._bravo = BravoDriver()
        self._bravo.connect()

        self.requests = requests
        self.realtime_packets = realtime_packets
        self.startup_packets = startup_packets
        self._running = False
        self._startup_status = False
        self._realtime_status = False

        # All Bravo Properties
        self.properties = {}
        for i in range(0, 7):
            self.properties[DeviceID(i + 1)] = {}

        for packet_id in self.realtime_packets:
            self._bravo.attach_callback(packet_id, self.packet_callback)

        for packet_id in self.startup_packets:
            self._bravo.attach_callback(packet_id, self.packet_callback)

        # Poll start-up info once:
        self.poll_startup_status()

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.stop)

    def poll_startup_status(self) -> None:
        """blah"""
        for packet in self.startup_packets:
            self._bravo.send(self.requests[packet])
            time.sleep(0.01)

    def poll_realtime_status(self) -> None:
        """request status at high rate"""
        if self._realtime_status is False:
            # Create a new thread to poll everything we care about real-time
            self.poll_t = threading.Thread(target=self.poll_realtime_status)
            self.poll_t.daemon = True
            self._realtime_status = True

        while self._running:
            for packet in self.realtime_packets:
                self._bravo.send(self.requests[packet])
                time.sleep(0.01)

    def start(self) -> None:
        """Start the reader."""
        # Start a connection to the Bravo
        # self._bravo.connect()

        # Start the polling thread
        self._running = True
        self.poll_t.start()

    def stop(self) -> None:
        """Stop the reader."""
        # Stop the poll thread loop
        self._running = False
        time.sleep(0.01)
        # Disconnect the bravo driver
        try:
            self._bravo.disconnect()
            self.poll_t.join()
        except AttributeError:
            ...

    def packet_callback(self, packet: Packet) -> None:
        """
        Args:
            packet: The joint position packet.
        """
        try:
            self.properties[packet.device_id][packet.packet_id] = parse_data(packet)
        except KeyError:
            pass

    def get_startup_status(self) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        if self._startup_status is False:
            self.poll_startup_status()
            self._startup_status = True
        return self.properties

    def print_startup_status(self) -> None:
        """_summary_"""
        if self._startup_status is False:
            self.poll_startup_status()
            self._startup_status = True

        device_status = [
            PacketID.SERIAL_NUMBER,
            PacketID.MODEL_NUMBER,
            PacketID.SOFTWARE_VERSION,
            PacketID.HEARTBEAT_FREQUENCY,
        ]

        joint_status = [
            PacketID.POSITION_LIMITS,
            PacketID.VELOCITY_LIMITS,
            PacketID.CURRENT_LIMITS,
        ]

        print("----------DEVICE STATUS----------")
        for dev_k, _ in self.properties.items():
            for prop_k, prop_v in self.properties[dev_k].items():
                if prop_k in device_status:
                    if prop_k == PacketID.SERIAL_NUMBER:
                        print(f"{prop_k.name}: \t\t{prop_v:.0f}")
                    elif prop_k == PacketID.SOFTWARE_VERSION:
                        print(f"{prop_k.name}: \t{prop_v}")

                    elif prop_k == PacketID.MODEL_NUMBER:
                        print(f"{prop_k.name}: \t\t{prop_v}")
            break
        print()

        print("----------JOINT STATUS----------")
        for dev_k, _ in self.properties.items():
            print(f"{dev_k.name}:")
            for prop_k, prop_v in self.properties[dev_k].items():
                if prop_k in joint_status:
                    print(f"\t{prop_k.name}: \t[{prop_v[1]:.2f}, {prop_v[0]:.2f}]")
            print()

    def print_rt_status(self) -> None:
        pass
