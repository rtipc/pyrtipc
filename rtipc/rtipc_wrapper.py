import array
from pathlib import Path


import cython

from cython.cimports.cpython.mem import PyMem_Malloc, PyMem_Calloc, PyMem_Free
from cython.cimports.cpython import array as carray
from cython.cimports.libc.string import memcpy

from cython.cimports import rtipc

from .config import MqAttr, VectorConfig


@cython.cclass
class CInfo:
    data: cython.p_char
    size: cython.size_t

    def __init__(self, info: bytes):
        self.size = len(info)
        self.data = cython.cast(cython.p_char, PyMem_Malloc(self.size))
        if not self.data:
            raise MemoryError()

        ptr: cython.p_char = info
        memcpy(self.data, ptr, self.size)

    def __dealloc__(self):
        PyMem_Free(self.data)


@cython.cclass
class CVectorConfig:
    _c_attrs: cython.pointer[rtipc.ri_attr_t]
    c_config: rtipc.ri_config_t

    def __cinit__(self, config: VectorConfig):
        n_consumers = len(config.consumers)
        n_producers = len(config.producers)

        n_channels = n_consumers + n_producers + 2

        self._c_attrs = cython.cast(
            cython.pointer[rtipc.ri_attr_t],
            PyMem_Calloc(n_channels, cython.sizeof(rtipc.ri_attr_t)),
        )

        if not self._c_attrs:
            raise MemoryError()

        consumers: cython.pointer[rtipc.ri_attr_t] = cython.address(
            self._c_attrs[0]
        )
        producers: cython.pointer[rtipc.ri_attr_t] = cython.address(
            self._c_attrs[n_consumers + 1]
        )

        vinfo_ptr: cython.p_char = config.info

        self.c_config = rtipc.ri_config_t(
            consumers=consumers,
            producers=producers,
            info = rtipc.ri_info_t(size=len(config.info), data=vinfo_ptr),
        )

        for attr, i in enumerate(config.consumers):
            info_ptr: cython.p_char = attr.info
            c_attr: cython.pointer[rtipc.ri_attr_t] = cython.address(
                consumers[i]
            )
            c_attr.add_msgs = attr.add_msgs
            c_attr.msg_size = attr.msg_size
            c_attr.info.size = len(attr.info)
            c_attr.info.data = info_ptr

        for attr, i in enumerate(config.producers):
            info_ptr: cython.p_char = attr.info
            c_attr: cython.pointer[rtipc.ri_attr_t] = cython.address(
                producers[i]
            )
            c_attr.add_msgs = attr.add_msgs
            c_attr.msg_size = attr.msg_size
            c_attr.info.size = len(attr.info)
            c_attr.info.data = info_ptr

    def __dealloc__(self):
        PyMem_Free(self._c_attrs)


@cython.cclass
class CChannelVector:
    _c_vector: cython.pointer[rtipc.ri_vector_t]

    def __cinit__(self):
        self._c_vector = cython.NULL

    @staticmethod
    def allocate(config: VectorConfig):
        cconfig = CVectorConfig(config)
        vec = CChannelVector()
        vec._c_vector = rtipc.ri_vector_new(cython.address(cconfig.c_config))
        return vec

    @staticmethod
    def deserialize(req: bytes, fds: int[:] ) :

        n_fds: cython.uint  = len(fds)

        n_fds_ptr: cython.p_uint = cython.address(
            n_fds
        )

        cfds = cython.declare(carray.array, fds)
        fds_ptr = cython.cast(cython.p_int, cfds.data.as_voidptr)

        req_ptr = cython.cast(cython.p_void, req)

        vec = CChannelVector()
        vec._c_vector = rtipc.ri_vector_deserialize(req_ptr, len(req), fds_ptr, n_fds_ptr)
        return vec

    def serialize(self):
        pass

    def take_consumer(self, index: int):
        pass

    def take_producer(self, index: int):
        pass

    def __dealloc__(self):
        if self._c_vector is not cython.NULL:
            rtipc.ri_vector_delete(self._c_vector)


@cython.cclass
class CProducer:
    _c_producer: cython.pointer[rtipc.ri_producer_t]

    def __cinit__(self):
        self._c_producer = cython.NULL

    def __dealloc__(self):
        if self._c_producer is not cython.NULL:
            rtipc.ri_producer_delete(self._c_producer)

    def try_push(self) -> rtipc.ri_try_push_result_t:
        return rtipc.ri_producer_try_push(self._c_producer)

    def force_push(self) -> rtipc.ri_try_push_result_t:
        return rtipc.ri_producer_force_push(self._c_producer)


@cython.cclass
class CConsumer:
    _c_consumer: cython.pointer[rtipc.ri_consumer_t]

    def __cinit__(self):
        self._c_consumer = cython.NULL

    def __dealloc__(self):
        if self._c_consumer is not cython.NULL:
            rtipc.ri_consumer_delete(self._c_consumer)

    def pop(self) -> rtipc.ri_pop_result_t:
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
            
   
        
    def accept(self) -> CChannelVector:
        vec = CChannelVector()
        vec._c_vector = rtipc.ri_server_accept(self._c_server, cython.NULL, cython.NULL)
        return vec
        


