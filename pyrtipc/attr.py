from dataclasses import dataclass


@dataclass
class ChannelAttributes:
    add_msgs: int
    msg_size: int
    eventfd: bool
    info: bytes


@dataclass
class GroupAttributes:
    consumers: list[ChannelAttributes]
    producers: list[ChannelAttributes]
    info: bytes
