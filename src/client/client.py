import asyncio
import json
import websockets

from state import MessagesState

class Client:
    def __init__(self, ws: websockets.ClientConnection, messages: MessagesState) -> None:
        self.ws = ws
        self.messages = messages
        self.pending_order_response: asyncio.Future | None = None
        self._is_closing: bool = False

    async def receive(self):
        try:
            async for message in self.ws:
                msg_str = str(message)
                await self.messages.append(msg_str)
                if self.pending_order_response and not self.pending_order_response.done():
                    if "[SERVIDOR]" in msg_str:
                        self.pending_order_response.set_result(msg_str)

        except websockets.exceptions.ConnectionClosed:
            if not self._is_closing:
                await self.messages.append("\n[AVISO] Conexão com o servidor encerrada.")
            return
        except asyncio.CancelledError:
            return
        except Exception as e:
            if not self._is_closing:
                await self.messages.append(f"\n[ERRO] Erro ao receber mensagem: {e}")
            return

    async def send_order(self, data: dict, timeout: float = 5.0) -> str:
        loop = asyncio.get_running_loop()
        self.pending_order_response = loop.create_future()
        try:
            await self.send_json(data)
            return await asyncio.wait_for(self.pending_order_response, timeout=timeout)
        finally:
            self.pending_order_response = None

    async def send_json(self, data: dict):
        await self.ws.send(json.dumps(data))

    async def close(self):
        self._is_closing = True
        try:
            await self.ws.close()
        except Exception:
            pass
