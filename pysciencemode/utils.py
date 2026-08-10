import crccheck
from .enums import ErrorCode, Rehastim2Commands

"""
This code provides utility functions for working with the Rehastim device, including packet construction and data 
validation. It also includes functions to convert and check various parameters used in Rehastim communication.
"""


def signed_int(packet: bytes) -> int:
    """
    Converts a signed int from the packet received from the Rehastim.

    Parameters
    ----------
    packet: bytes
        Packet received from the Rehastim.
    Returns
    -------
    signed_int: int
        Signed int converted.
    """
    return int.from_bytes(packet, "big", signed=True)


def check_stimulation_interval(stimulation_interval: int = None):
    """
    Checks if the stimulation interval is within limits.

    Parameters
    ----------
    stimulation_interval: int
        Stimulation interval to check. If out of limits, raise a ValueError.

    """
    if stimulation_interval:
        if stimulation_interval < 8 or stimulation_interval > 1025:
            raise ValueError(
                "Error : Stimulation interval [8,1025]. Stimulation given : %s"
                % stimulation_interval
            )


def check_inter_pulse_interval(inter_pulse_interval: int = None):
    """
    Checks if the "inter pulse interval" is within limits.

    Parameters
    ----------
    inter_pulse_interval: int, optional
        Inter pulse interval to check. If out of limits, raise a ValueError.

    """
    if inter_pulse_interval:
        if inter_pulse_interval < 2 or inter_pulse_interval > 129:
            raise ValueError(
                "Error : Inter pulse interval [2,129], given : %s"
                % inter_pulse_interval
            )


def check_low_frequency_factor(low_frequency_factor: int = None):
    """
    Checks if the low frequency factor is within limits.

    Parameters
    ----------
    low_frequency_factor: int, optional
        Low frequency factor to check. If out of limits, raise a ValueError.
    """
    if low_frequency_factor:
        if low_frequency_factor < 0 or low_frequency_factor > 7:
            raise ValueError(
                "Error : Low frequency factor [0,7], given : %s" % low_frequency_factor
            )


def check_unique_channel(list_channels: list = None) -> bool:
    """
    Checks if there is not 2 times the same channel in the list given.

    Parameters
    ----------
    list_channels: list[Channel], optional
        Contains a list of channel.

    Returns
    -------
    True if all channels are unique, False and print a warning if not.
    """
    if list_channels:
        active_channel = []
        for i in range(len(list_channels)):
            if list_channels[i].get_no_channel() in active_channel:
                print(
                    "Warning : 2 channel no%s" % list_channels[i].get_no_channel()
                    + " in list_channels given. The first one given will be used."
                )
                list_channels.pop(i)
                return False
            else:
                active_channel.append(list_channels[i].get_no_channel())
        return True


def check_list_channel_order(list_channels):
    """
    Checks if the channels in the list_channels given are ordered.

    Parameters
    ----------
    list_channels: list[Channel]
        Contains the channels. Raises a RuntimeError if not ordered.
    """
    number_previous_channel = 0
    for i in range(len(list_channels)):
        if list_channels[i].get_no_channel() < number_previous_channel:
            raise RuntimeError(
                "Error: channels in list_channels given are not in order."
            )
        number_previous_channel = list_channels[i].get_no_channel()


def check_stimulation_parameter_list(
    list_channels: list, parameter_list: dict, parameter_name: str
) -> int:
    """
    Checks if a stimulation parameter is given for each channel and if all the lists have the same length.
    Used for the pulse by pulse stimulation of the P24.

    Parameters
    ----------
    list_channels: list[Channel]
        Contains the channels that will be stimulated.
    parameter_list: dict
        Contains the parameter sent for each pulse. The key is the channel number and the value is the list of the
        parameter values sent one pulse after the other.
    parameter_name: str
        Name of the checked parameter. Only used to build the error messages.

    Returns
    -------
    nb_pulses: int
        Number of pulses which will be sent.
    """
    if not isinstance(parameter_list, dict):
        raise TypeError(
            "Error : the %s list must be a dict, %s given."
            % (parameter_name, type(parameter_list).__name__)
        )

    for channel in list_channels:
        if channel.get_no_channel() not in parameter_list:
            raise ValueError(
                "Error : no %s given for channel no%s."
                % (parameter_name, channel.get_no_channel())
            )

    nb_pulses = [
        len(parameter_list[channel.get_no_channel()]) for channel in list_channels
    ]
    if len(set(nb_pulses)) != 1:
        raise ValueError(
            "Error : all the %s lists must have the same length, given lengths : %s."
            % (parameter_name, nb_pulses)
        )
    if nb_pulses[0] == 0:
        raise ValueError(
            "Error : please provide at least one %s for stimulation." % parameter_name
        )

    return nb_pulses[0]


def check_pulse_interval_list(pulse_interval_list: list, nb_pulses: int):
    """
    Checks if an interval is given for each pulse and if the intervals are within limits.
    Used for the pulse by pulse stimulation of the P24.

    Parameters
    ----------
    pulse_interval_list: list
        Contains the interval in ms between a pulse and the next one.
    nb_pulses: int
        Number of pulses which will be sent.
    """
    if not isinstance(pulse_interval_list, list):
        raise TypeError(
            "Error : the pulse interval list must be a list, %s given."
            % type(pulse_interval_list).__name__
        )
    if len(pulse_interval_list) != nb_pulses:
        raise ValueError(
            "Error : one pulse interval must be given for each pulse, %s pulse intervals given for %s pulses."
            % (len(pulse_interval_list), nb_pulses)
        )
    for pulse_interval in pulse_interval_list:
        if not 0.5 <= pulse_interval <= 16383:
            raise ValueError(
                "Error : pulse interval min = 0.5ms, max = 16383ms, value given %sms."
                % pulse_interval
            )


def calc_electrode_number(
    list_channels: list, enable_low_frequency: bool = False
) -> int:
    """
    When enable_low_frequency = False :
    Calculates the number corresponding to which electrode is activated.
    During the initialisation, the computer needs to tell the Rehastim which channel needs to be activated. It is
    done through the addition of 2 pow the number of the channel.
    For example if the channel 1 and 4 needs to be activated, electrode_number = 2**1 + 2**4

    When enable_low_frequency = True :
    Calculates the number corresponding to which electrode has the low_frequency_factor enabled.

    Parameters
    ----------
    list_channels: list[Channel]
        Contains the channels that will be activated.
    enable_low_frequency: bool
        Choose whether the number correspond to active channel (False) or correspond to channel with low frequency
        factor enabled (True).

    Returns
    -------
    electrode_number: int
        Electrode number calculated.
    """
    electrode_number = 0
    for i in range(len(list_channels)):
        if enable_low_frequency:
            if list_channels[i].get_enable_low_frequency():
                electrode_number += 2 ** (list_channels[i].get_no_channel() - 1)
        if not enable_low_frequency:
            electrode_number += 2 ** (list_channels[i].get_no_channel() - 1)
    return electrode_number


def packet_construction(
    packet_count: int, packet_type: str, packet_data: list = None
) -> bytes:
    """
    Constructs the packet which will be sent to the Rehastim.

    Parameters
    ----------
    packet_count: int
        Correspond to the number of packet sent to the Rehastim.
    packet_type: str
        Correspond to the command that will be sent.
    packet_data: list
        Contain the data of the packet.

    Returns
    -------
    packet_construct: bytes
        Packet constructed which will be sent.
    """

    start_byte = 0xF0
    stop_byte = 0x0F
    stuffing_byte = 0x81

    packet = [start_byte]
    packet_command = Rehastim2Commands[packet_type].value
    packet_payload = [packet_count, packet_command]
    packet_payload = _stuff_packet_byte(packet_payload)
    if packet_data is not None:
        packet_data = _stuff_packet_byte(packet_data, command_data=True)
        packet_payload += packet_data

    checksum = crccheck.crc.Crc8.calc(packet_payload)
    checksum = _stuff_byte(checksum)
    data_length = _stuff_byte(len(packet_payload))

    packet = (
        packet
        + [stuffing_byte]
        + [checksum]
        + [stuffing_byte]
        + [data_length]
        + packet_payload
        + [stop_byte]
    )
    return b"".join([byte.to_bytes(1, "little") for byte in packet])


def _stuff_packet_byte(packet: list, command_data: bool = False) -> list:
    """
    Stuffs each byte if necessary of the packet.

    Parameters
    ----------
    packet: list
        Packet containing the bytes that will be checked and stuffed if necessary.
    command_data: bool
        True if the packet is a command data, False if not.
    Returns
    -------
    packet: list
        Packet returned with stuffed byte.
    """
    stuffed_bytes = [240, 15, 129, 85, 10]
    stuffing_byte = 0x81

    if command_data:
        packet_tmp = []
        for i in range(len(packet)):
            if packet[i] in stuffed_bytes:
                packet_tmp = packet_tmp + [stuffing_byte, _stuff_byte(packet[i])]
            else:
                packet_tmp.append(packet[i])
        return packet_tmp
    else:
        for i in range(len(packet)):
            if packet[i] in stuffed_bytes:
                packet[i] = _stuff_byte(packet[i])
        return packet


def _stuff_byte(byte: int) -> int:
    """
    Stuffs the byte given.
    Parameters
    ----------
    byte: int
        Byte which needs to be stuffed.
    Returns
    -------
    byte_stuffed: int
        The byte stuffed.
    """
    stuffing_key = 0x55

    return (byte & ~stuffing_key) | (~byte & stuffing_key)


def generic_error_check(ack_object):
    error_code = ErrorCode(ack_object.result)
    if error_code.message:
        raise ValueError(error_code.message)
