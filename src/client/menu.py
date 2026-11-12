import asyncio
import inspect
from typing import Callable

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

from state import MessagesState
from commands import Commandable
from renderer import TuxRenderer

class Menu:
    def __init__(
        self,
        messages: MessagesState,
        mascot_state: MessagesState,
        commandable: Commandable | None = None,
        on_exit: Callable | None = None
    ):
        self.input_buffer = Buffer()
        self.kb = KeyBindings()
        self.messages = messages
        self.mascot_state = mascot_state
        self.commands: dict[str, Callable] = {}
        self.pending_input: asyncio.Future | None = None
        self.on_exit = on_exit

        if commandable:
            self.set_commandable(commandable)

        self.messages.add_callback(self._on_message_added)
        self.mascot_state.add_callback(self._on_message_added)

        self._setup_key_bindings()
        self._setup_layout()

        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            full_screen=True
        )

    def set_commandable(self, commandable: Commandable):
        self.commands = commandable.get_commands()

    def _setup_layout(self):
        self.layout = Layout(
            HSplit([
                VSplit([
                    Window(
                        content=FormattedTextControl(self._get_messages),
                        ignore_content_width=True,
                        wrap_lines=False,
                    ),
                    Window(
                        content=FormattedTextControl(
                            lambda: TuxRenderer.render(self.mascot_state.get_last('Bem vindo!'))
                        ),
                        width=60,
                        dont_extend_width=True,
                        wrap_lines=False,
                        align=WindowAlign.CENTER
                    )
                ]),
                Window(height=1, char="-", style="class:line"),
                Window(content=BufferControl(buffer=self.input_buffer), height=1)
            ])
        )

    def _get_messages(self) -> str:
        return '\n'.join(self.messages.get_list())

    async def ask(self, question: str) -> str:
        await self.messages.append(question)
        loop = asyncio.get_running_loop()
        self.pending_input = loop.create_future()
        try:
            return await self.pending_input
        finally:
            self.pending_input = None

    def _setup_key_bindings(self):
        @self.kb.add('c-c')
        async def _(event):
            if self.on_exit:
                res = self.on_exit()
                if inspect.isawaitable(res):
                    await res
            event.app.exit()

        @self.kb.add('enter')
        async def _(event):
            await self._enter_input(event)

    async def _enter_input(self, event):
        text = self.input_buffer.text.strip()
        self.input_buffer.reset()

        if not text:
            return

        if text == '/exit':
            if self.pending_input and not self.pending_input.done():
                self.pending_input.cancel()
            if self.on_exit:
                res = self.on_exit()
                if inspect.isawaitable(res):
                    await res
            event.app.exit()
            return

        if self.pending_input and not self.pending_input.done():
            await self.messages.append(f"> {text}")
            self.pending_input.set_result(text)
            return

        parts = text.split()
        command = parts[0]
        params = parts[1:]

        if command in self.commands:
            func = self.commands[command]
            res = func(params)
            if inspect.isawaitable(res):
                await res
        else:
            if command.startswith('/'):
                await self.messages.append(
                    f"[AVISO] Comando '{command}' desconhecido. Digite /help para ver os comandos."
                )
            else:
                await self.messages.append(text)

    def _on_message_added(self) -> None:
        self.app.invalidate()

    async def run(self):
        await self.app.run_async()
