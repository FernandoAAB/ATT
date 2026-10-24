"""Histórico local, separado das preferências do usuário."""
from datetime import datetime
import json
from pathlib import Path

from att_backend import config_path


class ActivityStore:
    def __init__(self, preference_path=None):
        self.entries = []
        self.last_check = ""
        self.warning = ""
        self.path = None
        self.writable = True
        try:
            self.path = (Path(preference_path) if preference_path is not None else config_path()).with_name('history.json')
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or not isinstance(data.get('entries'), list):
                raise ValueError('Histórico inválido')
            self.last_check = data.get('last_check', '')
            if not isinstance(self.last_check, str):
                raise ValueError('Data de verificação inválida')
            if self.last_check:
                datetime.fromisoformat(self.last_check)
            for entry in data['entries']:
                if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in (
                    'time', 'name', 'identifier', 'source', 'installed', 'available', 'status', 'details'
                )):
                    raise ValueError('Registro de histórico inválido')
                datetime.fromisoformat(entry['time'])
            self.entries = data['entries'][-1000:]
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as error:
            self.writable = False
            self.last_check = ''
            self.warning = f'Não foi possível carregar o histórico: {error}. O arquivo será preservado.'

    def _save(self):
        if not self.writable or self.path is None:
            raise OSError(self.warning or 'Histórico indisponível')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        try:
            temporary.write_text(json.dumps({'last_check': self.last_check, 'entries': self.entries},
                                           ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def checked(self):
        self.last_check = datetime.now().astimezone().isoformat(timespec='seconds')
        self._save()

    def record(self, package, status, details):
        self.entries.append(dict(time=datetime.now().astimezone().isoformat(timespec='seconds'),
                                 name=package.name, identifier=package.identifier, source=package.source,
                                 installed=package.installed, available=package.available,
                                 status=status, details=details[-16000:]))
        self.entries = self.entries[-1000:]
        self._save()
