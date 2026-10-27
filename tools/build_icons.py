"""Gera máscaras de ícones. Só a geração requer Pillow; o ATT usa a stdlib.

Execute da raiz do projeto: python tools/build_icons.py
"""
import base64
from io import BytesIO
from math import cos, pi, sin
from pathlib import Path
import zlib

from PIL import Image, ImageDraw


NAMES = ('grid', 'download', 'arrow', 'clock', 'apps', 'sliders', 'settings', 'refresh', 'search', 'info',
         'dot', 'checkbox', 'checked', 'minus', 'chevron', 'toggle_track')
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
        for x, y in ((1.5, 1.5), (9.5, 1.5), (1.5, 9.5), (9.5, 9.5)):
            draw.rounded_rectangle(coordinates((x, y, x+5, y+5)), radius=scale, fill=255)
    elif name in ('download', 'arrow'):
        line(8, 1, 8, 11); line(4, 7, 8, 11, 12, 7)
        if name == 'download':
            line(2, 12, 2, 15, 14, 15, 14, 12)
    elif name == 'clock':
        ellipse((1, 1, 15, 15)); line(8, 4, 8, 8, 11, 10)
    elif name == 'apps':
        draw.rounded_rectangle(coordinates((1, 2, 15, 14)), radius=round(1.7*scale), outline=255, width=stroke)
        line(1, 6, 15, 6)
    elif name == 'sliders':
        for y, x in ((3, 5), (8, 11), (13, 6)):
            line(1, y, 15, y)
            draw.ellipse(coordinates((x-2, y-2, x+2, y+2)), fill=0, outline=255, width=stroke)
    elif name == 'settings':
        points = []
        for tooth in range(8):
            for offset, radius in ((-17, 5.2), (-10, 6.9), (10, 6.9), (17, 5.2)):
                angle = (tooth*45 + offset)*pi/180
                points.append((round((8 + radius*cos(angle))*scale), round((8 + radius*sin(angle))*scale)))
        draw.line(points + [points[0]], fill=255, width=stroke, joint='curve')
        ellipse((5.7, 5.7, 10.3, 10.3))
    elif name == 'refresh':
        draw.arc(coordinates((2, 2, 14, 14)), start=200, end=340, fill=255, width=stroke)
        draw.arc(coordinates((2, 2, 14, 14)), start=20, end=160, fill=255, width=stroke)
        line(14, 2, 14, 6, 10, 6)
        line(2, 14, 2, 10, 6, 10)
    elif name == 'search':
        ellipse((1, 1, 11, 11)); line(10, 10, 15, 15)
    elif name == 'info':
        ellipse((1, 1, 15, 15)); line(8, 8, 8, 12)
        draw.ellipse(coordinates((7.2, 4, 8.8, 5.6)), fill=255)
    elif name == 'dot':
        draw.ellipse((0, 0, size*8-1, size*8-1), fill=255)
    elif name in ('checkbox', 'checked'):
        draw.rounded_rectangle(coordinates((1.5, 1.5, 14.5, 14.5)), radius=round(2*scale), outline=255, width=stroke)
        if name == 'checked':
            line(4.5, 8, 7, 10.5, 11.5, 5.5)
    elif name == 'minus':
        line(4, 8, 12, 8)
    elif name == 'chevron':
        line(4, 6, 8, 10, 12, 6)
    elif name == 'toggle_track':
        draw.rounded_rectangle(coordinates((0.5, 4, 14.5, 12)), radius=round(4*scale), fill=255)
    return image.resize((size, size), Image.Resampling.LANCZOS).tobytes()


def app_image(size):
    """O mesmo A da identidade do painel, sem depender de fontes instaladas."""
    scale = size*8/16
    image = Image.new('RGBA', (size*8, size*8))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size*8-1, size*8-1), radius=round(3.5*scale), fill='#63DDA1')
    def polygon(points, color):
        draw.polygon([(round(x*scale), round(y*scale)) for x, y in points], fill=color)
    polygon(((3.2, 13), (6.7, 3), (9.3, 3), (12.8, 13), (10.4, 13),
             (9.6, 10.6), (6.4, 10.6), (5.6, 13)), '#123C30')
    polygon(((7, 8.5), (9, 8.5), (8, 5.4)), '#63DDA1')
    output = BytesIO()
    image.resize((size, size), Image.Resampling.LANCZOS).save(output, format='PNG')
    return base64.b64encode(output.getvalue()).decode('ascii')


def main():
    target = Path(__file__).resolve().parents[1] / 'att_icon_data.py'
    lines = ['"""Máscaras geradas por tools/build_icons.py; não editar manualmente."""', 'MASKS = {']
    for name in NAMES:
        sizes = (4, 10, 12) if name == 'dot' else (32,) if name == 'toggle_track' else SIZES
        for size in sizes:
            data = base64.b85encode(zlib.compress(mask(name, size), 9)).decode('ascii')
            lines.append(f'    ({name!r}, {size}): {data!r},')
    lines.extend(['}', '', 'BRAND_IMAGES = {'])
    for size in (16, 32):
        lines.append(f'    {size}: {app_image(size)!r},')
    lines.append('}\n')
    target.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
