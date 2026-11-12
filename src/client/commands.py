import asyncio
import json
import os
from typing import Callable, Protocol, Awaitable

from state import MessagesState

class Commandable(Protocol):
    def get_commands(self) -> dict[str, Callable[[list[str]], Awaitable[None]]]:
        ...

    def get_help(self) -> dict[str, str]:
        ...

class OrderCommandHandler:
    def __init__(
        self,
        messages: MessagesState,
        mascot: MessagesState,
        client,
        ask_user: Callable[[str], Awaitable[str]]
    ):
        self.messages = messages
        self.mascot = mascot
        self.client = client
        self.ask_user = ask_user
        self.is_cooking: bool = False

    def get_commands(self) -> dict[str, Callable[[list[str]], Awaitable[None]]]:
        return {
            '/cardapio': self.cmd_cardapio,
            '/menu': self.cmd_cardapio,
            '/pedido': self.cmd_pedido,
            '/pedir': self.cmd_pedido,
            '/clear': self.cmd_clear,
            '/limpar': self.cmd_clear,
            '/help': self.cmd_help,
            '/ajuda': self.cmd_help,
        }

    def get_help(self) -> dict[str, str]:
        return {
            '/cardapio': 'Exibe o cardápio e ingredientes',
            '/pedido [nome]': 'Faz um pedido para a cozinha',
            '/clear': 'Limpa o painel de mensagens',
            '/help': 'Exibe os comandos disponíveis',
            '/exit': 'Encerra a aplicação',
        }

    def _load_menu_data(self) -> list[dict]:
        data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def cmd_cardapio(self, params: list[str] | None = None):
        try:
            items = self._load_menu_data()
        except Exception as e:
            await self.messages.append(f"[ERRO] Falha ao ler cardápio: {e}")
            return

        lines = [
            "## CARDÁPIO TUXBURGER ##",
        ]
        for idx, item in enumerate(items, 1):
            lines.append(f" {idx}. {item['name']}")
            lines.append("    Ingredientes:")
            for ingredient, qty in item.get('ingredients', {}).items():
                lines.append(f"      • {ingredient}: {qty}")
            lines.append("")
        lines.append("Dica: Use '/pedido' ou '/pedido <nome>' para pedir!")

        await self.messages.extend(lines)

    async def cmd_clear(self, params: list[str] | None = None):
        await self.messages.clear()

    async def cmd_help(self, params: list[str] | None = None):
        lines = [
            "## COMANDOS DISPONÍVEIS ##",
        ]
        for cmd, desc in self.get_help().items():
            lines.append(f" {cmd:<16} - {desc}")

        await self.messages.extend(lines)

    async def cmd_pedido(self, params: list[str] | None = None):
        if self.is_cooking:
            await self.messages.append("[AVISO] A cozinha já está preparando um lanche! Aguarde finalizar.")
            return

        try:
            items = self._load_menu_data()
        except Exception as e:
            await self.messages.append(f"[ERRO] Falha ao carregar cardápio: {e}")
            return

        item = None
        if params:
            chosen = " ".join(params).strip()
            item = next((i for i in items if i['name'].lower() == chosen.lower()), None)
            if not item:
                valid_names = ", ".join(i['name'] for i in items)
                await self.messages.append(f"[PEDIDO] '{chosen}' não encontrado no cardápio. Opções: {valid_names}")
                return

        while item is None:
            valid_names = ", ".join(i['name'] for i in items)
            answer = await self.ask_user(
                f"[PEDIDO] Qual lanche deseja pedir? ({valid_names}) ou digite 'cancelar':"
            )
            answer = answer.strip()
            if answer.lower() in ('cancelar', '/cancelar', 'sair', 'c'):
                await self.messages.append("[PEDIDO] Operação cancelada pelo usuário.")
                return

            item = next((i for i in items if i['name'].lower() == answer.lower()), None)
            if not item:
                await self.messages.append(f"[PEDIDO] Lanche '{answer}' não consta no cardápio. Tente novamente.")

        confirm = await self.ask_user(
            f"[PEDIDO] Confirma pedido de '{item['name']}'? (s/n):"
        )
        if confirm.strip().lower() not in ('s', 'sim', 'y', 'yes'):
            await self.messages.append(f"[PEDIDO] Pedido de '{item['name']}' não foi confirmado.")
            return

        self.is_cooking = True
        try:
            await self.messages.append(f"[PEDIDO] Enviando '{item['name']}' para o servidor...")
            payload = {
                "id": "order",
                "name": item["name"],
                "ingredients": item["ingredients"]
            }

            server_reply = ""
            if hasattr(self.client, 'send_order'):
                try:
                    server_reply = await self.client.send_order(payload)
                except asyncio.TimeoutError:
                    await self.messages.append("[ERRO] Tempo limite aguardando confirmação do servidor.")
                    return
            elif hasattr(self.client, 'send_json'):
                await self.client.send_json(payload)

            if "RECUSADO" in server_reply:
                await self.messages.append("[PEDIDO] Operação abortada pela cozinha por falta de estoque.")
                return

            await self.messages.append("[COZINHA] Pedido aprovado! Tempo de preparo: 20s.")

            for remaining in [20, 15, 10, 5]:
                await asyncio.sleep(5)

            await self.messages.append(f"[COZINHA] Pedido de '{item['name']}' finalizado! Pode retirar no balcão.")
        finally:
            self.is_cooking = False
