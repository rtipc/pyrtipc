from dataclasses import dataclass
from typing import TypeVar, Generic, List

import cython
from cython.cimports.cpython.mem import PyMem_Malloc, PyMem_Calloc, PyMem_Free
from cython.cimports import crtipc

from cython.cimports.libc.string import memcpy


@dataclass
class ChannelConfig:
    add_msgs: int
    msg_size: int
    info: bytes

@dataclass
class VectorConfig:
    consumers: list[ChannelConfig]
    producers: list[ChannelConfig]
    info: bytes

@cython.cclass
class CInfo:
    data: cython.p_char
    size: cython.size_t
    
    def __cinit__(self, info: bytes):
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
    _c_channels: cython.pointer[crtipc.ri_channel_t]
    c_config: crtipc.ri_config_t
    
    def __cinit__(self, config: VectorConfig):
        n_consumers = len(config.consumers)
        n_producers = len(config.producers)
        
        n_channels = n_consumers + n_producers + 2
        
        self._c_channels = cython.cast(cython.pointer[crtipc.ri_channel_t], PyMem_Calloc(n_channels, cython.sizeof(crtipc.ri_channel_t)))
        
        if not self._c_channels:
            raise MemoryError()
            
        consumers: cython.pointer[crtipc.ri_channel_t] = cython.address(self._c_channels[0])
        producers: cython.pointer[crtipc.ri_channel_t] = cython.address(self._c_channels[n_consumers + 1])
        
        vinfo_ptr: cython.p_char = config.info
        
        self.c_config = crtipc.ri_config_t (
            consumers = consumers,
            producers = producers,
            info = crtipc.ri_info_t(size = len(config.info), data = vinfo_ptr))
            
        for channel, i in enumerate(config.consumers):
            info_ptr: cython.p_char = channel.info
            c_channel: cython.pointer[crtipc.ri_channel_t] = cython.address(consumers[i])
            c_channel.add_msgs = channel.add_msgs
            c_channel.msg_size = channel.msg_size
            c_channel.info.size = len(channel.info)
            c_channel.info.data = info_ptr
        
        for channel, i in enumerate(config.producers):
            info_ptr: cython.p_char = channel.info
            c_channel: cython.pointer[crtipc.ri_channel_t] = cython.address(producers[i])
            c_channel.add_msgs = channel.add_msgs
            c_channel.msg_size = channel.msg_size
            c_channel.info.size = len(channel.info)
            c_channel.info.data = info_ptr
            
    def __dealloc__(self):
        PyMem_Free(self._c_channels)
    

    
@cython.cclass
class CChannelVector:
    _c_vector: cython.pointer[crtipc.ri_vector_t]
        
    def __init__(self, config: VectorConfig):
        cconfig = CVectorConfig(config)
        self._c_vector = crtipc.ri_vector_new(cython.address(cconfig.c_config))
        if not self._c_vector:
            raise MemoryError()

    def __dealloc__(self):
        if self._c_vector is not cython.NULL:
            crtipc.ri_vector_delete(self._c_vector)
            

@cython.cclass
class CProducer:
    _c_producer: cython.pointer[crtipc.ri_producer_t]

    def __cinit__(self):
        self._c_producer = cython.NULL

    def __dealloc__(self):
        if self._c_producer is not cython.NULL:
            crtipc.ri_producer_delete(self._c_producer)

    def try_push(self) -> crtipc.ri_try_push_result_t:
        return crtipc.ri_producer_try_push(self._c_producer)

    def force_push(self) -> crtipc.ri_try_push_result_t:
        return crtipc.ri_producer_force_push(self._c_producer)

@cython.cclass
class CConsumer:
    _c_consumer: cython.pointer[crtipc.ri_consumer_t]

    def __cinit__(self):
        self._c_consumer = cython.NULL

    def __dealloc__(self):
        if self._c_consumer is not cython.NULL:
            crtipc.ri_consumer_delete(self._c_consumer)
