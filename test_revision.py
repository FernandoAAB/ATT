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


if __name__ == '__main__':
    unittest.main()
