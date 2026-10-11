# -*- coding: utf-8 -*-
"""归档者新招式/减益的占位贴图（品红底或透明）。"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PROJ = os.path.join(ROOT, "WastelandSoul", "Content", "Projectiles", "Archivist")
BUFF = os.path.join(ROOT, "WastelandSoul", "Content", "Buffs")


def save(path, image):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print(path, image.size)


def circle(size, fill, outline, width=2):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    pad = 1
    draw.ellipse((pad, pad, size - 1 - pad, size - 1 - pad), fill=fill, outline=outline, width=width)
    return image


def blob(size, fill, outline):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((2, 2, size - 3, size - 3), fill=fill, outline=outline, width=1)
    return image


def pillar():
    image = Image.new("RGBA", (80, 240), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for y in range(240):
        fade = 1.0 - y / 260.0
        color = (int(210 * fade), int(90 * fade), int(28 * fade), int(220 * fade))
        draw.line((8, y, 71, y), fill=color)
    draw.rectangle((10, 0, 69, 239), outline=(120, 40, 16, 255))
    return image


def seed():
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((3, 2, 12, 14), fill=(210, 90, 160, 255), outline=(120, 40, 90, 255))
    draw.point((8, 6), fill=(230, 160, 190, 255))
    return image


def hidden():
    return Image.new("RGBA", (8, 8), (0, 0, 0, 0))


def buff_wing():
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(4, 22), (10, 6), (16, 18)], fill=(200, 90, 40, 255), outline=(90, 30, 16, 255))
    draw.polygon([(28, 22), (22, 6), (16, 18)], fill=(200, 90, 40, 255), outline=(90, 30, 16, 255))
    return image


def buff_bubble():
    return circle(32, (90, 170, 210, 90), (70, 140, 180, 255), 2)


def main():
    save(os.path.join(PROJ, "ArchivistFireball.png"), blob(28, (220, 110, 36, 255), (140, 50, 16, 255)))
    save(os.path.join(PROJ, "ArchivistMiniFireball.png"), blob(14, (230, 130, 40, 255), (150, 60, 20, 255)))
    save(os.path.join(PROJ, "ArchivistFirePillar.png"), pillar())
    save(os.path.join(PROJ, "ArchivistVenomSeed.png"), seed())
    save(os.path.join(PROJ, "ArchivistBubble.png"), circle(52, (80, 170, 210, 80), (60, 140, 180, 230), 3))
    save(os.path.join(PROJ, "ArchivistBubbleStorm.png"), hidden())
    save(os.path.join(PROJ, "ArchivistArenaMist.png"), hidden())
    save(os.path.join(BUFF, "ArchivistWingBurn.png"), buff_wing())
    save(os.path.join(BUFF, "ArchivistBubbleTrap.png"), buff_bubble())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
