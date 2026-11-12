import asyncio
import json
import os
import sys
import websockets

from typing import Protocol

sys.path.append(os.path.dirname(__file__))
from repository import IngredientStorage

class Subscriber(Protocol):
    def get_id(self) -> str:
        ...
    async def update(self, ws: websockets.ServerConnection, data: dict):
        ...

class CustomerSub:
    def get_id(self) -> str:
        return 'customer'
    async def update(self, ws: websockets.ServerConnection, data: dict):
        print(data)
        await ws.send(f'Olá, {data["text"]}!')

class OrderSub:
    def __init__(self, storage: IngredientStorage | None = None):
        if storage is None:
            data_file = os.path.join(os.path.dirname(__file__), 'data.json')
            storage = IngredientStorage(data_file)
        self.storage = storage
        self.order_counter: int = 1

    def get_id(self) -> str:
        return 'order'

    async def update(self, ws: websockets.ServerConnection, data: dict):
        sandwich = data.get('name', 'Lanche')
        ingredients = data.get('ingredients', {})
        print(f"[SERVIDOR] Pedido recebido: {sandwich} ({ingredients})")

        success, reason, critical_alerts = await self.storage.check_and_subtract(ingredients)

        if not success:
            print(f"[SERVIDOR] Pedido de '{sandwich}' RECUSADO: {reason}")
            await ws.send(f"[SERVIDOR] Pedido de '{sandwich}' RECUSADO: {reason}")
            return

        comanda = f"#{self.order_counter:03d}"
        self.order_counter += 1

        print(f"[SERVIDOR] Comanda {comanda} ('{sandwich}') confirmada!")
        await ws.send(
            f"[SERVIDOR] Comanda {comanda} ('{sandwich}') confirmada com sucesso! Ingredientes deduzidos do estoque."
        )

        for alert in critical_alerts:
            alert_msg = f"[ALERTA DE ESTOQUE] O ingrediente '{alert}' atingiu nível crítico!"
            print(alert_msg)
            await ws.send(alert_msg)

class Server():
    clients: set = set()
    subscribers: list[Subscriber] = []

    def __init__(self, host: str, port: int) -> None:
        self.__host = host
        self.__port = port

    async def __handler(self, ws: websockets.ServerConnection):
        self.clients.add(ws)
        print('New client connected!')

        await ws.send(f'Bem vindo!')
        try:
            async for message in ws:
                data: dict = {}
                try:
                    data = json.loads(message)
                except:
                    return

                for sub in self.subscribers:
                    if sub.get_id() == data['id']:
                        await sub.update(ws, data)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(ws)
            print(f'Cliente {ws.remote_address} disconectado.')
    
    def add_subscriber(self, sub: Subscriber):
        self.subscribers.append(sub)

    async def init(self):
        async with websockets.serve(self.__handler, self.__host, self.__port):
            print("Servidor WebSocket iniciado em ws://localhost:3030")
            await asyncio.get_running_loop().create_future()

if __name__ == '__main__':
    server = Server('localhost', 3030)
    server.add_subscriber(CustomerSub())
    server.add_subscriber(OrderSub())
    try:
        asyncio.run(server.init())
    except KeyboardInterrupt:
        print('Desligando servidor')
        exit(0)


