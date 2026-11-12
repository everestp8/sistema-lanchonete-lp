import inspect
from typing import Callable

class MessagesState:
    messages: list[str]
    callback_list: list[Callable]

    def __init__(self):
        self.messages = []
        self.callback_list = []

    def get_list(self) -> list[str]:
        return self.messages

    def get_last(self, default: str = "") -> str:
        return self.messages[-1] if self.messages else default

    async def _notify(self):
        for f in self.callback_list:
            res = f()
            if inspect.isawaitable(res):
                await res

    async def append(self, msg: str):
        self.messages.append(msg)
        await self._notify()

    async def extend(self, msgs: list[str]):
        self.messages.extend(msgs)
        await self._notify()

    async def set(self, msg: str):
        self.messages = [msg]
        await self._notify()

    async def clear(self):
        self.messages.clear()
        await self._notify()

    def add_callback(self, cb: Callable):
        self.callback_list.append(cb)


