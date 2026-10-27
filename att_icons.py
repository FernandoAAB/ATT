"""Ícones PNG suavizados no tamanho final, sem dependências de execução."""
import base64
import struct
import tkinter as tk
import zlib

from att_icon_data import BRAND_IMAGES, MASKS


def app_images(master):
    return tuple(tk.PhotoImage(master=master, data=BRAND_IMAGES[size], format='png') for size in (32, 16))


def image_for(canvas, name, color, size):
    # O cache pertence ao widget: preserva PhotoImage e é liberado com a janela.
    cache = getattr(canvas, '_icon_images', None)
    if cache is None:
        cache = canvas._icon_images = {}
    key = (name, color, size)
    if key not in cache:
        mask = zlib.decompress(base64.b85decode(MASKS[(name, size)]))
        rgb = bytes(component // 257 for component in canvas.winfo_rgb(color))
        rows = b''.join(b'\0' + b''.join(rgb + bytes((alpha,)) for alpha in mask[y*size:(y+1)*size])
                        for y in range(size))

        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
        cache[key] = tk.PhotoImage(master=canvas, data=png, format='png')
    return cache[key]
