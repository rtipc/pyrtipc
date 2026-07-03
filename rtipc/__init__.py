from typing import TypeVar, Generic
from ctypes import Structure as CStructure, Union as CUnion

from pathlib import Path

from .config import MqAttr, VectorConfig


from .rtipc_wrapper import CChannelVector, CProducer, CConsumer, CServer

T = TypeVar("T", CStructure, CUnion)


class Producer(Generic[T]):
    def __init__(self, c_producer: CProducer):
        self.c_producer = c_producer


class Consumer(Generic[T]):
    def __init__(self, c_consumer: CConsumer):
        self.c_consumer = c_consumer

class ChannelVector(object):
    def __init__(self, c_vec: CChannelVector):
        self.c_vec = c_vec
        
    @classmethod
    def fromconfig(cls, config: VectorConfig) -> ChannelVector:
        c_vec = CChannelVector.fromconfig(config);
        return cls(c_vec)
    @classmethod
    def deserialize(cls, config: VectorConfig):
        pass
    
    def serialize(self):
        return self.c_vec.serialize()
    
    def take_producer[T](self, index: int) -> Producer[T]:
        pass

    def take_consumer[T](self, index: int) -> Consumer[T]:
        pass

class Server(object):
    def __init__(self, path: Path):
        self.c_server = CChannelVector(path)
        
    def accept(self) -> ChannelVector:
        c_vec = self.c_server.accept();
        return ChannelVector(c_vec)
