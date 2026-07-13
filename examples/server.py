import asyncio 
from asyncio import Future 
from dataclasses import dataclass
from enum import IntEnum
from ctypes import sizeof

from pyrtipc import ChannelAttr, GroupAttr, ChannelGroup, Server, TryPushResult, ForcePushResult, PopResult

from messages import MsgCommand, MsgResponse, MsgEvent, CommandId


producers = [ChannelAttr(0, sizeof(MsgCommand), True, b'rpc command')]
consumers = [ChannelAttr(0, sizeof(MsgResponse), True, b'rpc response'), ChannelAttr(10, sizeof(MsgEvent), True, b'rpc event')]
    
attr = GroupAttr(consumers, producers, b'rpc group')


class Rpc(object):
    def __init__(self, grp: ChannelGroup, loop):
        self.loop = loop
        self.grp = grp
        self.chnl_cmd = grp.acquire_consumer(MsgCommand, 0)
        self.chnl_rsp = grp.acquire_producer(MsgResponse, 0)
        self.chnl_evt = grp.acquire_producer(MsgEvent, 1)
        
        event_cmd = self.chnl_cmd.get_eventfd()
        self.loop.add_reader(event_cmd, self.command_handler)
        self.future = self.loop.create_future()

    def get_future(self):
        return self.future

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
                rsp.result, rsp.data = self.send_events(cmd.args[0], cmd.args[1], cmd.args[2] != 0)
            case CommandId.DIV:
                try:
                    rsp.data = Rpc.divide(cmd.args[0], cmd.args[1])
                except ZeroDivisionError:
                    rsp.result = -1
                
        self.chnl_rsp.force_push()

        if stop:
            self.future.set_result(0)

    @staticmethod
    def divide(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError()
        return int(float(a) / float(b))

    def send_events(self, id: int, num: int, force: bool) -> int:
        for i in range(0, num):
            msg = self.chnl_evt.current_msg()
            msg.id = id
            msg.nr = i
            if force:
                self.chnl_evt.force_push()
            else:
                r = self.chnl_evt.try_push()
                if r < 0:
                    return r, i;
        return 0, num


class CmdServer(object):
    def __init__(self, socket, loop):
        self.loop = loop
        self.server = Server(socket)
        self.rpc_futures = []
        self.listen_future = self.loop.create_future()

    async def listen(self):
        socket = self.server.get_socket()
        self.loop.add_reader(socket, self.connection_handler)
        await self.listen_future

    def connection_handler(self):
        grp = self.server.accept()
        rpc = Rpc(grp, self.loop)
        self.rpc_futures.append(rpc.get_future())
        self.listen_future.set_result(1)

    async def await_stop(self):
        await asyncio.wait(self.rpc_futures, return_when=asyncio.ALL_COMPLETED)


async def main():
    loop = asyncio.get_event_loop()
    server = CmdServer("rtipc.sock", loop)
    await server.listen()
    await server.await_stop()


if __name__ == "__main__":
    asyncio.run(main())
