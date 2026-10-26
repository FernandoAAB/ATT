"""Gera máscaras de ícones. Só a geração requer Pillow; o ATT usa a stdlib.

Execute da raiz do projeto: python tools/build_icons.py
"""
import base64
from pathlib import Path
import zlib

from PIL import Image, ImageDraw


NAMES = ('grid', 'download', 'arrow', 'clock', 'apps', 'sliders', 'settings', 'refresh', 'search', 'info')
SIZES = (12, 15, 16, 20)


def mask(name, size):
    scale = size * 8 / 16
    image = Image.new('L', (size * 8, size * 8))
    draw = ImageDraw.Draw(image)
    stroke = max(1, round(1.6 * scale))

    def coordinates(values):
        return tuple(round(value * scale) for value in values)

    def line(*values):
        draw.line(coordinates(values), fill=255, width=stroke, joint='curve')

    def ellipse(bounds, fill=None):
        draw.ellipse(coordinates(bounds), fill=fill, outline=255, width=stroke)

    if name == 'grid':
        for x, y in ((1, 1), (9, 1), (1, 9), (9, 9)):
            draw.rounded_rectangle(coordinates((x, y, x+5, y+5)), radius=scale, fill=255)
    elif name in ('download', 'arrow'):
        line(8, 1, 8, 11); line(4, 7, 8, 11, 12, 7)
        if name == 'download':
            line(2, 12, 2, 14, 14, 14, 14, 12)
    elif name == 'clock':
        ellipse((1, 1, 15, 15)); line(8, 4, 8, 8, 11, 10)
    elif name == 'apps':
        for y in (3, 8, 13):
            line(1, y, 15, y)
    elif name == 'sliders':
        for y, x in ((3, 5), (8, 11), (13, 6)):
            line(1, y, 15, y)
            draw.ellipse(coordinates((x-2, y-2, x+2, y+2)), fill=0, outline=255, width=stroke)
    elif name == 'settings':
        ellipse((2, 2, 14, 14)); ellipse((6, 6, 10, 10))
        for values in ((8, 0, 8, 2), (8, 14, 8, 16), (0, 8, 2, 8), (14, 8, 16, 8)):
            line(*values)
    elif name == 'refresh':
        draw.arc(coordinates((2, 2, 14, 14)), start=40, end=325, fill=255, width=stroke)
        line(10, 1, 14, 2, 13, 6)
    elif name == 'search':
        ellipse((1, 1, 11, 11)); line(10, 10, 15, 15)
    elif name == 'info':
        ellipse((1, 1, 15, 15)); line(8, 7, 8, 12)
        ellipse((7.3, 3.5, 8.7, 4.9), fill=255)
    return image.resize((size, size), Image.Resampling.LANCZOS).tobytes()


def main():
    target = Path(__file__).resolve().parents[1] / 'att_icon_data.py'
    lines = ['"""Máscaras geradas por tools/build_icons.py; não editar manualmente."""', 'MASKS = {']
    for name in NAMES:
        for size in SIZES:
            data = base64.b85encode(zlib.compress(mask(name, size), 9)).decode('ascii')
            lines.append(f'    ({name!r}, {size}): {data!r},')
    lines.append('}\n')
    target.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
