r"""
utility fxns for parsing bravo data
"""


import struct
import yaml

import numpy as np
import xml.etree.ElementTree as ET

from pybravo.protocol.packet_id import PacketID
from pybravo.protocol.device_id import DeviceID
from pybravo.protocol.packet import Packet
from pybravo.protocol.mode_id import ModeID

map = {
    "bravo_axis_a": DeviceID.LINEAR_JAWS,
    "bravo_axis_b": DeviceID.ROTATE_END_EFFECTOR,
    "bravo_axis_c": DeviceID.BEND_FOREARM,
    "bravo_axis_d": DeviceID.ROTATE_ELBOW,
    "bravo_axis_e": DeviceID.BEND_ELBOW,
    "bravo_axis_f": DeviceID.BEND_SHOULDER,
    "bravo_axis_g": DeviceID.ROTATE_BASE,
}
_position = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.POSITION.value])
)
_velocity = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VELOCITY.value])
)
_current = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.CURRENT.value])
)
_temperature = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.TEMPERATURE.value])
)
_serial_number = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.SERIAL_NUMBER.value])
)
_model_number = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.MODEL_NUMBER.value])
)
_voltage = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VOLTAGE.value])
)
_version = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.SOFTWARE_VERSION.value])
)
_mode = Packet(DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.MODE.value]))
_position_limits = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.POSITION_LIMITS.value])
)
_velocity_limits = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.VELOCITY_LIMITS.value])
)
_current_limits = Packet(
    DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.CURRENT_LIMITS.value])
)
_heartbeat_frequency = Packet(
    DeviceID.ALL_JOINTS,
    PacketID.REQUEST,
    bytes([PacketID.HEARTBEAT_FREQUENCY.value]),
)

requests = {
    PacketID.POSITION: _position,
    PacketID.VELOCITY: _velocity,
    PacketID.CURRENT: _current,
    PacketID.TEMPERATURE: _temperature,
    PacketID.SERIAL_NUMBER: _serial_number,
    PacketID.MODEL_NUMBER: _model_number,
    PacketID.VOLTAGE: _voltage,
    PacketID.SOFTWARE_VERSION: _version,
    PacketID.MODE: _mode,
    PacketID.HEARTBEAT_FREQUENCY: _heartbeat_frequency,
    PacketID.POSITION_LIMITS: _position_limits,
    PacketID.VELOCITY_LIMITS: _velocity_limits,
    PacketID.CURRENT_LIMITS: _current_limits,
}


def parse_data(self):
    """parses bravo packet data based on protocol"""
    if self.packet_id == PacketID.SOFTWARE_VERSION:
        parsed_data = f"{self.data[0]}.{self.data[1]}.{self.data[2]}"
    elif self.packet_id == PacketID.MODE:
        parsed_data = ModeID(self.data[0])
    elif self.packet_id in (
        PacketID.POSITION_LIMITS,
        PacketID.VELOCITY_LIMITS,
        PacketID.CURRENT_LIMITS,
    ):
        parsed_data = struct.unpack("ff", self.data)

    else:
        parsed_data = struct.unpack("<f", self.data)[0]

    return parsed_data


def compare_status(curr_props: dict, bravo_limits_yaml: str):
    """_summary_

    Args:
        current_properties (_type_): _description_
        bravo_limits_yaml (_type_): _description_
    """

    # Load desired limits as yaml into dictionary:
    limit_dict = None

    with open(bravo_limits_yaml, "r") as stream:
        try:
            limit_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    if limit_dict:
        props = limit_dict["joint_limits"]
        for k, _ in props.items():
            if k in map.keys():
                if props[k]["has_position_limits"]:
                    desired = tuple(props[k]["position_limits"])
                    actual = curr_props[map[k]][PacketID.POSITION_LIMITS]

                    if not np.allclose(desired, actual, atol=0.1):
                        print(map[k].name, desired, actual)

                if props[k]["has_current_limits"]:
                    desired = tuple(props[k]["current_limits"])
                    actual = curr_props[map[k]][PacketID.CURRENT_LIMITS]
                    if not np.allclose(desired, actual, atol=0.1):
                        print(map[k].name, desired, actual)

                if props[k]["has_velocity_limits"]:
                    desired = tuple(props[k]["velocity_limits"])
                    actual = curr_props[map[k]][PacketID.VELOCITY_LIMITS]
                    if not np.allclose(desired, actual, atol=0.1):
                        print(map[k].name, desired, actual)


def element_to_dict(element):
    """_summary_

    Args:
        element (_type_): _description_

    Returns:
        _type_: _description_
    """
    data = {}
    data["tag"] = element.tag
    data["attrib"] = element.attrib
    data["text"] = element.text
    data["children"] = [element_to_dict(child) for child in element]
    return data


def parse_xml_to_dict(xml_file):
    """_summary_

    Args:
        xml_file (_type_): _description_

    Returns:
        _type_: _description_
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    parsed_data = element_to_dict(root)
    return parsed_data


def extract_robot_properties(data):
    """_summary_

    Args:
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    robot_properties = {}

    for element in data:
        if "children" in element.keys():
            for children in element["children"]:
                if "tag" in children.keys():
                    if children["tag"] == "joint":
                        joint_name = children["attrib"]["name"]

                        for child in children["children"]:
                            if child["tag"] == "limit":
                                robot_properties[joint_name] = child["attrib"]
    return robot_properties
