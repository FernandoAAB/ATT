import tkinter as tk
import subprocess


def mostrar_mensagem(mensagem, tempo):
    root = tk.Tk()
    root.title("Atualizador")

    root.configure(bg="#363636")
    label = tk.Label(root, text=mensagem, padx=20, pady=20, bg="#363636", fg="white") # , bg="#363636"
    label.pack()

    # Centralizando a janela
    root.update_idletasks()  # Atualiza as tarefas para obter o tamanho da janela
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculando a posição x e y para centralizar
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")  # Define o tamanho e a posição da janela

    # Destroi a janela após o tempo especificado
    root.after(tempo, root.destroy)
    root.mainloop()  # Inicia o loop principal da interface gráfica

try:
    mostrar_mensagem("VERIFICANDO ATUALIZAÇÃO DE PROGRAMAS.", 10000)
    resto = subprocess.run(["winget", "upgrade", "--all", "--silent"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    if resto.returncode != 0:
        mostrar_mensagem("Erro ao atualizar programas.", 10000)
    else:
        mostrar_mensagem("Programas atualizados com sucesso.", 10000)

except Exception as e:
    mostrar_mensagem("Erro inesperado: " + str(e), 10000)