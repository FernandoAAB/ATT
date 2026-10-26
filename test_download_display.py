"""Regressões de execução com terminal e apresentação nítida."""
import subprocess
import re
from pathlib import Path
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from att_backend import Package, WingetClient, WingetError
from main import ATTApp, main
from att_display import enable_dpi_awareness
from test_att import FakeClient


class InteractiveUpgradeTests(unittest.TestCase):
    def test_visible_terminal_allows_prompts_and_keeps_exact_package(self):
        package = Package('Editor', 'Acme.Editor', '1', '2', 'winget')
        with patch('att_backend.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            status, details = WingetClient().upgrade_interactive(package)
        self.assertEqual(status, 'Atualizado')
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ['powershell.exe', '-NoProfile', '-Command'])
        self.assertIn("--id 'Acme.Editor' --exact --source 'winget'", command[3])
        self.assertNotIn('Tee-Object', command[3])
        self.assertNotIn('2>&1', command[3])
        self.assertNotIn('|', command[3])
        for flag in ('--silent', '--disable-interactivity', '--all', '--accept-', '--ignore-'):
            self.assertNotIn(flag, command[3])
        self.assertNotIn('stdin', run.call_args.kwargs)
        self.assertFalse(run.call_args.kwargs.get('capture_output', False))
        self.assertTrue(run.call_args.kwargs['creationflags'] & 0x10)  # CREATE_NEW_CONSOLE
        self.assertIn('PowerShell', details)

    def test_terminal_failure_keeps_original_output_and_return_code(self):
        def terminal(command, **kwargs):
            path = re.search(r"WriteAllLines\('((?:[^']|'')+)'", command[3]).group(1).replace("''", "'")
            Path(path).write_text('Download request status is not success.\n0x80190194 : Não encontrado (404).', encoding='utf-16')
            return subprocess.CompletedProcess(command, 0x8A150008 - 2**32)
        with patch('att_backend.subprocess.run', side_effect=terminal):
            status, details = WingetClient().upgrade_interactive(Package('Editor', 'Acme.Editor', '1', '2', 'winget'))
        self.assertEqual(status, 'Falhou')
        self.assertIn('HTTP 404', details)
        self.assertIn('0x8A150008', details)
        self.assertIn('Não encontrado (404)', details)
        self.assertIn('PowerShell', details)

    def test_terminal_rejects_ambiguous_and_injected_package_before_launch(self):
        for identifier in ('Acme.Editor; Remove-Item', "Acme.Editor'", '--all', 'Acme.Edi...'):
            with self.subTest(identifier=identifier), patch('att_backend.subprocess.run') as run:
                with self.assertRaises(WingetError):
                    WingetClient().upgrade_interactive(Package('Editor', identifier, '1', '2', 'winget'))
                run.assert_not_called()


class InteractiveDashboardTests(unittest.TestCase):
    def test_terminal_queue_waits_and_retains_failure_with_other_packages(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest('Interface requer tela ou Xvfb')
        class Client(FakeClient):
            def upgrade_interactive(self, package):
                self.called.append(package.identifier)
                return ('Falhou', '0x80190194') if len(self.called) == 1 else ('Atualizado', 'ok')
        client = Client()
        client.called = []
        try:
            with tempfile.TemporaryDirectory() as folder:
                app = ATTApp(root, client, Path(folder) / 'config.json', autostart=False)
                app._handle_event(('found', client.discover(), False, [], ''))
                app.interactive_update.set(True)
                app.select_all()
                app.start_updates()
                self.assertTrue(app.dashboard.interactive_check.instate(['disabled']))
                deadline = time.monotonic() + 5
                while app.busy or not app.events.empty():
                    root.update()
                    if time.monotonic() > deadline:
                        self.fail('Fila não terminou')
                    time.sleep(.01)
                self.assertEqual(client.called, ['Acme.Editor', 'Acme.Browser'])
                self.assertEqual(app.statuses, {'0': 'Falhou', '1': 'Atualizado'})
                self.assertEqual(len(app.tree.get_children()), 2)
                self.assertEqual(app.completed, 2)
                self.assertIn('0x80190194', app.details['0'])
                self.assertFalse(app.dashboard.interactive_check.instate(['disabled']))
        finally:
            root.destroy()


class DisplayTests(unittest.TestCase):
    def test_dpi_configuration_happens_before_window_creation(self):
        order = []
        def create_window():
            order.append('window')
            from unittest.mock import Mock
            return Mock()
        with patch('main.platform.system', return_value='Windows'), \
                patch('main.enable_dpi_awareness', create=True, side_effect=lambda: order.append('dpi')), \
                patch('main.tk.Tk', side_effect=create_window), patch('main.ATTApp'):
            self.assertEqual(main(), 0)
        self.assertEqual(order, ['dpi', 'window'])

    def test_existing_dpi_manifest_is_respected(self):
        from unittest.mock import Mock
        api = Mock()
        api.shcore.SetProcessDpiAwareness.return_value = -2147024891  # E_ACCESSDENIED
        with patch('att_display.sys.platform', 'win32'), patch('att_display.ctypes.windll', api, create=True):
            self.assertTrue(enable_dpi_awareness())
        api.user32.SetProcessDPIAware.assert_not_called()

    def test_older_windows_uses_supported_dpi_fallback(self):
        from unittest.mock import Mock
        api = Mock()
        api.shcore.SetProcessDpiAwareness.side_effect = AttributeError('API indisponível')
        api.user32.SetProcessDPIAware.return_value = 1
        with patch('att_display.sys.platform', 'win32'), patch('att_display.ctypes.windll', api, create=True):
            self.assertTrue(enable_dpi_awareness())
        api.user32.SetProcessDPIAware.assert_called_once_with()

    def test_tab_icons_keep_native_sized_images_after_navigation(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest('Interface requer tela ou Xvfb')
        try:
            with tempfile.TemporaryDirectory() as folder:
                app = ATTApp(root, FakeClient(), Path(folder) / 'config.json', autostart=False)
                root.update()
                for view, button in app.dashboard.nav.items():
                    app.dashboard.show(view)
                    root.update()
                    images = [button.itemcget(item, 'image') for item in button.find_all() if button.type(item) == 'image']
                    self.assertEqual(len(images), 1, view)
                    self.assertEqual(int(root.tk.call('image', 'width', images[0])), 20)
                    self.assertEqual(int(root.tk.call('image', 'height', images[0])), 20)
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
