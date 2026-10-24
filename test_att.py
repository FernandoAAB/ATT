"""python3 -m unittest -v (teste visual requer DISPLAY/Xvfb)."""

from pathlib import Path
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from att_backend import (
    ALREADY_INSTALLED, NO_APPLICATIONS, NOT_APPLICABLE, REBOOT_REQUIRED,
    Package, WingetClient, WingetError, load_preferences, parse_upgrades, save_preferences,
)
from main import ATTApp, main
from att_history import ActivityStore


def table(rows, portuguese=False):
    headings = ("Nome", "ID", "Versão", "Disponível", "Origem") if portuguese else (
        "Name", "Id", "Version", "Available", "Source")
    def row(values):
        return f"{values[0]:<28}{values[1]:<30}{values[2]:<16}{values[3]:<16}{values[4]}"
    return "\n".join([row(headings), "-" * 96, *(row(values) for values in rows),
                      f"{len(rows)} upgrades available."])


ROWS = [("Editor", "Acme.Editor", "1.0", "2.0", "winget"),
        ("Navegador", "Acme.Browser", "3.0", "4.0", "winget")]


def winget_response(code, output):
    return subprocess.CompletedProcess(['winget'], code, stdout=output, stderr='')


class BackendTests(unittest.TestCase):
    def test_portuguese_and_english_tables_and_ansi(self):
        for portuguese in (False, True):
            packages = parse_upgrades("\x1b[32m" + table(ROWS, portuguese) + "\x1b[0m")
            self.assertEqual([p.identifier for p in packages], ["Acme.Editor", "Acme.Browser"])
            self.assertFalse(any(p.blocked for p in packages))

    def test_unicode_terminal_width(self):
        output = table([("编辑器", *ROWS[0][1:])])
        output = output.replace("编辑器" + " " * 25, "编辑器" + " " * 22)
        package = parse_upgrades(output)[0]
        self.assertEqual(package.identifier, "Acme.Editor")
        self.assertFalse(package.blocked)

    def test_truncated_missing_and_duplicate_identifiers_blocked(self):
        for identifier in ("Acme.Edi…", "Acme.Edi...", "--all"):
            self.assertTrue(parse_upgrades(table([("Editor", identifier, "1", "2", "winget")]))[0].blocked)
        self.assertTrue(parse_upgrades(table([("Editor", "Acme.Editor", "1", "2", "")]))[0].blocked)
        packages = parse_upgrades(table([ROWS[0], ROWS[0]]))
        self.assertTrue(all(p.blocked for p in packages))

    def test_invalid_format_not_reported_as_no_updates(self):
        for output in ("", "Falha ao acessar a origem", "Name Id Version Source\n--------\nEditor Acme.Editor 1 winget"):
            with self.assertRaises(WingetError):
                parse_upgrades(output)

    def test_single_space_headers_and_pinned_table_not_included(self):
        # Uma tabela real usa o máximo de cada coluna e mais um espaço.
        output = (
            "Name    Id              Version Available Source\n"
            "-----------------------------------------------\n"
            "Firefox Mozilla.Firefox 1.0     2.0       winget\n"
            "1 upgrades available.\n\n"
            "The following packages have pins that prevent upgrade:\n" + table(ROWS)
        )
        packages = parse_upgrades(output)
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0].identifier, "Mozilla.Firefox")
        self.assertEqual(packages[0].source, "winget")
        self.assertFalse(packages[0].blocked)

    def test_zero_exit_empty_messages_and_unknown_output(self):
        client = WingetClient()
        for message in ("No installed package found matching input criteria.",
                        "Nenhum pacote instalado foi encontrado que corresponda aos critérios de entrada."):
            with patch("att_backend.subprocess.run", return_value=winget_response(0, message)):
                self.assertEqual(client.discover(), [])
        with patch("att_backend.subprocess.run", return_value=winget_response(0, "Unrecognized response")):
            with self.assertRaises(WingetError):
                client.discover()

    def test_preferences_first_use_roundtrip_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ATT" / "config.json"
            self.assertEqual(load_preferences(path), (False, ""))
            save_preferences(True, path)
            self.assertEqual(load_preferences(path), (True, ""))
            save_preferences(False, path)
            self.assertEqual(load_preferences(path), (False, ""))
            for value in ('{"auto_update": "false"}', '{', '[]'):
                path.write_text(value)
                enabled, warning = load_preferences(path)
                self.assertFalse(enabled)
                self.assertTrue(warning)

    def test_discovery_codes_and_exact_upgrade_arguments(self):
        client = WingetClient()
        package = parse_upgrades(table(ROWS))[0]
        for code in (NO_APPLICATIONS, NOT_APPLICABLE):
            with patch("att_backend.subprocess.run", return_value=winget_response(code, "Sem atualizações")):
                self.assertEqual(client.discover(), [])
        with patch("att_backend.subprocess.run", return_value=winget_response(1, "Origem indisponível")):
            with self.assertRaisesRegex(WingetError, "Origem indisponível"):
                client.discover()
        with patch("att_backend.subprocess.run", return_value=winget_response(0, "ok")) as command:
            self.assertEqual(client.upgrade(package)[0], "Atualizado")
            arguments = command.call_args.args[0][1:]
            self.assertEqual(arguments, ["upgrade", "--id", "Acme.Editor", "--exact", "--source", "winget", "--silent", "--disable-interactivity"])
            self.assertNotIn("--all", arguments)

    def test_result_classification(self):
        client = WingetClient()
        package = parse_upgrades(table(ROWS))[0]
        for code, expected in ((0, "Atualizado"), (REBOOT_REQUIRED, "Reinício necessário"),
                               (NOT_APPLICABLE, "Sem atualização"), (ALREADY_INSTALLED, "Sem atualização"),
                               (0x8A15010A, "Falhou"), (5, "Falhou")):
            with patch("att_backend.subprocess.run", return_value=winget_response(code, "detalhes")):
                self.assertEqual(client.upgrade(package)[0], expected)

    def test_missing_winget_and_timeout(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("winget", 180)):
            with patch("att_backend.subprocess.run", side_effect=error):
                with self.assertRaises(WingetError):
                    WingetClient().discover()

    def test_installed_inventory_column_layouts(self):
        fixtures = (
            "Name    Id              Version\n--------------------------------\nFirefox Mozilla.Firefox 1.0\n",
            "Name    Id              Version Source\n--------------------------------------\nFirefox Mozilla.Firefox 1.0     winget\n",
            table(ROWS),
        )
        client = WingetClient()
        for output in fixtures:
            with patch("att_backend.subprocess.run", return_value=winget_response(0, output)):
                inventory = client.list_installed()
                self.assertTrue(inventory)
                self.assertEqual(inventory[0].installed, '1.0')
        with patch("att_backend.subprocess.run", return_value=winget_response(1, 'Origem indisponível')):
            with self.assertRaises(WingetError):
                client.list_installed()

    def test_history_survives_restart_and_preserves_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            store = ActivityStore(path)
            store.checked()
            store.record(parse_upgrades(table(ROWS))[0], 'Atualizado', 'ok')
            restored = ActivityStore(path)
            self.assertEqual(restored.entries[0]['identifier'], 'Acme.Editor')
            self.assertEqual(restored.last_check, store.last_check)
            restored.path.write_text('{corrompido')
            broken = ActivityStore(path)
            self.assertTrue(broken.warning)
            with self.assertRaises(OSError):
                broken.checked()
            self.assertEqual(broken.path.read_text(), '{corrompido')

    def test_non_windows_rejected_without_starting_ui(self):
        with patch("main.platform.system", return_value="Linux"), patch("main.tk.Tk") as window:
            self.assertEqual(main(), 1)
            window.assert_not_called()


class FakeClient:
    def __init__(self):
        self.calls = []
        self.result = ("Atualizado", "Instalado com sucesso")
        self.gate = None
        self.entered = threading.Event()
        self.query_error = None
        self.packages = parse_upgrades(table(ROWS))

    def discover(self):
        if self.query_error:
            raise WingetError(self.query_error)
        return self.packages

    def list_installed(self):
        return list(self.packages)

    def upgrade(self, package):
        self.calls.append(package.identifier)
        self.entered.set()
        if self.gate and not self.gate.wait(5):
            raise RuntimeError("O teste não liberou o instalador")
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("Interface requer uma tela ou Xvfb")
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "config.json"
        self.client = FakeClient()
        self.app = ATTApp(self.root, self.client, self.path, autostart=False)
        self.root.update()

    def tearDown(self):
        if hasattr(self, "app"):
            if self.client.gate:
                self.client.gate.set()
            self.wait_idle()
            try:
                self.root.destroy()
            except tk.TclError:
                pass
            self.directory.cleanup()

    def wait_idle(self):
        deadline = time.monotonic() + 5
        while self.app.busy or not self.app.events.empty():
            self.root.update()
            if time.monotonic() > deadline:
                self.fail("Operação não terminou")
            time.sleep(0.01)
        self.root.update()

    def load(self, automatic=False):
        self.app.refresh(automatic)
        self.wait_idle()

    def test_manual_selection_filter_and_only_selected_install(self):
        self.load()
        self.assertEqual(self.app.selected, set())
        self.assertTrue(self.app.update_button.instate(["disabled"]))
        self.app.filter_text.set("editor")
        self.assertEqual(len(self.app.tree.get_children()), 1)
        self.app._toggle("0")
        self.assertEqual(self.app.selected, {"0"})
        self.app.start_updates()
        self.wait_idle()
        self.assertEqual(self.client.calls, ["Acme.Editor"])
        self.assertEqual(self.app.statuses, {"0": "Atualizado", "1": "Pendente"})

    def test_automatic_queue_all_and_continue_after_failure(self):
        self.client.result = ("Falhou", "Permissão negada")
        self.load(automatic=True)
        self.assertEqual(self.client.calls, ["Acme.Editor", "Acme.Browser"])
        self.assertIn("2 falha(s)", self.app.status_text.get())
        self.app.tree.selection_set("0")
        self.app._show_details()
        self.assertIn("Permissão negada", self.app.detail_box.get("1.0", "end"))

    def test_click_keyboard_and_clear_selection(self):
        self.load()
        self.root.update()
        x, y, width, height = self.app.tree.bbox("0", "select")
        self.app.tree.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
        self.root.update()
        self.assertEqual(self.app.selected, {"0"})
        self.app.tree.focus_force()
        self.app.tree.selection_set("1")
        self.app.tree.focus("1")
        self.root.update()
        self.app.tree.event_generate("<KeyPress-space>")
        self.root.update()
        self.assertEqual(self.app.selected, {"0", "1"})
        self.app.clear_selection()
        self.assertFalse(self.app.selected)

    def test_retry_summary_only_counts_current_queue(self):
        self.client.result = ("Falhou", "Sem acesso")
        self.load(automatic=True)
        self.client.result = ("Atualizado", "ok")
        self.app._toggle("0")
        self.app.start_updates()
        self.wait_idle()
        self.assertIn("0 falha(s)", self.app.status_text.get())
        self.assertEqual(self.app.statuses["1"], "Falhou")

    def test_controls_fit_minimum_window_size(self):
        self.load()
        self.root.geometry("900x720")
        self.root.update()
        button = self.app.update_button
        self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                             self.root.winfo_rootx() + self.root.winfo_width())
        self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                             self.root.winfo_rooty() + self.root.winfo_height())

    def test_stop_finishes_current_keeps_ui_responsive(self):
        self.load()
        self.client.gate = threading.Event()
        self.app.select_all()
        self.app.start_updates()
        self.assertTrue(self.client.entered.wait(1))
        self.root.update()
        self.app.filter_text.set("editor")
        self.assertEqual(len(self.app.tree.get_children()), 1)
        self.app.refresh()
        self.app.request_stop()
        self.client.gate.set()
        self.wait_idle()
        self.assertEqual(self.client.calls, ["Acme.Editor"])
        self.assertEqual(self.app.statuses["1"], "Pendente")

    def test_empty_error_and_blocked_rows(self):
        self.client.packages = []
        self.load(automatic=True)
        self.assertFalse(self.client.calls)
        self.assertIn("Tudo em dia", self.app.empty_label.cget("text"))
        self.client.query_error = "Falha de rede"
        self.load(automatic=True)
        self.assertIn("Falha de rede", self.app.detail_box.get("1.0", "end"))
        with patch.object(self.app.dashboard, 'show_package') as details:
            self.app.empty_label.event_generate('<Button-1>')
            self.root.update()
            details.assert_called_once()
        self.assertFalse(self.client.calls)
        self.client.query_error = None
        self.client.packages = [Package("Ambíguo", "Acme…", "1", "2", "winget", "ID truncado")]
        self.load(automatic=True)
        self.assertFalse(self.client.calls)
        self.assertFalse(self.app.selected)

    def test_preference_applies_only_next_launch_and_write_failure(self):
        self.load()
        self.app.auto_update.set(True)
        self.app._save_preference()
        self.assertEqual(load_preferences(self.path), (True, ""))
        self.assertFalse(self.client.calls)
        with patch("main.save_preferences", side_effect=PermissionError("Sem acesso")), patch("main.messagebox.showerror") as alert:
            self.app.auto_update.set(False)
            self.app._save_preference()
            self.assertTrue(self.app.auto_update.get())
            alert.assert_called_once()

    def test_saved_automatic_preference_on_startup(self):
        self.root.destroy()
        save_preferences(True, self.path)
        self.root = tk.Tk()
        self.app = ATTApp(self.root, self.client, self.path)
        deadline = time.monotonic() + 3
        while not self.client.calls and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.01)
        self.wait_idle()
        self.assertEqual(self.client.calls, ["Acme.Editor", "Acme.Browser"])

    def test_navigation_filters_sort_inventory_and_history(self):
        self.load()
        dashboard = self.app.dashboard
        self.assertEqual(dashboard.values[0].cget('text'), '2')
        for view in dashboard.nav:
            dashboard.nav[view].invoke()
            self.root.update()
            self.assertEqual(dashboard.heading.cget('text'), view)
        dashboard.show('Visão geral')
        dashboard.order.set('Nome Z–A')
        self.assertEqual(self.app.tree.get_children()[0], '1')
        self.app._toggle('0')
        dashboard.status_filter.set('Selecionados')
        self.assertEqual(self.app.tree.get_children(), ('0',))
        dashboard.source_filter.set('msstore')
        self.assertFalse(self.app.tree.get_children())
        dashboard.source_filter.set('Todas as origens')
        self.app.start_updates()
        self.wait_idle()
        self.assertEqual(dashboard.percent.cget('text'), '100%')
        self.assertEqual(len(dashboard.history_tree.get_children()), 1)
        self.assertEqual(dashboard.values[2].cget('text'), '1')
        self.assertEqual(len(ActivityStore(self.path).entries), 1)
        dashboard.apps_filter.set('browser')
        self.assertEqual(len(dashboard.apps_tree.get_children()), 1)
        dashboard.show('Histórico')
        dashboard.history_tree.selection_set('0')
        self.root.update()
        self.assertIn('Instalado com sucesso', dashboard.history_details.get('1.0', 'end'))

    def test_inventory_failure_does_not_block_updates(self):
        with patch.object(self.client, 'list_installed', side_effect=WingetError('Sem acesso')):
            self.load(automatic=True)
        self.assertEqual(self.client.calls, ['Acme.Editor', 'Acme.Browser'])
        self.assertEqual(self.app.dashboard.values[0].cget('text'), '—')
        self.assertIn('Sem acesso', self.app.dashboard.inventory_info.cget('text'))

    def test_new_selection_replaces_previous_queue_preview(self):
        self.load()
        self.app._toggle('0')
        self.app.start_updates()
        self.wait_idle()
        self.app._toggle('1')
        text = self.app.dashboard.queue_list.get('1.0', 'end')
        self.assertIn('Navegador', text)
        self.assertNotIn('Editor', text)

    def test_reference_layout_shows_five_rows_at_1280_by_720(self):
        self.client.packages = [Package(f'Programa {i}', f'Acme.App{i}', '1', '2', 'winget') for i in range(5)]
        self.load()
        self.root.geometry('1280x720')
        self.root.update()
        self.assertTrue(self.app.dashboard.stats.winfo_ismapped())
        self.assertTrue(self.app.dashboard.execution.winfo_ismapped())
        x, y, width, height = self.app.tree.bbox('4')
        self.assertLessEqual(y + height, self.app.tree.winfo_height())
        self.app.tree.event_generate('<Button-1>', x=18, y=14)
        self.root.update()
        self.assertEqual(len(self.app.selected), 5)
        self.app.tree.event_generate('<Button-1>', x=18, y=14)
        self.root.update()
        self.assertFalse(self.app.selected)

    def test_type_filter_and_package_details_button(self):
        self.client.packages = [Package('Firefox', 'Mozilla.Firefox', '1', '2', 'winget'),
                                Package('Editor', 'Acme.Editor', '1', '2', 'winget')]
        self.load()
        self.app.dashboard.type_filter.set('Navegadores')
        self.assertEqual(self.app.tree.get_children(), ('0',))
        self.root.update()
        with patch.object(self.app.dashboard, 'show_package') as details:
            self.app.tree.event_generate('<Button-1>', x=self.app.tree.winfo_width() - 18, y=48)
            self.root.update()
            details.assert_called_once()

    def test_history_write_failure_keeps_installation_result(self):
        self.load()
        with patch.object(self.app.activity, '_save', side_effect=PermissionError('Sem acesso')):
            self.app._toggle('0')
            self.app.start_updates()
            self.wait_idle()
        self.assertEqual(self.app.statuses['0'], 'Atualizado')
        self.assertIn('Não foi possível salvar o histórico', self.app.status_text.get())

    def test_close_waits_for_installer_and_skips_remaining(self):
        self.load()
        self.client.gate = threading.Event()
        self.app.select_all()
        self.app.start_updates()
        self.assertTrue(self.client.entered.wait(1))
        with patch("main.messagebox.askyesno", return_value=False):
            self.app.request_close()
            self.assertFalse(self.app.close_after)
        with patch("main.messagebox.askyesno", return_value=True):
            self.app.request_close()
        self.assertTrue(self.root.winfo_exists())
        self.client.gate.set()
        with patch.object(self.root, "destroy") as destroy:
            self.wait_idle()
            self.assertTrue(destroy.called)
        self.assertEqual(self.client.calls, ["Acme.Editor"])


if __name__ == "__main__":
    unittest.main()
