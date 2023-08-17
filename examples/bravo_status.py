import struct
import time
import threading
import atexit
import yaml

import numpy as np

from pybravo import BravoDriver, PacketID, DeviceID, Packet, ModeID
from utils import parse_data, requests, axis_map, bcolors


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
        # atexit.register(self.stop)

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

    def set_parameter(self, device_id, packet_id, packed_data) -> None:
        packet = Packet(device_id, packet_id, packed_data)
        self._bravo.send(packet)

    def print_comparison(self, equal, print_vals, desired, actual, limit_name):
        if print_vals:
            if equal:
                print(
                    f"   {bcolors.OKGREEN}{bcolors.BOLD}{limit_name} Limits:{bcolors.ENDC}"
                )
                print(
                    f"{bcolors.OKGREEN}\tDesired: ({desired[0]:.2f}, {desired[1]:.2f})\n\tActual: ({actual[0]:.2f}, {actual[1]:.2f}){bcolors.ENDC}"
                )
            else:
                print(
                    f"   {bcolors.WARNING}{bcolors.BOLD}{limit_name} Limits:{bcolors.ENDC}"
                )
                print(
                    f"{bcolors.WARNING}\tDesired: ({desired[0]:.2f}, {desired[1]:.2f})\n\tActual: ({actual[0]:.2f}, {actual[1]:.2f}){bcolors.ENDC}"
                )

    def compare_status(
        self, curr_props: dict, bravo_limits_yaml: str, print_vals=True
    ) -> bool:
        """_summary_

        Args:
            curr_props (dict): _description_
            bravo_limits_yaml (str): _description_
            print_vals (bool): _description_

        Returns:
            bool: _description_
        """
        # Load desired limits as yaml into dictionary:
        limit_dict = None
        all_equal = True

        with open(bravo_limits_yaml, "r") as stream:
            try:
                limit_dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        if limit_dict:
            props = limit_dict["joint_limits"]
            for k, _ in props.items():
                if k in axis_map:
                    print(
                        f"{bcolors.HEADER}{bcolors.BOLD}{axis_map[k].name}{bcolors.ENDC}"
                    )
                    if props[k]["has_position_limits"]:
                        desired = tuple(props[k]["position_limits"])
                        actual = curr_props[axis_map[k]][PacketID.POSITION_LIMITS]
                        equal = np.allclose(desired, actual, atol=0.1)
                        if not equal:
                            self.set_parameter(
                                axis_map[k],
                                PacketID.POSITION_LIMITS,
                                struct.pack("ff", *desired),
                            )
                            all_equal = False
                        self.print_comparison(
                            equal, print_vals, desired, actual, "Position"
                        )

                    if props[k]["has_current_limits"]:
                        desired = tuple(props[k]["current_limits"])
                        actual = curr_props[axis_map[k]][PacketID.CURRENT_LIMITS]
                        equal = np.allclose(desired, actual, atol=0.1)
                        if not equal:
                            self.set_parameter(
                                axis_map[k],
                                PacketID.CURRENT_LIMITS,
                                struct.pack("ff", *desired),
                            )
                            all_equal = False
                        self.print_comparison(
                            equal, print_vals, desired, actual, "Current"
                        )

                    if props[k]["has_velocity_limits"]:
                        desired = tuple(props[k]["velocity_limits"])
                        actual = curr_props[axis_map[k]][PacketID.VELOCITY_LIMITS]
                        equal = np.allclose(desired, actual, atol=0.1)
                        if not equal:
                            self.set_parameter(
                                axis_map[k],
                                PacketID.VELOCITY_LIMITS,
                                struct.pack("ff", *desired),
                            )
                            all_equal = False
                        self.print_comparison(
                            equal, print_vals, desired, actual, "Velocity"
                        )

        else:
            print("Couldn't Load Limit File as Dictionary!")
            return False

        return all_equal
