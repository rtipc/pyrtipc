import array
from enum import IntEnum
from pathlib import Path


import cython

from cython.cimports.cpython.mem import PyMem_Malloc, PyMem_Calloc, PyMem_Free
from cython.cimports.cpython import array as carray
from cython.cimports.libc.string import memcpy
from cython.cimports.cython.view import array as cvarray

from cython.cimports import rtipc

from .attr import ChannelAttr, GroupAttr

class TryPushResult(IntEnum):
    ERROR = rtipc.ri_try_push_result_t.RI_TRY_PUSH_RESULT_ERROR,
    FAIL = rtipc.ri_try_push_result_t.RI_TRY_PUSH_RESULT_FAIL,
    SUCCESS = rtipc.ri_try_push_result_t.RI_TRY_PUSH_RESULT_SUCCESS,
    
class ForcePushResult(IntEnum):
    ERROR = rtipc.ri_force_push_result_t.RI_FORCE_PUSH_RESULT_ERROR,
    SUCCESS = rtipc.ri_force_push_result_t.RI_FORCE_PUSH_RESULT_SUCCESS,
    DICARDED = rtipc.ri_force_push_result_t.RI_FORCE_PUSH_RESULT_DISCARDED,
    
class PopResult(IntEnum):
    ERROR = rtipc.ri_pop_result_t.RI_POP_RESULT_ERROR,
    NO_MSG = rtipc.ri_pop_result_t.RI_POP_RESULT_NO_MSG,
    NO_UPDATE = rtipc.ri_pop_result_t.RI_POP_RESULT_NO_UPDATE,
    SUCCESS = rtipc.ri_pop_result_t.RI_POP_RESULT_SUCCESS,
    DICARDED = rtipc.ri_pop_result_t.RI_POP_RESULT_DISCARDED,


def get_memoryview(c_ptr: cython.pointer(cython.char), size: cython.int):
    arr = cvarray(shape=(size,), itemsize=1, format="B", mode="c", allocate_buffer=False)
    arr.data = cython.cast(cython.pointer(cython.char), c_ptr)
    
    arr_view = cython.declare(cython.char[:], arr)
    
    return arr_view

@cython.cclass
class CInfo:
    data: cython.p_void
    size: cython.size_t


def info_to_bytes(info: CInfo) -> bytes:
    if info.size > 0:
        char_ptr = cython.cast(cython.p_char, info.data)
        return char_ptr[:info.size]
    else:
        return bytes()


@cython.cclass
class CGroupAttr:
    _c_chnl_attrs: cython.pointer[rtipc.ri_channel_attr_t]
    c_grp_attr: rtipc.ri_group_attr_t

    def __cinit__(self):
        self._c_chnl_attrs = cython.NULL


    def __init__(self, grp_attr: GroupAttr):
        n_consumers = len(grp_attr.consumers)
        n_producers = len(grp_attr.producers)

        n_channels = n_consumers + n_producers + 2

        self._c_chnl_attrs = cython.cast(
            cython.pointer[rtipc.ri_channel_attr_t],
            PyMem_Calloc(n_channels, cython.sizeof(rtipc.ri_channel_attr_t)),
        )

        if not self._c_chnl_attrs:
            raise MemoryError()

        consumers: cython.pointer[rtipc.ri_channel_attr_t] = cython.address(
            self._c_chnl_attrs[0]
        )
        producers: cython.pointer[rtipc.ri_channel_attr_t] = cython.address(
            self._c_chnl_attrs[n_consumers + 1]
        )

        grp_info_ptr: cython.p_char = grp_attr.info

        self.c_grp_attr = rtipc.ri_group_attr_t(
            consumers=consumers,
            producers=producers,
            info = rtipc.ri_info_t(size=len(grp_attr.info), data=grp_info_ptr),
        )

        for i, attr in enumerate(grp_attr.consumers):
            info_ptr: cython.p_char = attr.info
            c_attr: cython.pointer[rtipc.ri_channel_attr_t] = cython.address(
                consumers[i]
            )
            c_attr.add_msgs = attr.add_msgs
            c_attr.msg_size = attr.msg_size
            c_attr.eventfd = attr.eventfd
            c_attr.info.size = len(attr.info)
            c_attr.info.data = info_ptr

        for i, attr in enumerate(grp_attr.producers):
            info_ptr: cython.p_char = attr.info
            c_attr: cython.pointer[rtipc.ri_channel_attr_t] = cython.address(
                producers[i]
            )
            c_attr.add_msgs = attr.add_msgs
            c_attr.msg_size = attr.msg_size
            c_attr.eventfd = attr.eventfd
            c_attr.info.size = len(attr.info)
            c_attr.info.data = info_ptr

    def __dealloc__(self):
        if self._c_chnl_attrs is not cython.NULL:
            PyMem_Free(self._c_chnl_attrs)




@cython.cclass
class CChannelGroup:
    _c_group: cython.pointer[rtipc.ri_group_t]

    def __cinit__(self):
        self._c_group = cython.NULL

    def __dealloc__(self):
        if self._c_group is not cython.NULL:
            rtipc.ri_group_delete(self._c_group)


    @staticmethod
    def from_attr(attr: GroupAttr) -> CChannelGroup:
        cattr = CGroupAttr(attr)
        grp = CChannelGroup()
        grp._c_group = rtipc.ri_group_from_attr(cython.address(cattr.c_grp_attr))
        if grp._c_group is cython.NULL:
            raise RuntimeError()
        return grp

    @staticmethod
    def deserialize(req: bytes, fds: array.array) -> CChannelGroup:
        n_fds: cython.uint  = len(fds)

        n_fds_ptr: cython.p_uint = cython.address(
            n_fds
        )

        cfds = cython.declare(carray.array, fds)
        fds_ptr = cython.cast(cython.p_int, cfds.data.as_voidptr)

        req_ptr = cython.cast(cython.p_char, req)
        
        grp = CChannelGroup()
        grp._c_group = rtipc.ri_group_deserialize(req_ptr, len(req), fds_ptr, n_fds_ptr)
        if grp._c_group is cython.NULL:
            raise RuntimeError()
        return grp

    def serialize(self) -> tuple(bytearray, array.array):
        if self._c_group is cython.NULL:
            raise RuntimeError()
        size: cython.size_t  = rtipc.ri_group_serialize_size(self._c_group)
        req = bytearray(size)
        req_ptr: cython.p_char = req
        fds = array.array('i', [-1] * 253)
        n_fds : cython.uint = len(fds)
        n_fds_ptr = cython.address(n_fds)
        cfds: cython.int[:] = fds
        cfds_ptr: cython.p_int = cython.address(cfds[0])
        r =  rtipc.ri_group_serialize(self._c_group, req_ptr, size, cfds_ptr, n_fds_ptr)
        if r < 0:
            raise RuntimeError()
            
        return (req, fds[0:n_fds])
        
    def get_attr(self) -> GroupAttr:
        if self._c_group is cython.NULL:
            raise RuntimeError()
        c_attr = rtipc.ri_group_get_attr(self._c_group)
        
        
        consumers = []
        for i in range(0,  rtipc.ri_group_num_consumers(self._c_group)):
            c_chn_attr = c_attr.consumers[i]
            c_info = CInfo()
            c_info.size = c_chn_attr.info.size
            c_info.data = c_chn_attr.info.data
            chn_attr = ChannelAttr(c_chn_attr.add_msgs, c_chn_attr.msg_size, c_chn_attr.eventfd, info_to_bytes(c_info))
            consumers.append(chn_attr)

    
        producers = []
        for i in range(0, rtipc.ri_group_num_producers(self._c_group)):
            c_chn_attr = c_attr.producers[i]
            c_info = CInfo()
            c_info.size = c_chn_attr.info.size
            c_info.data = c_chn_attr.info.data
            chn_attr = ChannelAttr(c_chn_attr.add_msgs, c_chn_attr.msg_size, c_chn_attr.eventfd, info_to_bytes(c_info))
            producers.append(chn_attr)
        
        c_info = CInfo()
        c_info.size = c_attr.info.size
        c_info.data = c_attr.info.data
        grp_info = info_to_bytes(c_info)
        
        return GroupAttr(consumers, producers, grp_info)
            

    def num_consumers(self) -> int:
        if self._c_group is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_group_num_consumers(self._c_group)
        
    def num_producers(self) -> int:
        if self._c_group is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_group_num_producers(self._c_group)

    def acquire_consumer(self, index: int) -> CConsumer:
        if self._c_group is cython.NULL:
            raise RuntimeError()
        consumer = CConsumer()
        consumer._c_consumer = rtipc.ri_group_acquire_consumer(self._c_group, index)
        if consumer._c_consumer is cython.NULL:
            raise RuntimeError()
        return consumer
        

    def acquire_producer(self, index: int) -> CProducer:
        if self._c_group is cython.NULL:
            raise RuntimeError()
        producer = CProducer()
        producer._c_producer = rtipc.ri_group_acquire_producer(self._c_group, index)
        if producer._c_producer is cython.NULL:
            raise RuntimeError()
        return producer



@cython.cclass
class CProducer:
    _c_producer: cython.pointer[rtipc.ri_producer_t]

    def __cinit__(self):
        self._c_producer = cython.NULL

    def __dealloc__(self):
        if self._c_producer is not cython.NULL:
            rtipc.ri_producer_release(self._c_producer)

    def msg_size(self) -> int:
        if self._c_producer is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_producer_msg_size(self._c_producer)
    
    def current_msg(self):
        if self._c_producer is cython.NULL:
            raise RuntimeError()
            
        msg_ptr = rtipc.ri_producer_msg(self._c_producer)
        if msg_ptr is cython.NULL:
            return None
            
        msg_size = rtipc.ri_producer_msg_size(self._c_producer)
        msg_char_ptr = cython.cast(cython.pointer(cython.char), msg_ptr)
        
        return get_memoryview(msg_char_ptr, msg_size)
    
        
    def try_push(self) -> TryPushResult:
        if self._c_producer is cython.NULL:
            raise RuntimeError()
        result = rtipc.ri_producer_try_push(self._c_producer)
        return TryPushResult(result)

    def force_push(self) -> ForcePushResult:
        if self._c_producer is cython.NULL:
            raise RuntimeError()
            
        result = rtipc.ri_producer_force_push(self._c_producer)
        
        return ForcePushResult(result)


@cython.cclass
class CConsumer:
    _c_consumer: cython.pointer[rtipc.ri_consumer_t]

    def __cinit__(self):
        self._c_consumer = cython.NULL

    def __dealloc__(self):
        if self._c_consumer is not cython.NULL:
            rtipc.ri_consumer_release(self._c_consumer)

    def msg_size(self) -> int:
        if self._c_consumer is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_consumer_msg_size(self._c_consumer)


    def pop(self) -> PopResult:
        if self._c_consumer is cython.NULL:
            raise RuntimeError()
            
        result = rtipc.ri_consumer_pop(self._c_consumer)
        
        return PopResult(result)
    
    def current_msg(self):
        if self._c_consumer is cython.NULL:
            raise RuntimeError()
            
        msg_ptr = rtipc.ri_consumer_msg(self._c_consumer)
        if msg_ptr is cython.NULL:
            return None
            
        msg_size = rtipc.ri_consumer_msg_size(self._c_consumer)
        msg_char_ptr = cython.cast(cython.p_char, msg_ptr)
        
        return get_memoryview(msg_char_ptr, msg_size)

    def get_eventfd(self) -> int:
        if self._c_consumer is cython.NULL:
            raise RuntimeError()
            
@cython.cclass
class CServer:
    _c_server: cython.pointer[rtipc.ri_server_t]

    def __cinit__(self):
        _c_server = cython.NULL

    def __init__(self, path: Path):
        ptr: cython.p_char = path
        self._c_server = rtipc.ri_server_new(ptr, 0)

    def __dealloc__(self):
        if self._c_server is not cython.NULL:
            rtipc.ri_server_delete(self._c_server)

    def accept(self) -> CChannelGroup:
        grp = CChannelGroup()
        grp._c_group = rtipc.ri_server_accept(self._c_server, cython.NULL, cython.NULL)
        if grp._c_group is cython.NULL:
            raise RuntimeError()
        return grp



