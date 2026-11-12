# TuxBurger

O TuxBurger é um sistema distribuído cliente-servidor voltado para o gerenciamento de pedidos e controle de estoque de uma lanchonete temática. A aplicação conta com uma interface em modo texto (TUI) interativa e comunicação assíncrona em tempo real via WebSockets.

Para uma visão aprofundada das especificações, regras de negócio e histórias de usuário, recomenda-se a leitura do documento completo em [docs/requisitos.pdf](docs/requisitos.pdf).

## Visão Geral

- **Interface em Modo Texto (TUI):** Desenvolvida em Python com `prompt_toolkit` e `asyncio`, estruturada em tela cheia com painel de mensagens e arte temática do mascote Tux gerada via `cowsay` e `figlet`.
- **Arquitetura Assíncrona e Desacoplada:** O cliente segue princípios de responsabilidade única e segregação de interfaces (SOLID), operando sem chamadas bloqueantes no loop de eventos.
- **Comunicação em Tempo Real:** Conexão WebSocket na porta 3030 (`ws://localhost:3030`) utilizando mensagens estruturadas em JSON (UTF-8).
- **Servidor e Regras de Negócio:** Servidor assíncrono baseado no padrão Subscriber (`OrderSub`) que realiza controle atômico de inventário com `asyncio.Lock`, alertas de estoque crítico (limiar <= 5 unidades) e geração de comandas sequenciais.

## Funcionalidades Principais

- **Consulta de Cardápio:** Exibição detalhada de lanches e porções de ingredientes (`/cardapio`).
- **Realização de Pedidos:** Suporte a pedidos diretos por parâmetro (`/pedido <lanche>`) ou interativos guiados por perguntas (`/pedido`), com validação de itens e opção de cancelamento.
- **Simulação de Preparo:** Contagem assíncrona de 20 segundos para o tempo de cozinha, prevenindo requisições concorrentes no mesmo terminal.
- **Controle Automático de Estoque:** Validação prévia de disponibilidade de matéria-prima e débito automático persistido em arquivo JSON no servidor.
- **Comandos Utilitários:** Limpeza do histórico de mensagens (`/clear`) e listagem dinâmica de instruções (`/help`).

## Requisitos do Ambiente

- Sistema operacional Linux
- Python 3.10 ou superior
- Utilitários de terminal: `cowsay` e `figlet`
- Terminal com suporte a fontes monoespaçadas (Nerd Fonts recomendada)

## Execução

1. Iniciar o servidor:
   ```bash
   python src/server/main.py
   ```

2. Em outro terminal, iniciar o cliente:
   ```bash
   python src/client/main.py
   ```

## Documentação

A especificação formal completa dos requisitos funcionais, requisitos não-funcionais e histórias de usuário encontra-se detalhada no arquivo [docs/requisitos.pdf](docs/requisitos.pdf) (código-fonte em [docs/requisitos.tex](docs/requisitos.tex)).
