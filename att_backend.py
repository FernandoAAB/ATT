"""Consulta e execução do winget, sem dependências da interface gráfica."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata


NO_APPLICATIONS = 0x8A150014
NOT_APPLICABLE = 0x8A15002B
REBOOT_REQUIRED = 0x8A150109
ALREADY_INSTALLED = 0x8A15010D
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+\-]*\Z")
# Mensagens do winget que também podem acompanhar saída 0 sem tabela.
EMPTY_MESSAGES = {
    "No installed package found matching input criteria.",
    "Nenhum pacote instalado foi encontrado que corresponda aos critérios de entrada.",
}


class WingetError(RuntimeError):
    pass


@dataclass
class Package:
    name: str
    identifier: str
    installed: str
    available: str
    source: str
    blocked: str = ""


def config_path():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise OSError("A pasta LOCALAPPDATA do usuário não está disponível.")
    return Path(base) / "ATT" / "config.json"


def load_preferences(path=None):
    try:
        target = Path(path) if path is not None else config_path()
        with target.open(encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or type(data.get("auto_update")) is not bool:
            raise ValueError("formato de configuração inválido")
        return data["auto_update"], ""
    except FileNotFoundError:
        return False, ""
    except (OSError, ValueError) as error:
        return False, f"Não foi possível ler a preferência. Modo automático desativado. {error}"


def save_preferences(enabled, path=None):
    target = Path(path) if path is not None else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps({"auto_update": bool(enabled)}, indent=2), encoding="utf-8")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def _display_columns(text):
    """Espelha as colunas de terminal usadas pelo winget, inclusive caracteres largos."""
    result = []
    for char in text:
        if unicodedata.combining(char):
            if result:
                result[-1] += char
            continue
        result.append(char)
        if unicodedata.east_asian_width(char) in ("W", "F"):
            result.append("")
    return result


def parse_upgrades(output, installed=False):
    lines = ANSI.sub("", output).splitlines()
    packages = []
    recognized = False
    for index, line in enumerate(lines):
        if not re.fullmatch(r"\s*-{8,}\s*", line) or index == 0:
            continue
        header = lines[index - 1]
        headings = list(re.finditer(r"\S+", header))
        if len(headings) not in ((3, 4, 5) if installed else (5,)):
            headings = list(re.finditer(r"\S(?:.*?\S)?(?= {2,}|$)", header))
        if len(headings) not in ((3, 4, 5) if installed else (5,)):
            continue
        starts = [len(_display_columns(header[:match.start()])) for match in headings]
        recognized = True
        for row in lines[index + 1:]:
            if not row.strip() or row == header or re.fullmatch(r"\s*-{8,}\s*", row):
                break
            columns = _display_columns(row)
            cells = ["".join(columns[start:end]).strip()
                     for start, end in zip(starts, starts[1:] + [len(columns)])]
            # Rodapés e avisos do winget não ocupam as quatro primeiras colunas.
            required = 3 if installed else 4
            if len(columns) <= starts[required - 1] or not all(cells[:required]):
                break
            if len(cells) == 3:
                cells.extend(["", ""])
            elif len(cells) == 4:
                fourth_heading = headings[3].group().strip().casefold()
                if fourth_heading in ("available", "disponível"):
                    cells.append("")
                else:
                    cells.insert(3, "")
            name, identifier, installed_version, available, source = cells
            blocked = ""
            if (not IDENTIFIER.fullmatch(identifier) or not IDENTIFIER.fullmatch(source)
                    or "..." in identifier or "..." in source):
                blocked = "Identificador ou origem ausente, truncado ou inválido; consulte os detalhes."
            packages.append(Package(name, identifier, installed_version, available, source, blocked))
        break
    if not recognized or not packages:
        raise WingetError("A saída do winget não contém uma tabela de atualizações reconhecível.\n" + output)
    seen = set()
    duplicates = set()
    for package in packages:
        key = (package.identifier.casefold(), package.source.casefold())
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    for package in packages:
        if (package.identifier.casefold(), package.source.casefold()) in duplicates:
            package.blocked = "Identificador duplicado nesta origem; seleção ambígua."
    return packages


class WingetClient:
    def run(self, arguments, timeout=None):
        try:
            result = subprocess.run(
                ["winget", *arguments], capture_output=True,
                encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=timeout,
            )
        except FileNotFoundError as error:
            raise WingetError("winget não encontrado. Instale ou atualize o App Installer da Microsoft e verifique o PATH.") from error
        except subprocess.TimeoutExpired as error:
            raise WingetError("O winget demorou demais para consultar as atualizações. Tente novamente.") from error
        return result.returncode & 0xFFFFFFFF, (result.stdout + "\n" + result.stderr).strip()

    def discover(self):
        code, output = self.run(["upgrade", "--disable-interactivity"], timeout=180)
        if code in (NO_APPLICATIONS, NOT_APPLICABLE):
            return []
        if code != 0:
            raise WingetError(f"Falha na consulta (0x{code:08X}).\n{output}")
        if any(line.strip() in EMPTY_MESSAGES for line in ANSI.sub("", output).splitlines()):
            # Não descarte tabelas adicionais (por exemplo, pacotes fixados pelo usuário).
            if not re.search(r"(?m)^\s*-{8,}\s*$", output):
                return []
        return parse_upgrades(output)

    def list_installed(self):
        code, output = self.run(["list", "--disable-interactivity"], timeout=180)
        if code == NO_APPLICATIONS:
            return []
        if code != 0:
            raise WingetError(f"Falha ao listar aplicativos (0x{code:08X}).\n{output}")
        if any(line.strip() in EMPTY_MESSAGES for line in output.splitlines()):
            if not re.search(r"(?m)^\s*-{8,}\s*$", output):
                return []
        return parse_upgrades(output, installed=True)

    def upgrade(self, package):
        if (package.blocked or not IDENTIFIER.fullmatch(package.identifier)
                or not IDENTIFIER.fullmatch(package.source)
                or "..." in package.identifier or "..." in package.source):
            raise WingetError("Pacote sem identificação segura para atualização.")
        code, output = self.run([
            "upgrade", "--id", package.identifier, "--exact", "--source", package.source,
            "--silent", "--disable-interactivity",
        ])
        if code == 0:
            return "Atualizado", output
        if code == REBOOT_REQUIRED:
            return "Reinício necessário", output
        if code in (NOT_APPLICABLE, ALREADY_INSTALLED):
            return "Sem atualização", output
        return "Falhou", f"Código 0x{code:08X}\n{output}"
