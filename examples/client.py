import asyncio
from asyncio import Future
from ctypes import sizeof
from dataclasses import dataclass

import rpc
from messages import CommandId

from rpc import (
    client_group_rpc,
    CommandArgs,
    SendEventArgs,
    DivArgs,
    MsgCommand,
    MsgEvent,
    MsgResponse,
)

from pyrtipc import ChannelAttributes, GroupAttributes, PopResult, client_connect


command_list = [
    MsgCommand(id=CommandId.HELLO),
    MsgCommand(
        id=CommandId.SENDEVENT,
        args=CommandArgs(send=SendEventArgs(id=11, force=False, num=20)),
    ),
    MsgCommand(
        id=CommandId.SENDEVENT,
        args=CommandArgs(send=SendEventArgs(id=12, force=True, num=20)),
    ),
    MsgCommand(
        id=CommandId.DIV, args=CommandArgs(div=DivArgs(divisor=100.0, divident=7.0))
    ),
    MsgCommand(
        id=CommandId.DIV, args=CommandArgs(div=DivArgs(divisor=100.0, divident=0.0))
    ),
    MsgCommand(id=CommandId.STOP),
]


class Client:
    def __init__(self, socket, loop):
        self.loop = loop
        group = client_connect(socket, client_group_rpc)

        self.chnl_cmd = rpc.client_rpc_acquire_command(group)
        self.chnl_rsp = rpc.client_rpc_acquire_response(group)
        self.chnl_evt = rpc.client_rpc_acquire_event(group)

        event_rsp = self.chnl_rsp.get_eventfd()
        event_evt = self.chnl_evt.get_eventfd()
        self.loop.add_reader(event_rsp, self.response_handler)
        self.loop.add_reader(event_evt, self.event_handler)

    def send_command(self, cmd: MsgCommand):
        msg = self.chnl_cmd.current_msg()
        # msg = cmd doesn't work, because it just replaces the reference
        msg.id = cmd.id
        msg.args = cmd.args

        self.chnl_cmd.force_push()

    def start(self) -> Future:
        self.command = iter(command_list)
        self.send_command(next(self.command))
        self.fut = self.loop.create_future()
        return self.fut

    def response_handler(self):
        r = self.chnl_rsp.pop()

        if r != PopResult.SUCCESS and r != PopResult.DISCARDED:
            print("response pop failed=" + str(r))
            return

        msg = self.chnl_rsp.current_msg()
        print(
            "respones: received id="
            + str(msg.id)
            + " result="
            + str(msg.result)
            + " data="
            + str(msg.data)
        )
        try:
            cmd = next(self.command)
        except StopIteration:
            self.fut.set_result(0)
            return
        self.send_command(cmd)

    def event_handler(self):
        r = self.chnl_evt.pop()
        if r != PopResult.SUCCESS and r != PopResult.DISCARDED:
            print("event pop failed=" + str(r))
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
