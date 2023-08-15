import struct
import time
import threading
import atexit

from pybravo import BravoDriver, PacketID, DeviceID, Packet, ModeID


def parse_data(packet):
    """parses bravo packet data based on protocol"""
    if packet.packet_id == PacketID.SOFTWARE_VERSION:
        data = (packet.data[0], packet.data[1], packet.data[2])
    elif packet.packet_id == PacketID.MODE:
        data = ModeID(packet.data[0])
    elif packet.packet_id in (
        PacketID.POSITION_LIMITS,
        PacketID.VELOCITY_LIMITS,
        PacketID.CURRENT_LIMITS,
    ):
        data = struct.unpack("ff", packet.data)

    else:
        data = struct.unpack("<f", packet.data)[0]

    return data


class BravoRequests:
    """Class listing different requests"""

    position = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.POSITION.value])
    )
    velocity = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VELOCITY.value])
    )
    current = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.CURRENT.value])
    )
    temperature = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.TEMPERATURE.value])
    )
    serial_number = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.SERIAL_NUMBER.value])
    )
    model_number = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.MODEL_NUMBER.value])
    )
    voltage = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VOLTAGE.value])
    )
    version = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.SOFTWARE_VERSION.value])
    )
    mode = Packet(DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.MODE.value]))
    position_limits = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.POSITION_LIMITS.value])
    )
    velocity_limits = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VELOCITY_LIMITS.value])
    )
    current_limits = Packet(
        DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.CURRENT_LIMITS.value])
    )
    heartbeat_frequency = Packet(
        DeviceID.ALL_JOINTS,
        PacketID.REQUEST,
        bytes([PacketID.HEARTBEAT_FREQUENCY.value]),
    )

    requests = {
        PacketID.POSITION: position,
        PacketID.VELOCITY: velocity,
        PacketID.CURRENT: current,
        PacketID.TEMPERATURE: temperature,
        PacketID.SERIAL_NUMBER: serial_number,
        PacketID.MODEL_NUMBER: model_number,
        PacketID.VOLTAGE: voltage,
        PacketID.SOFTWARE_VERSION: version,
        PacketID.MODE: mode,
        PacketID.HEARTBEAT_FREQUENCY: heartbeat_frequency,
        PacketID.POSITION_LIMITS: position_limits,
        PacketID.VELOCITY_LIMITS: velocity_limits,
        PacketID.CURRENT_LIMITS: current_limits,
    }


class BravoStatus:
    """Class to print out the bravo status"""

    def __init__(self, realtime_packets, startup_packets) -> None:
        # Create Bravo Driver:
        self._bravo = BravoDriver()
        self._bravo.connect()

        self.req = BravoRequests()
        self.realtime_packets = realtime_packets
        self.startup_packets = startup_packets
        self._running = False
        self._startup_status = False
        self._realtime_status = False

        # All Bravo Properties
        self.properties = {}
        for i in range(1, 7):
            self.properties[DeviceID(i)] = {}

        for packet_id in self.realtime_packets:
            self._bravo.attach_callback(packet_id, self.packet_callback)

        for packet_id in self.startup_packets:
            self._bravo.attach_callback(packet_id, self.packet_callback)

        # Poll start-up info once:
        self.poll_startup_status()

        # Make sure that we shutdown the interface when we exit
        # atexit.register(self.stop)

    def poll_startup_status(self) -> None:
        """blah"""
        for packet in self.startup_packets:
            self._bravo.send(self.req.requests[packet])
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
                self._bravo.send(self.req.requests[packet])
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
        self._bravo.disconnect()
        self.poll_t.join()

    def packet_callback(self, packet: Packet) -> None:
        """
        Args:
            packet: The joint position packet.
        """
        try:
            data = parse_data(packet)
            self.properties[packet.device_id][packet.packet_id] = data
        except KeyError:
            pass

    def print_startup_status(self) -> None:
        """ """
        if self._startup_status is False:
            self.poll_startup_status()
            self._startup_status = True

        for dev_k, dev_v in self.properties.items():
            for prop_k, prop_v in self.properties[dev_k].items():
                if prop_k in self.startup_packets:
                    print(dev_k, prop_k, prop_v)

    def print_rt_status(self) -> None:
        pass
