"""Inicialização de renderização nativa antes da primeira janela Tk."""
import ctypes
import sys


def enable_dpi_awareness():
    """Evita ampliação por bitmap; respeita um manifesto já configurado."""
    if sys.platform != 'win32':
        return False
    try:
        result = ctypes.windll.shcore.SetProcessDpiAwareness(1) & 0xFFFFFFFF
        if result in (0, 0x80070005):  # S_OK ou configuração existente (E_ACCESSDENIED)
            return True
    except (AttributeError, OSError):
        pass
    try:
        return bool(ctypes.windll.user32.SetProcessDPIAware())
    except (AttributeError, OSError):
        return False
