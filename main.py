import tkinter as tk
import subprocess
import platform
import sys

def mostrar_mensagem(mensagem, duracao_ms, tipo="info"):
    # Exibe uma janela flutuante moderna com mensagem temporária.
    # tipo: "info" | "erro" | "aviso"
    janela = tk.Tk()
    janela.overrideredirect(True)
    janela.attributes("-topmost", True)
    janela.attributes("-alpha", 0.0)

    # Paleta de cores por tipo
    paleta = {
        "info": {"fundo": "#0C2C11","destaque": "#89FAAB", "texto": "#CDF4D5", "icone": "⟳"},
        "erro": { "fundo": "#0C252C", "destaque": "#F38BA8", "texto": "#CDF4D5", "icone": "✕"},
        "aviso": { "fundo": "#0C252C", "destaque": "#F9E2AF", "texto": "#CDF4D5", "icone": "⚠"},
    }
    cores = paleta.get(tipo, paleta["info"])
    janela.configure(bg=cores["fundo"])

    # Frame com borda colorida
    borda = tk.Frame(janela, bg=cores["destaque"], padx=2, pady=2)
    borda.pack(fill="both", expand=True)

    # Conteúdo principal
    conteudo = tk.Frame(borda, bg=cores["fundo"], padx=28, pady=20)
    conteudo.pack(fill="both", expand=True)

    # Ícone + título
    cabecalho = tk.Frame(conteudo, bg=cores["fundo"])
    cabecalho.pack(fill="x", anchor="w")
    rotulo_icone = tk.Label(
        cabecalho,
        text=cores["icone"],
        font=("Segoe UI", 18),
        bg=cores["fundo"],
        fg=cores["destaque"],
    )
    rotulo_icone.pack(side="left", padx=(0, 8))

    rotulo_titulo = tk.Label(
        cabecalho,
        text="ATT — Atualizador",
        font=("Segoe UI", 10, "bold"),
        bg=cores["fundo"],
        fg=cores["destaque"],
        anchor="w",
    )
    rotulo_titulo.pack(side="left")

    # Separador
    separador = tk.Frame(conteudo, bg=cores["destaque"], height=1)
    separador.pack(fill="x", pady=(10, 14))

    # Mensagem principal
    rotulo_mensagem = tk.Label(
        conteudo,
        text=mensagem,
        font=("Segoe UI", 11),
        bg=cores["fundo"],
        fg=cores["texto"],
        wraplength=380,
        justify="left",
        anchor="w",
    )
    rotulo_mensagem.pack(fill="x", anchor="w")

    # Barra de progresso animada
    frame_progresso = tk.Frame(conteudo, bg="#313244", height=4)
    frame_progresso.pack(fill="x", pady=(18, 0))
    frame_progresso.pack_propagate(False)

    barra_progresso = tk.Frame(frame_progresso, bg=cores["destaque"], height=4)
    barra_progresso.place(x=0, y=0, relwidth=1.0, height=4)

    # Centralizar na tela
    janela.update_idletasks()
    largura = janela.winfo_reqwidth() + 4
    altura = janela.winfo_reqheight() + 4
    posicao_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    posicao_y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{posicao_x}+{posicao_y}")

    # Animações
    passos_opacidade = 20
    intervalo_opacidade = 150

    def animar_entrada(passo=0):
        opacidade = passo / passos_opacidade
        janela.attributes("-alpha", min(opacidade, 1.0))
        if passo < passos_opacidade:
            janela.after(intervalo_opacidade // passos_opacidade, animar_entrada, passo + 1)
        else:
            animar_barra()

    def animar_barra():
        fps = 60
        intervalo = 1000 // fps
        passos_totais = duracao_ms // intervalo

        def atualizar_barra(passo_atual=0):
            if not janela.winfo_exists():
                return
            fracao = 1.0 - (passo_atual / passos_totais)
            barra_progresso.place(x=0, y=0, relwidth=max(fracao, 0.0), height=4)
            if passo_atual < passos_totais:
                janela.after(intervalo, atualizar_barra, passo_atual + 1)
            else:
                animar_saida()

        atualizar_barra()

    def animar_saida(passo=0):
        if not janela.winfo_exists():
            return
        opacidade = 1.0 - (passo / passos_opacidade)
        janela.attributes("-alpha", max(opacidade, 0.0))
        if passo < passos_opacidade:
            janela.after(intervalo_opacidade // passos_opacidade, animar_saida, passo + 1)
        else:
            janela.destroy()

    animar_entrada()
    janela.mainloop()
    
def main() -> None:

    # Validação do sistema operacional
    if platform.system() != "Windows":
        mostrar_mensagem(
            mensagem="Este script só pode ser executado no Windows.",
            duracao_ms=5000,
            tipo="aviso",
        )
        sys.exit(1)
    
    # Execução principal
    try:
        mostrar_mensagem(
            "Verificando atualizações de programas…\nAguarde, isso pode levar alguns instantes.",
            10000,
            tipo="info",
        )
        subprocess.run(
            ["winget", "upgrade", "--all", "--silent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as erro:
        mostrar_mensagem(f"Ocorreu um erro inesperado:\n{erro}", 10000, tipo="erro",)


if __name__ == "__main__":
    main()