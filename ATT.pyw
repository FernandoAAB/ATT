import tkinter as tk
import subprocess
import platform

def mostrar_mensagem(mensagem, tempo, tipo="info"):
    """
    Exibe uma janela flutuante moderna com mensagem temporária.
    tipo: "info" | "erro" | "aviso"
    """
    root = tk.Tk()
    root.overrideredirect(True)          # Remove barra de título padrão
    root.attributes("-topmost", True)    # Mantém sempre no topo
    root.attributes("-alpha", 0.0)       # Começa invisível (fade-in)

    # Paleta de cores por tipo
    paleta = {
        "info":  {"bg": "#0C2C11", "accent": "#89FAAB", "fg": "#CDF4D5", "icon": "⟳"},
        "erro":  {"bg": "#0C252C", "accent": "#F38BA8", "fg": "#CDF4D5", "icon": "✕"},
        "aviso": {"bg": "#0C252C", "accent": "#F9E2AF", "fg": "#CDF4D5", "icon": "⚠"},
    }
    cores = paleta.get(tipo, paleta["info"])
    root.configure(bg=cores["bg"])
    # Frame com borda colorida
    borda = tk.Frame(root, bg=cores["accent"], padx=2, pady=2)
    borda.pack(fill="both", expand=True)

    conteudo = tk.Frame(borda, bg=cores["bg"], padx=28, pady=20)
    conteudo.pack(fill="both", expand=True)
    # Ícone + título
    topo = tk.Frame(conteudo, bg=cores["bg"])
    topo.pack(fill="x", anchor="w")
    lbl_icone = tk.Label(
        topo,
        text=cores["icon"],
        font=("Segoe UI", 18),
        bg=cores["bg"],
        fg=cores["accent"],
    )
    lbl_icone.pack(side="left", padx=(0, 8))

    lbl_titulo = tk.Label(
        topo,
        text="ATT — Atualizador",
        font=("Segoe UI", 10, "bold"),
        bg=cores["bg"],
        fg=cores["accent"],
        anchor="w",
    )
    lbl_titulo.pack(side="left")

    # Separador
    sep = tk.Frame(conteudo, bg=cores["accent"], height=1)
    sep.pack(fill="x", pady=(10, 14))

    # Mensagem principal
    lbl_msg = tk.Label(
        conteudo,
        text=mensagem,
        font=("Segoe UI", 11),
        bg=cores["bg"],
        fg=cores["fg"],
        wraplength=380,
        justify="left",
        anchor="w",
    )
    lbl_msg.pack(fill="x", anchor="w")

    # Barra de progresso animada
    prog_frame = tk.Frame(conteudo, bg="#313244", height=4)
    prog_frame.pack(fill="x", pady=(18, 0))
    prog_frame.pack_propagate(False)

    prog_bar = tk.Frame(prog_frame, bg=cores["accent"], height=4)
    prog_bar.place(x=0, y=0, relwidth=1.0, height=4)

    # Centralizar na tela
    root.update_idletasks()
    largura = root.winfo_reqwidth() + 4    # +4 pela borda
    altura  = root.winfo_reqheight() + 4
    root.geometry(f"{largura}x{altura}")
    root.update_idletasks()
    x = (root.winfo_screenwidth()  // 2) - (largura // 2)
    y = (root.winfo_screenheight() // 2) - (altura  // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")

    # Animações
    duracao_ms  = tempo
    passos_fade = 20
    intervalo_fade = 150   # ms por passo

    def fade_in(passo=0):
        alpha = passo / passos_fade
        root.attributes("-alpha", min(alpha, 1.0))
        if passo < passos_fade:
            root.after(intervalo_fade // passos_fade, fade_in, passo + 1)
        else:
            animar_barra()
    def animar_barra():
        """Encolhe a barra da direita para a esquerda ao longo de `tempo` ms."""
        fps = 60
        intervalo = 1000 // fps
        passos = duracao_ms // intervalo

        def passo(n=0):
            if not root.winfo_exists():
                return
            frac = 1.0 - (n / passos)
            prog_bar.place(x=0, y=0, relwidth=max(frac, 0.0), height=4)
            if n < passos:
                root.after(intervalo, passo, n + 1)
            else:
                fade_out()

        passo()

    def fade_out(passo=0):
        if not root.winfo_exists():
            return
        alpha = 1.0 - (passo / passos_fade)
        root.attributes("-alpha", max(alpha, 0.0))
        if passo < passos_fade:
            root.after(intervalo_fade // passos_fade, fade_out, passo + 1)
        else:
            root.destroy()
    fade_in()
    root.mainloop()

if platform.system() != "Windows": # VERIFICAÇÃO DO SITEMA
    mostrar_mensagem(
        "Este script só pode ser executado no Windows.",
        5000,
        tipo="aviso",
    )
    exit()

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
except Exception as e:
    mostrar_mensagem(f"Ocorreu um erro inesperado:\n{e}", 10000, tipo="erro")