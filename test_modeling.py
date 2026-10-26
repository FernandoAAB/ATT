"""Contratos públicos e cenários de estresse do domínio ATT."""
import json
from pathlib import Path
import subprocess
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from att_backend import NO_APPLICATIONS, Package, WingetClient
from att_history import ActivityStore
from att_widgets import UpdateTable


class WingetContractTests(unittest.TestCase):
    def test_package_removed_after_query_is_failure(self):
        package = Package('Editor', 'Acme.Editor', '1', '2', 'winget')
        response = subprocess.CompletedProcess(
            ['winget'], NO_APPLICATIONS - 2**32,
            stdout='No installed package found matching input criteria.', stderr='')
        with patch('att_backend.subprocess.run', return_value=response):
            status, details = WingetClient().upgrade(package)
        self.assertEqual(status, 'Falhou')
        self.assertIn('0x8A150014', details)

    def test_inventory_without_origin_keeps_available_version(self):
        for heading in ('Available', 'Disponível'):
            with self.subTest(heading=heading):
                output = (
                    f'Name    Id              Version {heading}\n'
                    '------------------------------------------\n'
                    'Firefox Mozilla.Firefox 1.0     2.0\n')
                response = subprocess.CompletedProcess(['winget'], 0, stdout=output, stderr='')
                with patch('att_backend.subprocess.run', return_value=response):
                    package = WingetClient().list_installed()[0]
                self.assertEqual(package.available, '2.0')
                self.assertEqual(package.source, '')

    def test_same_identifier_from_two_origins_stays_distinct(self):
        output = (
            'Name   Id          Version Available Source\n'
            '-------------------------------------------\n'
            'Editor Acme.Editor 1.0     2.0       winget\n'
            'Editor Acme.Editor 1.0     3.0       company\n')
        result = subprocess.CompletedProcess(['winget'], 0, stdout=output, stderr='')
        with patch('att_backend.subprocess.run', return_value=result):
            packages = WingetClient().discover()
        self.assertEqual([p.source for p in packages], ['winget', 'company'])
        self.assertFalse(any(p.blocked for p in packages))
        result = subprocess.CompletedProcess(['winget'], 0, stdout='ok', stderr='')
        with patch('att_backend.subprocess.run', return_value=result) as command:
            WingetClient().upgrade(packages[1])
        self.assertEqual(command.call_args.args[0], [
            'winget', 'upgrade', '--id', 'Acme.Editor', '--exact', '--source', 'company',
            '--silent', '--disable-interactivity'])

    def test_download_failure_has_package_diagnostic_and_original_message(self):
        response = subprocess.CompletedProcess(['winget'], 0x8A150008,
                                               stdout='HTTP 503: servidor indisponível', stderr='')
        with patch('att_backend.subprocess.run', return_value=response):
            status, details = WingetClient().upgrade(Package('Editor', 'Acme.Editor', '1', '2', 'winget'))
        self.assertEqual(status, 'Falhou')
        self.assertIn('Acme.Editor', details)
        self.assertIn('0x8A150008', details)
        self.assertIn('baixar', details)
        self.assertIn('HTTP 503', details)

    def test_epson_404_explains_missing_file_and_source_refresh(self):
        output = ('Baixando https://download.epson-europe.com/pub/download/6741/epson674187eu.exe\n'
                  'Download request status is not success.\n0x80190194 : Não encontrado (404).')
        for code in (0x80190194, 0x8A150008):
            with self.subTest(code=code):
                response = subprocess.CompletedProcess(['winget'], code, stdout=output, stderr='')
                with patch('att_backend.subprocess.run', return_value=response):
                    status, details = WingetClient().upgrade(
                        Package('EpsonNet Print', 'EPSON.EpsonNetPrint', '3.1.0', '3.3.1', 'winget'))
                self.assertEqual(status, 'Falhou')
                self.assertIn('HTTP 404', details)
                self.assertIn('winget source update', details)
                self.assertIn('EPSON.EpsonNetPrint', details)
                self.assertIn('0x80190194', details)

    def test_known_installer_failures_keep_different_diagnostics(self):
        for code, expected in ((0x8A150102, 'Outro instalador'),
                               (0x8A150041, 'termos'),
                               (0x8A150011, 'integridade')):
            with self.subTest(code=code):
                response = subprocess.CompletedProcess(['winget'], code, stdout='Detalhe original', stderr='')
                with patch('att_backend.subprocess.run', return_value=response) as command:
                    status, details = WingetClient().upgrade(Package('Editor', 'Acme.Editor', '1', '2', 'winget'))
                self.assertEqual(status, 'Falhou')
                self.assertIn(expected, details)
                self.assertIn('Detalhe original', details)
                self.assertNotIn('--ignore-security-hash', command.call_args.args[0])
                self.assertNotIn('--accept-package-agreements', command.call_args.args[0])


class HistoryContractTests(unittest.TestCase):
    def test_history_retains_latest_thousand_attempts_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            preferences = Path(directory) / 'config.json'
            history = Path(directory) / 'history.json'
            entries = [dict(time='2026-10-23T12:00:00-03:00', name=f'Programa {index}',
                            identifier=f'Acme.App{index}', source='winget', installed='1',
                            available='2', status='Atualizado', details='ok')
                       for index in range(1000)]
            history.write_text(json.dumps({'entries': entries, 'last_check': ''}), encoding='utf-8')
            ActivityStore(preferences).record(Package('Novo', 'Acme.New', '1', '2', 'winget'), 'Falhou', 'Sem acesso')
            restored = ActivityStore(preferences)
            self.assertEqual(len(restored.entries), 1000)
            self.assertEqual(restored.entries[0]['identifier'], 'Acme.App1')
            self.assertEqual(restored.entries[-1]['identifier'], 'Acme.New')
            self.assertEqual(restored.entries[-1]['status'], 'Falhou')


class TableInteractionTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest('Interface requer tela ou Xvfb')
        self.root.geometry('500x150')
        self.table = UpdateTable(self.root)
        self.table.pack(fill='both', expand=True)
        for key in ('primeiro', 'segundo', 'terceiro', 'quarto', 'quinto'):
            self.table.insert('', 'end', iid=key,
                              values=('[ ]', key, '1', '2', 'Pendente'))
        self.root.update()

    def tearDown(self):
        if hasattr(self, 'table'):
            self.root.destroy()

    def test_first_down_key_focuses_first_program(self):
        self.table.focus_force()
        self.root.update()
        self.table.event_generate('<KeyPress-Down>')
        self.root.update()
        self.assertEqual(self.table.selection(), ('primeiro',))

    def test_empty_space_below_drawn_rows_has_no_program(self):
        self.assertEqual(self.table.identify_row(self.table.winfo_height() - 1), '')


if __name__ == '__main__':
    unittest.main()
