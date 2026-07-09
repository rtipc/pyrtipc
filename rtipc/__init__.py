from typing import TypeVar, Generic
from ctypes import Structure as CStructure, Union as CUnion, sizeof as csizeof

from pathlib import Path

from .attr import ChannelAttr, GroupAttr

from .rtipc_wrapper import CChannelGroup, CProducer, CConsumer, CServer

T = TypeVar("T", CStructure, CUnion)


class Producer(Generic[T]):
    def __init__(self, c_producer: CProducer, cls: type[T]):
        self.c_producer = c_producer
        self.cls = cls
        
    def current_msg(self) -> T:
        msg: bytearray = self.c_producer.current_msg()
        if msg is None:
            return None
        return self.cls.from_buffer(msg)
        
class Consumer(Generic[T]):
    def __init__(self, c_consumer: CConsumer, cls: type[T],):
        self.c_consumer = c_consumer
        self.cls = cls
        
    def current_msg(self) -> T:
        msg: bytearray = self.c_consumer.current_msg()
        if msg is None:
            return None
        return self.cls.from_buffer(msg)

class ChannelGroup(object):
    def __init__(self, c_grp: CChannelGroup):
        self.c_grp = c_grp
        
    @classmethod
    def from_attr(cls, attr: GroupAttr) -> ChannelGroup:
        c_grp = CChannelGroup.from_attr(attr);
        return cls(c_grp)
        
    @classmethod
    def deserialize(cls, req: bytes, fds: int[:]) -> ChannelGroup:
        c_grp = CChannelGroup.deserialize(req, fds);
        return cls(c_grp)
    
    def get_attr(self) -> GroupAttr:
        return self.c_grp.get_attr();
    
    def serialize(self):
        return self.c_grp.serialize()
    
    def acquire_producer(self, cls: type[T], index: int) -> Producer[T]:
        c_producer = self.c_grp.acquire_producer(index)
        if csizeof(cls) > c_producer.msg_size():
            raise RuntimeError()
        return Producer(c_producer, cls)

    def acquire_consumer(self, cls: type[T], index: int) -> Consumer[T]:
        c_consumer = self.c_grp.acquire_consumer(index)
        if csizeof(cls) > c_consumer.msg_size():
            raise RuntimeError()
        return Consumer(c_consumer, cls)

class Server(object):
    def __init__(self, path: Path):
        self.c_server = CChannelVector(path)
        
    def accept(self) -> ChannelGroup:
        c_grp = self.c_server.accept();
        return ChannelGroup(c_grp)
