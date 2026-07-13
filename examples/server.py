import asyncio 
from asyncio import Future 
from dataclasses import dataclass
from enum import IntEnum

from pyrtipc import ChannelAttr, GroupAttr, Server, TryPushResult, ForcePushResult, PopResult


from ctypes import sizeof

from messages import MsgCommand, MsgResponse, MsgEvent, CommandId


producers = [ChannelAttr(0, sizeof(MsgCommand), True, b'rpc command')]
consumers = [ChannelAttr(0, sizeof(MsgResponse), True, b'rpc response'), ChannelAttr(10, sizeof(MsgEvent), True, b'rpc event')]
    
attr = GroupAttr(consumers, producers, b'rpc group')


class CmdServer(object):
    def __init__(self, socket, loop):
        self.loop = loop
        self.server = Server(socket)
        self.fut = self.loop.create_future()

    def listen(self):
        socket = self.server.get_socket()
        self.loop.add_reader(socket, self.connection_handler)


    async def await_stop(self):
        await self.fut

    def connection_handler(self):
        grp = self.server.accept()
        self.chnl_cmd = grp.acquire_consumer(MsgCommand, 0)
        self.chnl_rsp = grp.acquire_producer(MsgResponse, 0)
        self.chnl_evt = grp.acquire_producer(MsgEvent, 1)
        
        event_cmd = self.chnl_cmd.get_eventfd()
        self.loop.add_reader(event_cmd, self.command_handler)

    def command_handler(self):
        r = self.chnl_cmd.pop()
        
        if r != PopResult.SUCCESS and r != PopResult.DICARDED:
            print("command pop failed=" +str(r))
            return
        
        cmd = self.chnl_cmd.current_msg()
        print("command: received id=" + str(cmd.id))
        
        rsp = self.chnl_rsp.current_msg()
        rsp.id = cmd.id
        rsp.result = 0
        rsp.data = 0
        stop = False
        match cmd.id:
            case CommandId.UNKNOWN:
                stop = True
            case CommandId.HELLO:
                pass
            case CommandId.STOP:
                stop = True
            case CommandId.SENDEVENT:
                pass
            case CommandId.DIV:
                pass
                
        self.chnl_rsp.force_push()
        
        if stop:
            self.fut.set_result(0)
            


async def main():
    loop = asyncio.get_event_loop()
    server = CmdServer("rtipc.sock", loop)
    server.listen()
    await server.await_stop()

    
if __name__ == "__main__":
    asyncio.run(main())
