# ATT — Atualizador Automático para Windows

Este é um utilitário leve e moderno desenvolvido em **Python** utilizando a biblioteca **Tkinter**. O objetivo principal do script é automatizar a atualização de todos os softwares instalados no Windows através do gerenciador de pacotes nativo do sistema (`winget`), exibindo notificações flutuantes personalizadas e animadas em segundo plano.

---

## Como Funciona?

O script executa um fluxo automatizado dividido em três etapas principais:

1. **Validação do Ambiente:** O script verifica se o sistema operacional atual é o Windows. Caso contrário, exibe um alerta e interrompe a execução.
2. **Interface Visual (Toast Notifications):** Uma janela customizada sem bordas (`overrideredirect`), sempre no topo (`-topmost`) e com efeito, surge no centro da tela informando o início do processo.
3. **Atualização Silenciosa:** Utilizando o módulo `subprocess`, o script dispara o comando `winget upgrade --all --silent` ocultando qualquer janela de terminal. Todos os programas compatíveis são atualizados simultaneamente sem intervenção do utilizador.


## Tecnologias Utilizadas

* **Python 3.x** (Linguagem base)
* **Tkinter** (Construção da interface gráfica nativa)
* **Subprocess** (Execução de comandos do sistema em segundo plano)
* **Platform** (Deteção do Sistema Operacional)
* **Winget** (Gerenciador de Pacotes do Windows)

---

## 📋 Pré-requisitos

Para que o script funcione corretamente, certifique-se de cumprir os seguintes requisitos:
* **Sistema Operacional:** Windows 10 (versão 1709 ou posterior) ou Windows 11.
* **Gerenciador de Pacotes:** O `winget` deve estar instalado e configurado no PATH do sistema (geralmente já vem por padrão no "App Installer" da Microsoft Store).
* **Python instalado** (caso pretenda executar o ficheiro `.py` diretamente).

---
