from typing import TypeVar, Generic
from ctypes import Structure as CStructure, Union as CUnion

from pathlib import Path

from .attr import ChannelAttr, GroupAttr


from .rtipc_wrapper import CChannelGroup, CProducer, CConsumer, CServer

T = TypeVar("T", CStructure, CUnion)


class Producer(Generic[T]):
    def __init__(self, c_producer: CProducer):
        self.c_producer = c_producer


class Consumer(Generic[T]):
    def __init__(self, c_consumer: CConsumer):
        self.c_consumer = c_consumer

class ChannelGroup(object):
    def __init__(self, c_grp: CChannelGroup):
        self.c_grp = c_grp
        
    @classmethod
    def from_attr(cls, attr: GroupAttr) -> ChannelGroup:
        c_grp = ChannelGroup.from_attr(attr);
        return cls(c_grp)
        
    @classmethod
    def deserialize(cls, config: VectorConfig):
        pass
    
    def serialize(self):
        return self.c_grp.serialize()
    
    def take_producer[T](self, index: int) -> Producer[T]:
        pass

    def take_consumer[T](self, index: int) -> Consumer[T]:
        pass

class Server(object):
    def __init__(self, path: Path):
        self.c_server = CChannelVector(path)
        
    def accept(self) -> ChannelGroup:
        c_grp = self.c_server.accept();
        return ChannelGroup(c_grp)
