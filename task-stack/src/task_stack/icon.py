from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


_SIZE = 64
_BG_ACTIVE = (70, 130, 180)   # steel blue — tasks present
_BG_EMPTY = (120, 120, 120)   # grey — no tasks
_FG = (255, 255, 255)


def make_icon(count: int) -> Image.Image:
    color = _BG_ACTIVE if count > 0 else _BG_EMPTY
    img = Image.new("RGBA", (_SIZE, _SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, _SIZE - 1, _SIZE - 1], fill=color)

    label = str(min(count, 99)) if count > 0 else ""
    if label:
        font_size = 36 if len(label) == 1 else 26
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((_SIZE - w) / 2 - bbox[0], (_SIZE - h) / 2 - bbox[1]),
            label,
            font=font,
            fill=_FG,
        )
    return img
