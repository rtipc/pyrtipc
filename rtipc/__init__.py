from typing import TypeVar, Generic
from ctypes import Structure as CStructure, Union as CUnion

from .config import MqAttr, VectorConfig

from .rtipc_wrapper import *

T = TypeVar("T", CStructure, CUnion)


class Producer(Generic[T]):
    def __init__(self, c_producer: CProducer):
        self.c_producer = c_producer


class Consumer(Generic[T]):
    def __init__(self, c_consumer: CConsumer):
        self.c_consumer = c_consumer

class ChannelVector(object):
    def __init__(self, config: VectorConfig):
        self.vec = CChannelVector(config)

    def take_producer[T](self, index: int) -> Producer[T]:
        pass

    def take_consumer[T](self, index: int) -> Consumer[T]:
        pass

