"""Regressões verificadas na revisão de desenvolvimento do ATT."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from att_backend import Package, load_preferences, save_preferences
from att_history import ActivityStore
from main import ATTApp
from test_att import FakeClient


class MixedResultsClient(FakeClient):
    def upgrade(self, package):
        self.calls.append(package.identifier)
        if package.identifier == 'Acme.Editor':
            return 'Atualizado', 'ok'
        return 'Falhou', 'Código 0x8A150008\nFalha no download do pacote.'


class HistoryRevisionTests(unittest.TestCase):
    def test_two_open_windows_keep_both_update_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            first = ActivityStore(path)
            second = ActivityStore(path)
            first.record(Package('Editor', 'Acme.Editor', '1', '2', 'winget'), 'Atualizado', 'ok')
            second.record(Package('Browser', 'Acme.Browser', '1', '2', 'winget'), 'Falhou', 'Sem acesso')
            saved = ActivityStore(path)
            self.assertEqual([entry['identifier'] for entry in saved.entries],
                             ['Acme.Editor', 'Acme.Browser'])

    def test_simultaneous_writers_keep_every_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            ready = threading.Barrier(8)

            def record(index):
                store = ActivityStore(path)
                ready.wait(timeout=5)
                store.record(Package(f'App {index}', f'Acme.App{index}', '1', '2', 'winget'),
                             'Atualizado', 'ok' * 500)

            with ThreadPoolExecutor(max_workers=8) as workers:
                list(workers.map(record, range(8)))
            saved = ActivityStore(path)
            self.assertEqual(len(saved.entries), 8)
            self.assertEqual(len({entry['identifier'] for entry in saved.entries}), 8)

    def test_retry_after_disk_error_keeps_pending_and_other_window_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            first, second = ActivityStore(path), ActivityStore(path)
            with patch('att_history.datetime', wraps=datetime) as clock:
                clock.now.side_effect = [datetime.fromisoformat(value) for value in (
                    '2026-10-26T08:00:00-03:00', '2026-10-26T09:00:00-03:00',
                    '2026-10-26T10:00:00-03:00')]
                with patch('att_storage.os.replace', side_effect=PermissionError('Disco indisponível')):
                    with self.assertRaises(PermissionError):
                        first.record(Package('Editor', 'Acme.Editor', '1', '2', 'winget'), 'Atualizado', 'ok')
                second.record(Package('Browser', 'Acme.Browser', '1', '2', 'winget'), 'Falhou', 'Sem acesso')
                first.checked()
            saved = ActivityStore(path)
            self.assertEqual([entry['identifier'] for entry in saved.entries],
                             ['Acme.Editor', 'Acme.Browser'])
            self.assertEqual(len({entry['event_id'] for entry in saved.entries}), 2)
            self.assertFalse(list(Path(directory).glob('*.tmp')))

    def test_check_from_another_open_window_does_not_erase_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            first, second = ActivityStore(path), ActivityStore(path)
            first.record(Package('Editor', 'Acme.Editor', '1', '2', 'winget'), 'Atualizado', 'ok')
            second.checked()
            saved = ActivityStore(path)
            self.assertEqual([entry['identifier'] for entry in saved.entries], ['Acme.Editor'])
            self.assertTrue(saved.last_check)

    def test_separate_processes_keep_both_results(self):
        worker = '''
from pathlib import Path
import sys, time
from att_backend import Package
from att_history import ActivityStore
folder, name = Path(sys.argv[1]), sys.argv[2]
store = ActivityStore(folder / 'config.json')
(folder / (name + '.ready')).touch()
deadline = time.monotonic() + 5
while len(list(folder.glob('*.ready'))) < 2:
    if time.monotonic() > deadline:
        raise RuntimeError('O outro processo não ficou pronto')
    time.sleep(0.01)
store.record(Package(name, 'Acme.' + name, '1', '2', 'winget'), 'Atualizado', 'ok')
'''
        with tempfile.TemporaryDirectory() as directory:
            processes = [subprocess.Popen([sys.executable, '-c', worker, directory, name],
                                         cwd=Path(__file__).resolve().parent,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                         for name in ('First', 'Second')]
            try:
                for process in processes:
                    _, errors = process.communicate(timeout=10)
                    self.assertEqual(process.returncode, 0, errors)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
            saved = ActivityStore(Path(directory) / 'config.json')
            self.assertEqual({entry['identifier'] for entry in saved.entries},
                             {'Acme.First', 'Acme.Second'})

    def test_corruption_after_window_opens_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            store = ActivityStore(path)
            store.checked()
            store.path.write_text('{arquivo danificado', encoding='utf-8')
            with self.assertRaises(OSError):
                store.record(Package('Editor', 'Acme.Editor', '1', '2', 'winget'), 'Atualizado', 'ok')
            self.assertEqual(store.path.read_text(encoding='utf-8'), '{arquivo danificado')


class PreferencesRevisionTests(unittest.TestCase):
    def test_simultaneous_preference_saves_leave_valid_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            ready = threading.Barrier(8)

            def save(index):
                ready.wait(timeout=5)
                save_preferences(index % 2 == 0, path)

            with ThreadPoolExecutor(max_workers=8) as workers:
                list(workers.map(save, range(8)))
            enabled, warning = load_preferences(path)
            self.assertIsInstance(enabled, bool)
            self.assertEqual(warning, '')


class DashboardRevisionTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest('Interface requer uma tela ou Xvfb')
        self.directory = tempfile.TemporaryDirectory()
        self.app = ATTApp(self.root, FakeClient(), Path(self.directory.name) / 'config.json', autostart=False)
        self.root.update()
        self.app.refresh()
        self.wait_idle()

    def wait_idle(self):
        deadline = time.monotonic() + 5
        while self.app.busy or not self.app.events.empty():
            self.root.update()
            if time.monotonic() > deadline:
                self.fail('A operação não terminou')
            time.sleep(0.01)
        self.root.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            self.wait_idle()
            self.root.destroy()
            self.directory.cleanup()

    def test_finished_queue_does_not_offer_completed_program_as_ready(self):
        self.app.select_all()
        self.app.start_updates()
        self.wait_idle()
        dashboard = self.app.dashboard
        self.assertNotIn('Pronto para iniciar', dashboard.queue_list.get('1.0', 'end'))
        self.assertEqual(dashboard.queue_count.cget('text'), '2 de 2 processados')
        self.assertEqual(dashboard.execution_state.cget('text'), 'CONCLUÍDA')

    def test_new_selection_does_not_inherit_previous_completion(self):
        self.app.tree.selection_set('0')
        self.app.tree.focus_force()
        self.app.tree.event_generate('<space>')
        self.root.update()
        self.app.start_updates()
        self.wait_idle()
        self.app.select_all()
        self.root.update()
        self.assertEqual(self.app.dashboard.percent.cget('text'), '0%')
        self.assertEqual(float(self.app.progress.cget('value')), 0)
        self.assertEqual(self.app.dashboard.execution_state.cget('text'), 'EM ESPERA')

    def test_selecting_updates_keeps_inventory_selection(self):
        dashboard = self.app.dashboard
        dashboard.show('Aplicativos')
        row = dashboard.apps_tree.get_children()[0]
        dashboard.apps_tree.selection_set(row)
        self.root.update()
        self.app.select_all()
        self.root.update()
        self.assertEqual(dashboard.apps_tree.selection(), (row,))

    def test_filter_actions_fit_at_intermediate_window_sizes(self):
        for width in (900, 1100, 1200, 1280):
            with self.subTest(width=width):
                self.root.geometry(f'{width}x720')
                self.root.update()
                button = self.app.select_button
                self.assertLessEqual(button.winfo_x() + button.winfo_width(),
                                     button.master.winfo_width())

    def test_long_type_name_does_not_overlap_menu_arrow(self):
        self.app.dashboard.type_filter.set('Desenvolvimento')
        self.root.update()
        choice = self.app.dashboard.type_combo
        text_items = [item for item in choice.find_all() if choice.type(item) == 'text']
        self.assertEqual(len(text_items), 1)
        self.assertEqual(choice.itemcget(text_items[0], 'text'), 'Desenvolvimento')
        self.assertLessEqual(choice.bbox(text_items[0])[2], choice.winfo_width() - 24)

    def test_initial_window_fits_a_laptop_screen(self):
        self.root.destroy()
        self.root = tk.Tk()
        with patch.object(self.root, 'winfo_screenheight', return_value=768), \
                patch.object(self.root, 'winfo_screenwidth', return_value=1366):
            self.app = ATTApp(self.root, FakeClient(), Path(self.directory.name) / 'config.json', autostart=False)
        self.root.update()
        self.assertLessEqual(self.root.winfo_height(), 680)
        self.assertLessEqual(self.root.minsize()[1], 560)

    def test_settings_last_line_can_be_read_in_short_window(self):
        self.root.geometry('900x560')
        self.app.dashboard.show('Configurações')
        self.root.update()
        text = self.app.dashboard.settings_text
        self.assertIn('proteção do Windows', text.get('1.0', 'end'))
        text.yview_moveto(1)
        self.root.update()
        self.assertIsNotNone(text.dlineinfo('end-2c'))
        self.assertLessEqual(text.winfo_rooty() + text.winfo_height(),
                             self.root.winfo_rooty() + self.root.winfo_height())

    def test_selected_filter_keeps_success_and_failure_results_visible(self):
        self.app.client = MixedResultsClient()
        self.app.select_all()
        self.app.dashboard.status_filter.set('Selecionados')
        self.app.start_updates()
        self.wait_idle()
        self.assertEqual(self.app.statuses, {'0': 'Atualizado', '1': 'Falhou'})
        self.assertEqual(self.app.tree.get_children(), ('0', '1'))

    def test_new_query_shows_updates_after_selected_filter(self):
        self.app.select_all()
        self.app.dashboard.status_filter.set('Selecionados')
        self.app.refresh()
        self.wait_idle()
        self.assertEqual(self.app.dashboard.status_filter.get(), 'Todos os status')
        self.assertEqual(self.app.tree.get_children(), ('0', '1'))

    def test_retry_selection_only_repeats_failed_packages(self):
        self.app.client = MixedResultsClient()
        self.app.select_all()
        self.app.start_updates()
        self.wait_idle()
        self.app.dashboard.retry_button.invoke()
        self.assertEqual(self.app.selected, {'1'})
        self.app.client = FakeClient()
        self.app.start_updates()
        self.wait_idle()
        self.assertEqual(self.app.client.calls, ['Acme.Browser'])
        self.assertEqual(self.app.statuses, {'0': 'Atualizado', '1': 'Atualizado'})

    def test_failure_details_can_be_copied(self):
        self.app.client = MixedResultsClient()
        self.app.select_all()
        self.app.start_updates()
        self.wait_idle()
        self.app.tree.selection_set('1')
        self.root.update()
        popup = self.app.dashboard.show_package()
        self.root.update()
        buttons = [child for frame in popup.winfo_children() for child in frame.winfo_children()
                   if callable(getattr(child, 'invoke', None)) and child.cget('text') == 'Copiar detalhes']
        self.assertEqual(len(buttons), 1)
        buttons[0].invoke()
        self.assertIn('Acme.Browser', self.root.clipboard_get())
        self.assertIn('0x8A150008', self.root.clipboard_get())

    def test_short_window_keeps_navigation_and_main_action_visible(self):
        self.root.geometry('900x520')
        for view in self.app.dashboard.nav:
            with self.subTest(view=view):
                self.app.dashboard.show(view)
                self.root.update()
                button = self.app.update_button
                self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                     self.root.winfo_rooty() + self.root.winfo_height())
                for navigation in self.app.dashboard.nav.values():
                    self.assertTrue(navigation.winfo_ismapped())
                    self.assertLessEqual(navigation.winfo_rooty() + navigation.winfo_height(),
                                         self.root.winfo_rooty() + self.root.winfo_height())


if __name__ == '__main__':
    unittest.main()
