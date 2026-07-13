import asyncio 
from asyncio import Future 
from dataclasses import dataclass
from enum import IntEnum

from pyrtipc import ChannelAttr, GroupAttr, client_connect, TryPushResult, ForcePushResult, PopResult


from ctypes import sizeof

from messages import MsgCommand, MsgResponse, MsgEvent, CommandId


producers = [ChannelAttr(0, sizeof(MsgCommand), True, b'rpc command')]
consumers = [ChannelAttr(0, sizeof(MsgResponse), True, b'rpc response'), ChannelAttr(10, sizeof(MsgEvent), True, b'rpc event')]
    
attr = GroupAttr(consumers, producers, b'rpc group')

     
    
@dataclass
class Command:
    id: CommandId
    args: list[int]

command_list = [
    Command(CommandId.HELLO, [1, 2, 3]),
    Command(CommandId.SENDEVENT, [11, 20, 0]),
    Command(CommandId.SENDEVENT, [12, 20, 1]),
    Command(CommandId.DIV, [100, 7, 0]),
    Command(CommandId.DIV, [100, 0, 0]),
    Command(CommandId.STOP, [0, 0, 0]),
]


class Client(object):
    def __init__(self, socket, loop):
        self.loop = loop
        grp = client_connect(socket, attr)
        
        self.chnl_cmd = grp.acquire_producer(MsgCommand, 0)
        self.chnl_rsp = grp.acquire_consumer(MsgResponse, 0)
        self.chnl_evt = grp.acquire_consumer(MsgEvent, 1)
        
        event_rsp = self.chnl_rsp.get_eventfd()
        event_evt = self.chnl_evt.get_eventfd()
        self.loop.add_reader(event_rsp, self.response_handler)
        self.loop.add_reader(event_evt, self.event_handler)
        
    def send_command(self, cmd: Command):
        if cmd is None:
            return
        msg = self.chnl_cmd.current_msg()
        msg.id = cmd.id
        
        for i, arg in enumerate(cmd.args):
             msg.args[i] = arg
             
        self.chnl_cmd.force_push()
    
    def start(self) -> Future:
        self.command = iter(command_list)
        self.send_command(next(self.command))
        self.fut = self.loop.create_future()
        return self.fut
    
    def response_handler(self):
        r = self.chnl_rsp.pop()
        
        if r != PopResult.SUCCESS and r != PopResult.DICARDED:
            print("response pop failed=" +str(r))
            return
        
        msg = self.chnl_rsp.current_msg()
        print("respones: received id=" + str(msg.id) + " result=" + str(msg.result) + " data=" + str(msg.data))
        try:
            cmd = next(self.command)
        except StopIteration:
            self.fut.set_result(0)
            return
        self.send_command(cmd)
        
    def event_handler(self):
        r = self.chnl_evt.pop()
        if r != PopResult.SUCCESS and r != PopResult.DICARDED:
            print("event pop failed=" +str(r))
            return
        msg = self.chnl_evt.current_msg()
        print("event: received id=" + str(msg.id) + " nr=" + str(msg.nr))

async def main():
    loop = asyncio.get_event_loop()
    client = Client("rtipc.sock", loop)
    fut = client.start()
    await fut

    
if __name__ == "__main__":
    asyncio.run(main())
