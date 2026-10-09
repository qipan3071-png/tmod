# -*- coding: utf-8 -*-
"""Dump a vanilla Terraria texture from .xnb to PNG, tolerating this build's headers.

`read_vanilla_tex.py` already parses the header for *sizes*; this adds decompression
plus pixel decoding so an actual vanilla armour sheet can be measured (box sizes,
per-row widths, palette) -- which is how the worn-armour art should be derived
instead of guessing.

The header layout differs per build, so the compressed block start is found by
**trying every plausible offset** and keeping the one that decompresses to the
declared length. That is cheap and removes all guesswork.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from read_xnb import lz4_decompress, read_7bit_int, read_string  # noqa: E402

VANILLA = r"E:\steam\steamapps\common\Terraria\Content\Images"

SURFACE_COLOR = 0
SURFACE_DXT3 = 5
SURFACE_DXT5 = 6


def load_content(path):
    with open(path, "rb") as handle:
        data = handle.read()

    if data[:3] != b"XNB":
        raise ValueError("not XNB")

    flags = data[5]

    if not flags & 0x80:
        return data[6:]

    # try every offset 6..20 for the (decompressed, compressed) pair
    for offset in range(6, 21):
        if offset + 8 > len(data):
            break

        decompressed, compressed = struct.unpack_from("<ii", data, offset)

        if not (0 < decompressed < 64 * 1024 * 1024) or not (0 < compressed <= len(data)):
            continue

        for start in (offset + 8, offset + 9):
            if start + compressed > len(data) + 16:
                continue

            try:
                content = lz4_decompress(data[start:start + compressed], decompressed)
            except Exception:  # noqa: BLE001 - 探测式解压，失败是正常的
                continue

            if len(content) == decompressed:
                return content

    raise ValueError("LZ4 解压失败（所有候选偏移都不行）")


def parse_texture(content):
    pos = 0
    readers, pos = read_7bit_int(content, pos)

    for _ in range(readers):
        _name, pos = read_string(content, pos)
        pos += 4

    _shared, pos = read_7bit_int(content, pos)
    _type_id, pos = read_7bit_int(content, pos)
    fmt, width, height, mips, _size = struct.unpack_from("<iiiii", content, pos)
    return fmt, width, height, pos + 20


def decode(content, path):
    from PIL import Image

    fmt, width, height, data_pos = parse_texture(content)
    data = content[data_pos:]

    if fmt == SURFACE_COLOR:
        pixels = bytearray(data[:width * height * 4])
    else:
        raise ValueError("surface format %d 暂不支持" % fmt)

    if len(pixels) < width * height * 4:
        raise ValueError("像素数据不足")

    return Image.frombytes("RGBA", (width, height), bytes(pixels))


def main():
    args = sys.argv[1:]
    prefix = args[0]
    indexes = args[1:]
    out_dir = r"E:\开发\.tmp-3d\vanilla"
    os.makedirs(out_dir, exist_ok=True)

    for index in indexes:
        name = "%s_%s.xnb" % (prefix, index)
        path = os.path.join(VANILLA, name)

        if not os.path.exists(path):
            print("%-24s MISSING" % name)
            continue

        try:
            image = decode(load_content(path), path)
        except Exception as error:  # noqa: BLE001 - 诊断脚本
            print("%-24s FAIL %s" % (name, error))
            continue

        out = os.path.join(out_dir, name.replace(".xnb", ".png"))
        image.save(out)
        print("%-24s OK %dx%d -> %s" % (name, image.width, image.height, out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
