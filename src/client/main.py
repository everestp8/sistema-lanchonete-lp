import asyncio
import websockets

from client import Client
from commands import OrderCommandHandler
from menu import Menu
from state import MessagesState 

async def main():
    uri = 'ws://localhost:3030'

    try:
        print('Conectando ao servidor...')
        async with websockets.connect(uri) as ws:
            print('Conectado!')

            messages = MessagesState()
            mascot_state = MessagesState()

            client = Client(ws, messages)

            menu = Menu(messages, mascot_state, on_exit=client.close)

            commands_handler = OrderCommandHandler(
                messages=messages,
                mascot=mascot_state,
                client=client,
                ask_user=menu.ask
            )
            menu.set_commandable(commands_handler)

            try:
                await asyncio.gather(client.receive(), menu.run())
            finally:
                await client.close()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f'Erro: {e}')

if __name__ == '__main__':
    asyncio.run(main())
