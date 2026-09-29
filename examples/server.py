import asyncio
from ctypes import sizeof

from messages import CommandId
import rpc
from rpc import MsgCommand, MsgEvent, MsgResponse, server_group_rpc

from pyrtipc import (
    ChannelAttributes,
    ChannelGroup,
    GroupAttributes,
    PopResult,
    Server,
)


class Rpc:
    def __init__(self, group: ChannelGroup, loop):
        self.loop = loop
        self.chnl_cmd = rpc.server_rpc_acquire_command(group)
        self.chnl_rsp = rpc.server_rpc_acquire_response(group)
        self.chnl_evt = rpc.server_rpc_acquire_event(group)

        event_cmd = self.chnl_cmd.get_eventfd()
        self.loop.add_reader(event_cmd, self.command_handler)
        self.future = self.loop.create_future()

    def get_future(self):
        return self.future

    def command_handler(self):
        r = self.chnl_cmd.pop()

        if r != PopResult.SUCCESS and r != PopResult.DISCARDED:
            print("command pop failed=" + str(r))
            return

        cmd = self.chnl_cmd.current_msg()
        print("command: received id=" + str(cmd.id))

        rsp = self.chnl_rsp.current_msg()
        rsp.id = cmd.id
        rsp.result = 0
        stop = False
        match cmd.id:
            case CommandId.UNKNOWN:
                stop = True
            case CommandId.HELLO:
                pass
            case CommandId.STOP:
                stop = True
            case CommandId.SENDEVENT:
                rsp.result, _ = self.send_events(
                    cmd.args.send.id, cmd.args.send.num, cmd.args.send.force
                )
            case CommandId.DIV:
                rsp.result, rsp.data.quotient = Rpc.divide(
                    cmd.args.div.divisor, cmd.args.div.divident
                )

        self.chnl_rsp.force_push()

        if stop:
            self.future.set_result(0)

    @staticmethod
    def divide(a: float, b: float) -> Tuple[int, float]:
        if b == 0:
            return -1, 0.0
        return 0, (float(a) / float(b))

    def send_events(self, id: int, num: int, force: bool) -> Tuple[int, int]:
        for i in range(num):
            msg = self.chnl_evt.current_msg()
            msg.id = id
            msg.nr = i
            if force:
                self.chnl_evt.force_push()
            else:
                r = self.chnl_evt.try_push()
                if r < 0:
                    return r, i
        return 0, num


class CmdServer:
    def __init__(self, socket, loop):
        self.loop = loop
        self.server = Server(socket)
        self.rpc_futures = []
        self.listen_future = self.loop.create_future()

    async def listen(self):
        socket = self.server.get_socket()
        self.loop.add_reader(socket, self.connection_handler)
        await self.listen_future

    def filter(self, attr: GroupAttributes) -> bool:
        return attr == server_group_rpc

    def connection_handler(self):
        grp = self.server.accept(self.filter)
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
