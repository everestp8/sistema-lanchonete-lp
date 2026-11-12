import subprocess

class TuxRenderer:
    @staticmethod
    def render(message: str) -> str:
        cmd1 = subprocess.run(['figlet', 'TuxBurger'], stdout=subprocess.PIPE, text=True)
        cmd2 = subprocess.run(['cowsay', '-f', 'tux', message], stdout=subprocess.PIPE, text=True)
        return '\n' * 3 + (cmd1.stdout or '') + (cmd2.stdout or '')

