"""Consulta e execução do winget, sem dependências da interface gráfica."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata

from att_storage import write_json


NO_APPLICATIONS = 0x8A150014
NOT_APPLICABLE = 0x8A15002B
REBOOT_REQUIRED = 0x8A150109
ALREADY_INSTALLED = 0x8A15010D
DOWNLOAD_FAILED = 0x8A150008
HTTP_NOT_FOUND = 0x80190194
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+\-]*\Z")
# Mensagens do winget que também podem acompanhar saída 0 sem tabela.
EMPTY_MESSAGES = {
    "No installed package found matching input criteria.",
    "Nenhum pacote instalado foi encontrado que corresponda aos critérios de entrada.",
}

# HRESULTs do AppInstallerErrors.h; o texto original do winget é mantido abaixo.
FAILURE_HINTS = {
    DOWNLOAD_FAILED: 'Falha ao baixar o instalador. Confira a conexão e a disponibilidade do servidor do programa.',
    HTTP_NOT_FOUND: ('Arquivo do instalador não encontrado no servidor (HTTP 404). '
                     'O endereço fornecido pelo catálogo pode estar desatualizado ou indisponível. '
                     'Execute winget source update em um terminal e tente novamente somente este pacote. '
                     'Se persistir, o link precisa ser corrigido pelo catálogo ou distribuidor.'),
    0x8A15006B: 'Falha ao baixar uma dependência exigida pelo programa.',
    0x8A150107: 'O instalador informou que está sem conexão de rede.',
    0x80072EE2: 'O download excedeu o tempo de resposta. Confira a conexão e tente novamente este pacote.',
    0x80072EE7: 'O endereço do servidor não foi encontrado. Confira a conexão e o DNS.',
    0x80072EFD: 'Não foi possível conectar ao servidor de download.',
    0x8A150102: 'Outro instalador está em andamento. Aguarde a conclusão antes de tentar novamente este pacote.',
    0x80070652: 'O Windows já está executando outra instalação. Aguarde antes de tentar novamente este pacote.',
    0x8A150041: 'O pacote exige aceitação de termos. Revise a solicitação em um terminal do winget.',
    0x8A150046: 'A origem exige aceitação de termos. Revise a solicitação em um terminal do winget.',
    0x8A150076: 'A origem exige autenticação interativa pelo winget.',
    0x8A150011: 'O arquivo baixado falhou na verificação de integridade. Confira a origem e o distribuidor.',
    0x8A15002E: 'O tamanho do arquivo baixado não corresponde ao esperado pelo winget.',
    0x8A15005E: 'O certificado recebido não corresponde ao esperado pelo winget.',
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
    write_json(target, {"auto_update": bool(enabled)})


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

    @staticmethod
    def _upgrade_arguments(package):
        if (package.blocked or not IDENTIFIER.fullmatch(package.identifier)
                or not IDENTIFIER.fullmatch(package.source)
                or "..." in package.identifier or "..." in package.source):
            raise WingetError("Pacote sem identificação segura para atualização.")
        return [
            "upgrade", "--id", package.identifier, "--exact", "--source", package.source,
        ]

    def upgrade(self, package):
        arguments = self._upgrade_arguments(package)
        code, output = self.run([*arguments, "--silent", "--disable-interactivity"])
        return self._upgrade_result(package, code, output, 'silencioso')

    def upgrade_interactive(self, package):
        """Terminal real, com entrada disponível; aguarda antes do próximo pacote."""
        self._upgrade_arguments(package)
        # Somente argumentos validados; aspas simples protegem inclusive caminhos
        # temporários com espaços ou apóstrofos. Não usa shell=True nem elevação.
        def quote(value):
            return "'" + value.replace("'", "''") + "'"

        command = f"& winget upgrade --id {quote(package.identifier)} --exact --source {quote(package.source)}"
        with tempfile.TemporaryDirectory(prefix='att-winget-') as folder:
            log = Path(folder) / 'output.txt'
            # Não redirecionar stdout: versões do winget exigem entrada E saída
            # ligadas a um console para certas perguntas. Após concluir, tenta
            # guardar as últimas 200 linhas do buffer visível. A coleta pode não
            # ser suportada pelo host e nunca substitui o código do instalador.
            script = f"""
$global:LASTEXITCODE = 1
{command}
$attCode = $LASTEXITCODE
try {{
    $attUI = $Host.UI.RawUI
    $attBottom = [Math]::Min($attUI.CursorPosition.Y, $attUI.BufferSize.Height - 1)
    $attTop = [Math]::Max(0, $attBottom - 199)
    $attRight = $attUI.BufferSize.Width - 1
    $attRect = [System.Management.Automation.Host.Rectangle]::new(0, $attTop, $attRight, $attBottom)
    $attBuffer = $attUI.GetBufferContents($attRect)
    $attLines = [System.Collections.Generic.List[string]]::new()
    for ($attRow = 0; $attRow -lt $attBuffer.GetLength(0); $attRow++) {{
        $attLine = [System.Text.StringBuilder]::new()
        for ($attCol = 0; $attCol -lt $attBuffer.GetLength(1); $attCol++) {{
            [void]$attLine.Append($attBuffer[$attRow, $attCol].Character)
        }}
        [void]$attLines.Add($attLine.ToString().TrimEnd())
    }}
    [System.IO.File]::WriteAllLines({quote(str(log))}, $attLines, [System.Text.UTF8Encoding]::new($false))
}} catch {{}}
if ($attCode -ne 0) {{
    Write-Host ('ATT: winget terminou com codigo ' + $attCode)
    [void](Read-Host 'Pressione Enter para retornar ao ATT')
}}
exit $attCode
"""
            try:
                result = subprocess.run(
                    ['powershell.exe', '-NoProfile', '-Command', script],
                    creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0x10),
                )
            except FileNotFoundError as error:
                raise WingetError('PowerShell não encontrado. Use o modo silencioso ou confira a instalação do Windows PowerShell.') from error
            try:
                raw = log.read_bytes()
                encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
                output = raw.decode(encoding, errors='replace').strip()
            except OSError:
                output = 'O host não disponibilizou o texto do terminal. Consulte a mensagem na janela do PowerShell.'
        return self._upgrade_result(package, result.returncode & 0xFFFFFFFF, output, 'PowerShell com janela')

    @staticmethod
    def _upgrade_result(package, code, output, mode):
        command = f'winget upgrade --id {package.identifier} --exact --source {package.source}'
        executed = command + (' --silent --disable-interactivity' if mode == 'silencioso' else '')
        context = f'Modo: {mode}\nComando executado: {executed}\nComando para comparar no PowerShell: {command}\n'
        if code == 0:
            return "Atualizado", context + output
        if code == REBOOT_REQUIRED:
            return "Reinício necessário", context + output
        if code in (NOT_APPLICABLE, ALREADY_INSTALLED):
            return "Sem atualização", context + output
        hint_code = code
        if code == DOWNLOAD_FAILED and re.search(r'\b0x80190194\b', output, flags=re.IGNORECASE):
            hint_code = HTTP_NOT_FOUND
        hint = FAILURE_HINTS.get(hint_code, 'O winget não concluiu a atualização deste pacote. Consulte o retorno abaixo.')
        details = (f'Pacote: {package.identifier}\nOrigem: {package.source}\nCódigo 0x{code:08X}\n'
                   f'{context}{hint}\n\nRetorno do winget:\n{output[-12000:] or "Nenhuma mensagem retornada."}')
        return "Falhou", details
