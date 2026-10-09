# -*- coding: utf-8 -*-
"""把 Terraria 的 .xnb 贴图解成 PNG（XNA/MonoGame Texture2D）。

为什么自己写
------------
`tModLoader` 只提供命令行构建/启动，没有"把原版贴图导成 png"的开关，
而我们要用**原版玩家贴图**给方块人物上色（项目所有者明确允许使用原版素材，
只是不许把灾厄等第三方模组的本地文件改掉）。
所以这里直接解 XNB：LZ4 解压 → 读 Texture2D 头 → 按 surface format 还原像素。

实测（tModLoader 1.4.4.9 的 Content/Images）：
    'X','N','B','w',5,0x80, 0x7C, <解压后长度 int32>, <压缩长度 int32>, <LZ4 数据>
0x80 表示 LZ4 压缩；平台字节 'w' = Windows。

用法:
    python tools/decode_xnb.py <in.xnb> <out.png> [<in.xnb> <out.png> ...]
    python tools/decode_xnb.py --probe <in.xnb>
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from read_xnb import lz4_decompress, read_7bit_int, read_string  # noqa: E402

# XNA SurfaceFormat
SURFACE_COLOR = 0
SURFACE_DXT1 = 4
SURFACE_DXT3 = 5
SURFACE_DXT5 = 6

FORMAT_NAMES = {
    SURFACE_COLOR: "Color",
    SURFACE_DXT1: "Dxt1",
    SURFACE_DXT3: "Dxt3",
    SURFACE_DXT5: "Dxt5",
}


def load_content(path):
    """返回 XNB 里解压后的内容块。"""
    with open(path, "rb") as handle:
        data = handle.read()

    if data[:3] != b"XNB":
        raise ValueError("不是 XNB 文件：%s" % path)

    flags = data[5]

    # 字节序（实测 Player_1_4.xnb）：
    #   0..2 'XNB' | 3 平台 'w' | 4 版本 5 | 5 flags 0x80 | 6 0x7C（额外标志）
    #   7..10 解压后长度 | 11..14 压缩长度 | 15.. LZ4 数据
    # 早先按 6/10 读会整体错一位，LZ4 立刻报"offset 越界"。
    if flags & 0x80:
        decompressed, compressed = struct.unpack_from("<ii", data, 7)
        content = lz4_decompress(data[15:15 + compressed], decompressed)

        if len(content) != decompressed:
            raise ValueError("LZ4 解压长度不符：得到 %d，期望 %d"
                             % (len(content), decompressed))
    else:
        content = data[10:]

    return content


def parse_texture(content):
    """解析 Texture2D：返回 (surface_format, width, height, 像素数据区起点)。"""
    pos = 0
    readers, pos = read_7bit_int(content, pos)

    for _ in range(readers):
        _name, pos = read_string(content, pos)
        pos += 4  # reader version

    _shared, pos = read_7bit_int(content, pos)
    _type_id, pos = read_7bit_int(content, pos)

    fmt, width, height, mips, _size = struct.unpack_from("<iiiii", content, pos)
    pos += 20

    if mips > 1:
        raise ValueError("带 mipmap 的贴图暂不支持（mips=%d）" % mips)

    return fmt, width, height, pos


def decode_color(data, width, height):
    """SurfaceFormat.Color 是 32 位：XNA 里按 R,G,B,A 字节序存。"""
    pixels = bytearray(width * height * 4)

    for i in range(width * height):
        r, g, b, a = data[i * 4:i * 4 + 4]
        pixels[i * 4:i * 4 + 4] = bytes((r, g, b, a))

    return pixels


def decode_dxt3(data, width, height):
    """DXT3/BC2：每 16 字节一块，前 8 字节是显式 4 位 alpha，后 8 字节是 DXT1 颜色。"""
    pixels = bytearray(width * height * 4)
    block = 0

    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            offset = block * 16
            block += 1

            if offset + 16 > len(data):
                return pixels

            alpha_bits = struct.unpack_from("<Q", data, offset)[0]
            c0, c1 = struct.unpack_from("<HH", data, offset + 8)
            indices = struct.unpack_from("<I", data, offset + 12)[0]

            colors = expand_dxt_colors(c0, c1)

            for py in range(4):
                for px in range(4):
                    index = (indices >> (2 * (py * 4 + px))) & 0x3
                    alpha = ((alpha_bits >> (4 * (py * 4 + px))) & 0xF) * 17
                    x, y = bx + px, by + py

                    if x >= width or y >= height:
                        continue

                    r, g, b = colors[index]
                    slot = (y * width + x) * 4
                    pixels[slot:slot + 4] = bytes((r, g, b, alpha))

    return pixels


def expand_dxt_colors(c0, c1):
    def unpack(value):
        r = (value >> 11) & 0x1F
        g = (value >> 5) & 0x3F
        b = value & 0x1F
        return (r * 255 // 31, g * 255 // 63, b * 255 // 31)

    first = unpack(c0)
    second = unpack(c1)

    if c0 > c1:
        third = tuple((2 * first[i] + second[i]) // 3 for i in range(3))
        fourth = tuple((first[i] + 2 * second[i]) // 3 for i in range(3))
    else:
        third = tuple((first[i] + second[i]) // 2 for i in range(3))
        fourth = (0, 0, 0)

    return (first, second, third, fourth)


def decode(path, out_png):
    from PIL import Image

    content = load_content(path)
    fmt, width, height, data_pos = parse_texture(content)
    data = content[data_pos:]

    if fmt == SURFACE_COLOR:
        pixels = decode_color(data, width, height)
    elif fmt == SURFACE_DXT3:
        pixels = decode_dxt3(data, width, height)
    else:
        raise ValueError("暂不支持的 surface format %s（%s）"
                         % (fmt, FORMAT_NAMES.get(fmt, "?")))

    image = Image.frombytes("RGBA", (width, height), bytes(pixels))
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    image.save(out_png)
    return width, height, FORMAT_NAMES.get(fmt, str(fmt))


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        return 2

    if args[0] == "--probe":
        for path in args[1:]:
            content = load_content(path)
            fmt, width, height, data_pos = parse_texture(content)
            print("%-46s %4dx%-4d %-6s 数据 %d 字节"
                  % (os.path.basename(path), width, height,
                     FORMAT_NAMES.get(fmt, str(fmt)), len(content) - data_pos))
        return 0

    if len(args) % 2 != 0:
        print("需要成对的 <in.xnb> <out.png>")
        return 2

    for i in range(0, len(args), 2):
        width, height, name = decode(args[i], args[i + 1])
        print("%s -> %s  %dx%d %s" % (os.path.basename(args[i]), args[i + 1], width, height, name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
