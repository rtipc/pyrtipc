from ctypes import Structure, c_int32, c_uint32
from enum import IntEnum


class CommandId(IntEnum):
    UNKNOWN = (0,)
    HELLO = (1,)
    STOP = (2,)
    SENDEVENT = (3,)
    DIV = (4,)


class MsgCommand(Structure):
    _fields_ = [("id", c_uint32), ("args", c_int32 * 3)]


class MsgResponse(Structure):
    _fields_ = [("id", c_uint32), ("result", c_int32), ("data", c_int32)]


class MsgEvent(Structure):
    _fields_ = [("id", c_uint32), ("nr", c_uint32)]
