"""Histórico local, separado das preferências do usuário."""
from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

from att_backend import config_path
from att_storage import data_lock, write_json


class ActivityStore:
    def __init__(self, preference_path=None):
        self.entries = []
        self.last_check = ''
        self.warning = ''
        self.path = None
        self.writable = True
        self._pending_entries = []
        self._pending_check = None
        try:
            target = Path(preference_path) if preference_path is not None else config_path()
            self.path = target.with_name('history.json')
            with data_lock(self.path.with_suffix('.lock')):
                data = self._read()
            self.last_check = data['last_check']
            self.entries = data['entries'][-1000:]
        except (OSError, ValueError, TypeError) as error:
            self._unavailable(error)

    def _read(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {'entries': [], 'last_check': ''}
        if not isinstance(data, dict) or not isinstance(data.get('entries'), list):
            raise ValueError('Histórico inválido')
        last_check = data.get('last_check', '')
        if not isinstance(last_check, str):
            raise ValueError('Data de verificação inválida')
        if last_check:
            datetime.fromisoformat(last_check)
        for entry in data['entries']:
            if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in (
                'time', 'name', 'identifier', 'source', 'installed', 'available', 'status', 'details'
            )):
                raise ValueError('Registro de histórico inválido')
            if 'event_id' in entry and not isinstance(entry['event_id'], str):
                raise ValueError('Identidade de registro inválida')
            datetime.fromisoformat(entry['time'])
        return {'entries': data['entries'], 'last_check': last_check}

    def _unavailable(self, error):
        self.writable = False
        self.warning = f'Não foi possível carregar o histórico: {error}. O arquivo será preservado.'

    def _save(self):
        if not self.writable or self.path is None:
            raise OSError(self.warning or 'Histórico indisponível')
        with data_lock(self.path.with_suffix('.lock')):
            self._commit()

    def _commit(self):
        try:
            current = self._read()
        except (OSError, ValueError, TypeError) as error:
            self._unavailable(error)
            raise OSError(self.warning) from error
        known = {entry['event_id'] for entry in current['entries'] if 'event_id' in entry}
        entries = current['entries'] + [entry for entry in self._pending_entries
                                        if entry['event_id'] not in known]
        entries.sort(key=lambda entry: datetime.fromisoformat(entry['time']).timestamp())
        entries = entries[-1000:]
        checks = [value for value in (current['last_check'], self._pending_check) if value]
        last_check = max(checks, key=lambda value: datetime.fromisoformat(value).timestamp()) if checks else ''
        write_json(self.path, {'last_check': last_check, 'entries': entries})
        self.entries = entries
        self.last_check = last_check
        self._pending_entries.clear()
        self._pending_check = None

    def checked(self):
        self.last_check = datetime.now().astimezone().isoformat(timespec='seconds')
        self._pending_check = self.last_check
        self._save()

    def record(self, package, status, details):
        entry = dict(event_id=uuid4().hex, time=datetime.now().astimezone().isoformat(timespec='microseconds'),
                     name=package.name, identifier=package.identifier, source=package.source,
                     installed=package.installed, available=package.available,
                     status=status, details=details[-16000:])
        self._pending_entries.append(entry)
        self.entries = (self.entries + [entry])[-1000:]
        self._save()
