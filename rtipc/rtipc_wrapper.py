import array
from pathlib import Path


import cython

from cython.cimports.cpython.mem import PyMem_Malloc, PyMem_Calloc, PyMem_Free
from cython.cimports.cpython import array as carray
from cython.cimports.libc.string import memcpy

from cython.cimports import rtipc

from .attr import ChannelAttr, GroupAttr


@cython.cclass
class CInfo:
    data: cython.p_char
    size: cython.size_t

    def __cinit__(self):
        self.data = cython.NULL


    def __init__(self, info: bytes):
        self.size = len(info)
        self.data = cython.cast(cython.p_char, PyMem_Malloc(self.size))
        if not self.data:
            raise MemoryError()

        ptr: cython.p_char = info
        memcpy(self.data, ptr, self.size)

    def __dealloc__(self):
        if self.data is not cython.NULL:
           PyMem_Free(self.data)


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

        if not self._c_channel_attrs:
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
    def from_attr(attr: GroupAttr):
        cattr = CGroupAttr(attr)
        grp = CChannelGroup()
        grp._c_group = rtipc.ri_group_from_attr(cython.address(cattr.c_grp_attr))
        if grp._c_group is cython.NULL:
            raise RuntimeError()
        return grp

    @staticmethod
    def deserialize(req: bytes, fds: int[:]):
        n_fds: cython.uint  = len(fds)

        n_fds_ptr: cython.p_uint = cython.address(
            n_fds
        )

        cfds = cython.declare(carray.array, fds)
        fds_ptr = cython.cast(cython.p_int, cfds.data.as_voidptr)

        req_ptr = cython.cast(cython.p_void, req)

        grp = CChannelGroup()
        grp._c_group = rtipc.ri_group_deserialize(req_ptr, len(req), fds_ptr, n_fds_ptr)
        if grp._c_group is cython.NULL:
            raise RuntimeError()
        return grp

    def serialize(self) -> tuple(bytes, array.array):
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


    def acquire_consumer(self, index: int):
        if self._c_group is cython.NULL:
            raise RuntimeError()

    def acquire_producer(self, index: int):
        if self._c_group is cython.NULL:
            raise RuntimeError()



@cython.cclass
class CProducer:
    _c_producer: cython.pointer[rtipc.ri_producer_t]

    def __cinit__(self):
        self._c_producer = cython.NULL

    def __dealloc__(self):
        if self._c_producer is not cython.NULL:
            rtipc.ri_producer_release(self._c_producer)

    def try_push(self) -> rtipc.ri_try_push_result_t:
        if self._c_producer is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_producer_try_push(self._c_producer)

    def force_push(self) -> rtipc.ri_try_push_result_t:
        if self._c_producer is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_producer_force_push(self._c_producer)


@cython.cclass
class CConsumer:
    _c_consumer: cython.pointer[rtipc.ri_consumer_t]

    def __cinit__(self):
        self._c_consumer = cython.NULL

    def __dealloc__(self):
        if self._c_consumer is not cython.NULL:
            rtipc.ri_consumer_release(self._c_consumer)

    def pop(self) -> rtipc.ri_pop_result_t:
        if self._c_consumer is cython.NULL:
            raise RuntimeError()
        return rtipc.ri_consumer_pop(self._c_consumer)


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



