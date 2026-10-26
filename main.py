"""ATT — painel de atualizações para Windows, construído com Tkinter."""

import platform
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from att_backend import WingetClient, load_preferences, save_preferences
from att_history import ActivityStore
from att_dashboard import Dashboard
from att_display import enable_dpi_awareness


SUCCESS = {"Atualizado", "Reinício necessário", "Sem atualização"}


class ATTApp:
    def __init__(self, root, client=None, preference_path=None, autostart=True):
        self.root = root
        self.client = client or WingetClient()
        self.preference_path = preference_path
        self.activity = ActivityStore(preference_path)
        self.installed = None
        self.inventory_error = ""
        self.checked = False
        self.query_failed = False
        self.storage_error = ""
        self.events = queue.Queue()
        self.stop_requested = threading.Event()
        self.busy = None
        self.close_after = False
        self.packages = {}
        self.statuses = {}
        self.details = {}
        self.selected = set()
        self.completed = 0
        self.total = 0
        self.run_keys = []
        self.selection_changed_since_run = True
        self._timers = set()
        self.last_output = "Selecione um pacote para consultar seu status e os detalhes da execução."
        enabled, warning = load_preferences(preference_path)
        self.auto_launch = enabled
        self.auto_update = tk.BooleanVar(value=enabled)
        self.interactive_update = tk.BooleanVar(value=False)
        self.filter_text = tk.StringVar()
        self.status_text = tk.StringVar(value="Pronto para buscar atualizações.")
        self.progress_text = tk.StringVar(value="Nenhuma atualização em execução")
        self._build()
        self.filter_text.trace_add("write", lambda *_: self._render_rows())
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)
        self.root.bind("<Destroy>", self._on_destroy, add="+")
        self._schedule(60, self._poll)
        warning = "\n".join(filter(None, (warning, self.activity.warning)))
        if warning:
            self._schedule(100, lambda: messagebox.showwarning("Preferência indisponível", warning, parent=self.root))
        if autostart:
            self._schedule(200, lambda: self.refresh(automatic=self.auto_launch))

    def _schedule(self, milliseconds, callback):
        def invoke():
            self._timers.discard(timer)
            callback()
        timer = self.root.after(milliseconds, invoke)
        self._timers.add(timer)

    def _on_destroy(self, event):
        if event.widget == self.root:
            for timer in self._timers:
                self.root.after_cancel(timer)
            self._timers.clear()

    def _build(self):
        self.dashboard = Dashboard(self)
        self.dashboard.build()
        self._update_controls()

    def _persist(self, operation, *args):
        try:
            operation(*args)
            self.storage_error = ""
        except OSError as error:
            self.storage_error = f"Não foi possível salvar o histórico: {error}"
            self.status_text.set(self.storage_error)

    def _set_details(self, text):
        self.detail_box.configure(state="normal")
        self.detail_box.delete("1.0", "end")
        self.detail_box.insert("1.0", text[-16000:])
        self.detail_box.configure(state="disabled")

    def _save_preference(self):
        enabled = self.auto_update.get()
        try:
            save_preferences(enabled, self.preference_path)
        except OSError as error:
            self.auto_update.set(not enabled)
            messagebox.showerror("Não foi possível salvar", str(error), parent=self.root)
            return
        self.status_text.set("Preferência salva. O novo modo será usado na próxima abertura do ATT.")

    def _eligible(self, key):
        return not self.packages[key].blocked and self.statuses[key] not in SUCCESS

    def _update_controls(self):
        idle = self.busy is None
        self.refresh_button.configure(state="normal" if idle else "disabled")
        self.dashboard.interactive_check.configure(state="normal" if idle else "disabled")
        self.select_button.configure(state="normal" if idle and any(self._eligible(key) for key in self.packages) else "disabled")
        self.clear_button.configure(state="normal" if idle and self.selected else "disabled")
        self.update_button.configure(state="normal" if idle and self.selected else "disabled")
        self.stop_button.configure(state="normal" if self.busy == "update" and not self.stop_requested.is_set() else "disabled")
        has_failures = any(status == 'Falhou' for status in self.statuses.values())
        self.dashboard.retry_button.configure(state='normal' if idle and has_failures else 'disabled')
        if has_failures:
            self.dashboard.retry_button.pack(side='right')
        else:
            self.dashboard.retry_button.pack_forget()
        self.dashboard.update()

    def _render_rows(self):
        self.tree.identifiers = {key:p.identifier for key,p in self.packages.items()}
        focused = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        query = self.filter_text.get().strip().casefold()
        for key, package in self.dashboard.ordered():
            if not self.dashboard.accepts(key, package):
                continue
            if query and query not in package.name.casefold() and query not in package.identifier.casefold():
                continue
            status = self.statuses[key]
            symbol = "[x]" if key in self.selected else "[ ]"
            if not self._eligible(key):
                symbol = "—"
            tag = "blocked" if package.blocked else "failed" if status == "Falhou" else "success" if status in SUCCESS else ""
            self.tree.insert("", "end", iid=key, values=(symbol, package.name, package.installed, package.available, status), tags=(tag,))
        if focused and self.tree.exists(focused[0]):
            self.tree.selection_set(focused[0])
        if self.tree.get_children():
            self.empty_label.place_forget()
        else:
            filtered = query or self.dashboard.status_filter.get() != "Todos os status" or self.dashboard.source_filter.get() != "Todas as origens" or self.dashboard.type_filter.get() != "Todos os tipos"
            text = "Nenhum programa corresponde ao filtro." if filtered else self.last_output
            self.empty_label.configure(text=text[:160], cursor="hand2" if self.query_failed else "")
            self.empty_label.place(relx=0.5, rely=0.55, anchor="center")
        self._update_controls()

    def _toggle(self, key):
        if self.busy or not key or not self._eligible(key):
            return
        self.selection_changed_since_run = True
        if key in self.selected:
            self.selected.remove(key)
        else:
            self.selected.add(key)
        self._render_rows()

    def _click_row(self, event):
        if event.x>self.tree.winfo_width()-6:
            self.tree.drag_scroll(event.y)
            return
        if event.y<30 and event.x<38:
            if not self.busy:self.dashboard.toggle_all()
            return
        key = self.tree.identify_row(event.y)
        if not key:return
        self.tree.focus_force()
        self.tree.selection_set(key)
        if self.tree.identify_column(event.x) == "#1":
            self._toggle(key)
        elif self.tree.identify_column(event.x) == "#6":
            self.dashboard.show_package()

    def _space_row(self, _event):
        selected = self.tree.selection()
        if selected:
            self._toggle(selected[0])
        return "break"

    def _show_details(self, _event=None):
        selected = self.tree.selection()
        if selected and selected[0] in self.packages:
            key = selected[0]
            package = self.packages[key]
            self._set_details(f"{package.name}  •  {package.identifier}  •  Origem: {package.source}\n"
                              + (self.details.get(key) or package.blocked or "Aguardando seleção para atualizar."))

    def select_all(self):
        if not self.busy:
            self.selection_changed_since_run = True
            self.selected = {key for key in self.packages if self._eligible(key)}
            self._render_rows()

    def clear_selection(self):
        if not self.busy:
            self.selection_changed_since_run = True
            self.selected.clear()
            self._render_rows()

    def select_failed(self):
        if self.busy:
            return
        self.selected = {key for key in self.packages if self.statuses[key] == 'Falhou' and self._eligible(key)}
        self.selection_changed_since_run = True
        self.filter_text.set('')
        self.dashboard.source_filter.set('Todas as origens')
        self.dashboard.type_filter.set('Todos os tipos')
        self.dashboard.status_filter.set('Selecionados')
        self._render_rows()
        self.status_text.set('Falhas selecionadas. Clique em Atualizar selecionados para tentar novamente.')

    def refresh(self, automatic=False):
        if self.busy:
            return
        self.busy = "query"
        self.packages.clear()
        self.statuses.clear()
        self.details.clear()
        self.selected.clear()
        self.completed = 0
        self.total = 0
        self.run_keys = []
        self.selection_changed_since_run = True
        self.checked = False
        self.query_failed = False
        self.installed = None
        self.inventory_error = ""
        self.dashboard.source_filter.set("Todas as origens")
        if self.dashboard.status_filter.get() == 'Selecionados':
            self.dashboard.status_filter.set('Todos os status')
        self.last_output = "Consultando atualizações com o winget…"
        self.status_text.set(self.last_output)
        self.progress_text.set("Buscando versões disponíveis…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._set_details("A consulta pode levar alguns instantes. Nenhum pacote é instalado nesta etapa.")
        self._render_rows()
        threading.Thread(target=self._query_worker, args=(automatic,), daemon=False).start()

    def _query_worker(self, automatic):
        try:
            packages = self.client.discover()
            installed, error = None, ""
            try:
                installed = self.client.list_installed()
            except Exception as problem:
                error = f"Inventário indisponível: {problem}"
            self.events.put(("found", packages, automatic, installed, error))
        except Exception as error:
            self.events.put(("query_error", str(error)))

    def start_updates(self):
        if self.busy:
            return
        keys = [key for key in self.packages if key in self.selected and self._eligible(key)]
        if not keys:
            return
        self.busy = "update"
        self.stop_requested.clear()
        self.dashboard.stop_toggle.set(False)
        self.completed = 0
        self.total = len(keys)
        self.run_keys = keys
        self.selection_changed_since_run = False
        self.progress.configure(mode="determinate", maximum=self.total, value=0)
        self.progress_text.set(f"0 de {self.total} processados")
        for key in keys:
            self.statuses[key] = "Na fila"
        interactive = self.interactive_update.get()
        self.status_text.set("Modo PowerShell: responda às solicitações na janela do terminal."
                             if interactive else "Atualizando os pacotes. O Windows poderá solicitar permissão.")
        self._render_rows()
        threading.Thread(target=self._upgrade_worker,
                         args=([(key, self.packages[key]) for key in keys], interactive), daemon=False).start()

    def _upgrade_worker(self, items, interactive=False):
        for key, package in items:
            if self.stop_requested.is_set():
                break
            self.events.put(("started", key))
            try:
                operation = self.client.upgrade_interactive if interactive else self.client.upgrade
                status, details = operation(package)
            except Exception as error:
                status, details = "Falhou", str(error)
            self.events.put(("result", key, status, details))
        self.events.put(("finished",))

    def request_stop(self):
        if self.busy == "update":
            self.stop_requested.set()
            self.status_text.set("A fila será interrompida após a instalação em andamento.")
            self._update_controls()

    def request_close(self):
        if not self.busy:
            self.root.destroy()
        elif messagebox.askyesno("Sair após a operação atual?",
                                 "A operação em andamento será concluída antes de sair.\n"
                                 "Os próximos pacotes não serão iniciados.\n\n"
                                 "Deseja sair assim que ela terminar?", parent=self.root):
            self.close_after = True
            self.stop_requested.set()
            self.status_text.set("Aguardando a operação atual terminar para fechar…")
            self._update_controls()

    def _handle_event(self, event):
        kind = event[0]
        if kind in ("found", "query_error"):
            self.progress.stop()
            self.progress.configure(mode="determinate", value=0)
            self.busy = None
            if kind == "query_error":
                self.query_failed = True
                self.last_output = "Não foi possível consultar. Clique aqui para ver os detalhes e tente novamente."
                self._set_details(event[1])
                self.status_text.set("Falha na consulta. Nenhuma atualização foi iniciada.")
            else:
                self.checked = True
                self.installed = event[3] if len(event) > 3 else None
                self.inventory_error = event[4] if len(event) > 4 else ""
                self._persist(self.activity.checked)
                for index, package in enumerate(event[1]):
                    key = str(index)
                    self.packages[key] = package
                    self.statuses[key] = "Indisponível" if package.blocked else "Pendente"
                self.last_output = "Tudo em dia. Nenhuma atualização disponível."
                blocked = sum(bool(package.blocked) for package in self.packages.values())
                self.status_text.set(f"{len(self.packages)} atualização(ões) encontrada(s)."
                                     + (f" {blocked} item(ns) bloqueado(s); selecione a linha para ver o motivo." if blocked else ""))
                self._set_details("Marque os programas que deseja atualizar e clique em Atualizar selecionados.")
            self.progress_text.set("Consulta concluída" if kind == "found" else "Consulta não concluída")
            self._render_rows()
            if self.storage_error:
                self.status_text.set(self.storage_error)
            elif self.inventory_error:
                self.status_text.set(self.status_text.get() + " Inventário indisponível; veja Aplicativos.")
            if self.close_after:
                return
            if kind == "found" and event[2] and self.packages:
                self.select_all()
                self.start_updates()
        elif kind == "started":
            key = event[1]
            self.statuses[key] = "Atualizando…"
            self.progress_text.set(f"{self.completed} de {self.total} processados • {self.packages[key].name}")
            self._render_rows()
            if self.tree.exists(key):
                self.tree.selection_set(key)
                self.tree.see(key)
            note = ("Responda às solicitações no PowerShell. Se houver erro, pressione Enter no terminal para retornar ao ATT."
                    if self.interactive_update.get() else "Aguardando o instalador concluir.")
            self._set_details(f"Atualizando {self.packages[key].name}…\n{note}")
        elif kind == "result":
            _, key, status, details = event
            self.statuses[key] = status
            self._persist(self.activity.record, self.packages[key], status, details)
            self.details[key] = status + ("\n" + details if details else "")
            self.selected.discard(key)
            self.completed += 1
            self.progress.configure(value=self.completed)
            self.progress_text.set(f"{self.completed} de {self.total} processados")
            self._render_rows()
            self._set_details(f"{self.packages[key].name}: {self.details[key]}")
        elif kind == "finished":
            self.busy = None
            self.dashboard.stop_toggle.set(False)
            for key in self.packages:
                if self.statuses[key] == "Na fila":
                    self.statuses[key] = "Pendente"
            results = [self.statuses[key] for key in self.run_keys]
            failed = results.count("Falhou")
            updated = results.count("Atualizado") + results.count("Reinício necessário")
            unchanged = results.count("Sem atualização")
            restart = "Reinício necessário" in results
            self.status_text.set(f"{'Fila interrompida' if self.stop_requested.is_set() else 'Execução concluída'}: "
                                 f"{self.completed} de {self.total} processados; {updated} atualizado(s), "
                                 f"{unchanged} sem atualização, {failed} falha(s). "
                                 + ("Reinicie o Windows para concluir a instalação. " if restart else "")
                                 + "Busque novamente para atualizar a lista.")
            if self.storage_error:
                self.status_text.set(self.status_text.get() + " " + self.storage_error)
            self._render_rows()

    def _poll(self):
        try:
            while True:
                self._handle_event(self.events.get_nowait())
        except queue.Empty:
            pass
        if self.close_after and not self.busy:
            self.root.destroy()
            return
        self._schedule(60, self._poll)


def main():
    if platform.system() != "Windows":
        print("O ATT só pode executar atualizações no Windows.", file=sys.stderr)
        return 1
    enable_dpi_awareness()
    root = tk.Tk()
    ATTApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
