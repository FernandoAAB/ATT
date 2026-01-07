import tkinter as tk
import subprocess
import platform
import os

def mostrar_mensagem(mensagem, tempo):
    root = tk.Tk()
    root.title("ATT_Informação.")
    if os.path.exists('ATT.ico'):
        root.iconbitmap("ATT.ico")
    root.configure(bg="#363636")

    label = tk.Label(root, text=mensagem, padx=20, pady=20, bg="#363636", fg="white") # , bg="#363636"
    label.pack()

    # Centralizando a janela
    root.update_idletasks()  # Atualiza as tarefas para obter o tamanho da janela 
    # Calculando a posição x e y para centralizar
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"{root.winfo_width()}x{root.winfo_height()}+{x}+{y}")  # Define o tamanho e a posição da janela
    root.after(tempo, root.destroy) # Destroi a janela após o tempo especificado
    root.mainloop()  # Inicia o loop principal da interface gráfica

if platform.system() != "Windows":
    mostrar_mensagem("Este script só pode ser executado no Windows.", 5000)
    exit()

try:
    mostrar_mensagem("VERIFICANDO ATUALIZAÇÃO DE PROGRAMAS.", 10000)
    resto = subprocess.run(["winget", "upgrade", "--all", "--silent"],
    stdout=subprocess.DEVNULL, # NULL
    stderr=subprocess.DEVNULL,  # NULL
    stdin=subprocess.DEVNULL,  # NULL
    creationflags=subprocess.CREATE_NO_WINDOW)
except Exception as e:
    mensagem = f"Erros (se houver): {e}"
    mostrar_mensagem(mensagem, 10000)

