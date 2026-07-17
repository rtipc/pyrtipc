from dataclasses import dataclass

@dataclass
class ChannelAttr:
    add_msgs: int
    msg_size: int
    eventfd: bool
    info: bytes


@dataclass
class GroupAttr:
    consumers: list[ChannelAttr]
    producers: list[ChannelAttr]
    info: bytes
