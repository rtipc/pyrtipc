import ctypes

from pyrtipc import ChannelAttributes, GroupAttributes


class SendEventArgs(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("force", ctypes.c_bool),
        ("num", ctypes.c_uint32),
    ]


class DivArgs(ctypes.Structure):
    _fields_ = [
        ("divisor", ctypes.c_double),
        ("divident", ctypes.c_double),
    ]


class CommandArgs(ctypes.Union):
    _fields_ = [
        ("div", DivArgs),
        ("send", SendEventArgs),
    ]


class MsgCommand(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("args", CommandArgs),
    ]


class ResponseData(ctypes.Union):
    _fields_ = [
        ("quotient", ctypes.c_double),
    ]


class MsgResponse(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("result", ctypes.c_int32),
        ("data", ResponseData),
    ]


class MsgEvent(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("nr", ctypes.c_uint32),
    ]


SEND_EVENT_ARGS_INFO = bytes(
    [0x2, 0x3, 0x2, 0x69, 0x64, 0x1, 0x13, 0x5, 0x66, 0x6f, 0x72, 0x63, 0x65, 0x1, 0x0, 0x3, 0x6e,
    0x75, 0x6d, 0x1, 0x13,]
)

DIV_ARGS_INFO = bytes(
    [0x2, 0x2, 0x7, 0x64, 0x69, 0x76, 0x69, 0x73, 0x6f, 0x72, 0x1, 0x24, 0x8, 0x64, 0x69, 0x76,
    0x69, 0x64, 0x65, 0x6e, 0x74, 0x1, 0x24,]
)

COMMAND_ARGS_INFO = bytes(
    [0x3, 0x2, 0x3, 0x64, 0x69, 0x76, 0x2, 0x2, 0x7, 0x64, 0x69, 0x76, 0x69, 0x73, 0x6f, 0x72, 0x1,
    0x24, 0x8, 0x64, 0x69, 0x76, 0x69, 0x64, 0x65, 0x6e, 0x74, 0x1, 0x24, 0x4, 0x73, 0x65, 0x6e,
    0x64, 0x2, 0x3, 0x2, 0x69, 0x64, 0x1, 0x13, 0x5, 0x66, 0x6f, 0x72, 0x63, 0x65, 0x1, 0x0, 0x3,
    0x6e, 0x75, 0x6d, 0x1, 0x13,]
)

MSG_COMMAND_INFO = bytes(
    [0x2, 0x2, 0x2, 0x69, 0x64, 0x1, 0x13, 0x4, 0x61, 0x72, 0x67, 0x73, 0x3, 0x2, 0x3, 0x64, 0x69,
    0x76, 0x2, 0x2, 0x7, 0x64, 0x69, 0x76, 0x69, 0x73, 0x6f, 0x72, 0x1, 0x24, 0x8, 0x64, 0x69,
    0x76, 0x69, 0x64, 0x65, 0x6e, 0x74, 0x1, 0x24, 0x4, 0x73, 0x65, 0x6e, 0x64, 0x2, 0x3, 0x2,
    0x69, 0x64, 0x1, 0x13, 0x5, 0x66, 0x6f, 0x72, 0x63, 0x65, 0x1, 0x0, 0x3, 0x6e, 0x75, 0x6d, 0x1,
    0x13,]
)

RESPONSE_DATA_INFO = bytes(
    [0x3, 0x1, 0x8, 0x71, 0x75, 0x6f, 0x74, 0x69, 0x65, 0x6e, 0x74, 0x1, 0x24,]
)

MSG_RESPONSE_INFO = bytes(
    [0x2, 0x3, 0x2, 0x69, 0x64, 0x1, 0x13, 0x6, 0x72, 0x65, 0x73, 0x75, 0x6c, 0x74, 0x1, 0x3, 0x4,
    0x64, 0x61, 0x74, 0x61, 0x3, 0x1, 0x8, 0x71, 0x75, 0x6f, 0x74, 0x69, 0x65, 0x6e, 0x74, 0x1,
    0x24,]
)

MSG_EVENT_INFO = bytes(
    [0x2, 0x2, 0x2, 0x69, 0x64, 0x1, 0x13, 0x2, 0x6e, 0x72, 0x1, 0x13,]
)

RPC_INFO = bytes(
    [0x3, 0x52, 0x50, 0x43, 0x7, 0x63, 0x6f, 0x6d, 0x6d, 0x61, 0x6e, 0x64, 0x8, 0x72, 0x65, 0x73,
    0x70, 0x6f, 0x6e, 0x73, 0x65, 0x5, 0x65, 0x76, 0x65, 0x6e, 0x74,]
)

rpc_c2s_channels = [
    ChannelAttributes(0, ctypes.sizeof(MsgCommand), True, MSG_COMMAND_INFO),
]
rpc_s2c_channels = [
    ChannelAttributes(0, ctypes.sizeof(MsgResponse), True, MSG_RESPONSE_INFO),
    ChannelAttributes(10, ctypes.sizeof(MsgEvent), True, MSG_EVENT_INFO),
]


client_group_rpc = GroupAttributes(
    consumers=rpc_s2c_channels, producers=rpc_c2s_channels, info=RPC_INFO
)


def client_rpc_acquire_response(group: ChannelGroup) -> Consumer[MsgResponse]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.consumers[0]

    expect_attr = client_group_rpc.consumers[0]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_consumer(MsgResponse, 0)


def client_rpc_acquire_event(group: ChannelGroup) -> Consumer[MsgEvent]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.consumers[1]

    expect_attr = client_group_rpc.consumers[1]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_consumer(MsgEvent, 1)


def client_rpc_acquire_command(group: ChannelGroup) -> Producer[MsgCommand]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.producers[0]

    expect_attr = client_group_rpc.producers[0]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_producer(MsgCommand, 0)


server_group_rpc = GroupAttributes(
    consumers=rpc_c2s_channels, producers=rpc_s2c_channels, info=RPC_INFO
)


def server_rpc_acquire_command(group: ChannelGroup) -> Consumer[MsgCommand]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.consumers[0]

    expect_attr = server_group_rpc.consumers[0]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_consumer(MsgCommand, 0)


def server_rpc_acquire_response(group: ChannelGroup) -> Producer[MsgResponse]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.producers[0]

    expect_attr = server_group_rpc.producers[0]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_producer(MsgResponse, 0)


def server_rpc_acquire_event(group: ChannelGroup) -> Producer[MsgEvent]:
    group_attr = group.get_attributes()
    remote_attr = group_attr.producers[1]

    expect_attr = server_group_rpc.producers[1]
    if expect_attr != remote_attr:
        raise RuntimeError()

    return group.acquire_producer(MsgEvent, 1)
