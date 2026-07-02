from dataclasses import dataclass

@dataclass
class MqAttr:
    add_msgs: int
    msg_size: int
    info: bytes


@dataclass
class VectorConfig:
    consumers: list[MqAttr]
    producers: list[MqAttr]
    info: bytes
