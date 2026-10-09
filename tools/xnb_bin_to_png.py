# -*- coding: utf-8 -*-
"""把**已解压**的 XNB 载荷（.bin）转成 PNG。

背景（批次 38）：Terraria 的 `Content/Images/*.xnb` 是**标准压缩 XNB（LZX）**，
本机没有纯 Python 的 LZX 解码器，所以解压那一步交给跑在游戏进程里的临时模组
（`.tmp-vanilladump`，用 FNA 自带的内部 `Microsoft.Xna.Framework.Content.LzxDecoder`），
它把解压后的原始载荷写成 `.bin`；这个脚本负责解析 Texture2D 并落成 PNG。

载荷结构（XNA `Texture2DReader`）：
    7bit 读取器数量 | 每个读取器（7bit 长度 + 名字 + 4 字节版本） |
    7bit 共享资源数 | 7bit 类型 id | int32 格式 | int32 宽 | int32 高 |
    int32 mip 数 | int32 数据字节数 | 像素字节

用法:
    python tools/xnb_bin_to_png.py <in.bin> <out.png>
    python tools/xnb_bin_to_png.py --batch <rawdir> <outdir>
"""
import argparse
import os
import struct
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from read_xnb import read_7bit_int, read_string  # noqa: E402

# XNA SurfaceFormat 里我们会遇到的那几个
FORMAT_COLOR = 0
FORMAT_BGR565 = 1
FORMAT_BGRA5551 = 2
FORMAT_BGRA4444 = 3
FORMAT_DXT1 = 4
FORMAT_DXT3 = 5
FORMAT_DXT5 = 6


def parse_texture(content):
    pos = 0
    readers, pos = read_7bit_int(content, pos)
    names = []

    for _ in range(readers):
        name, pos = read_string(content, pos)
        names.append(name)
        pos += 4

    shared, pos = read_7bit_int(content, pos)

    if shared > 0:
        pos += shared * 0  # 共享资源索引表：本批贴图用不到

    _type_id, pos = read_7bit_int(content, pos)
    fmt, width, height, mips, size = struct.unpack_from("<iiiii", content, pos)
    pos += 20
    pixels = content[pos:pos + size]

    return names, shared, fmt, width, height, mips, size, pixels


def to_rgba(fmt, width, height, pixels):
    if fmt == FORMAT_COLOR:
        expected = width * height * 4
        raw = pixels[:expected]

        if len(raw) < expected:
            raise ValueError("像素数据不足：%d < %d" % (len(raw), expected))

        return Image.frombytes("RGBA", (width, height), raw)

    if fmt == FORMAT_BGR565:
        raw = pixels[:width * height * 2]
        out = bytearray(width * height * 4)

        for i in range(width * height):
            value = raw[i * 2] | (raw[i * 2 + 1] << 8)
            r = (value >> 11) & 0x1F
            g = (value >> 5) & 0x3F
            b = value & 0x1F
            out[i * 4 + 0] = (r << 3) | (r >> 2)
            out[i * 4 + 1] = (g << 2) | (g >> 4)
            out[i * 4 + 2] = (b << 3) | (b >> 2)
            out[i * 4 + 3] = 255

        return Image.frombytes("RGBA", (width, height), bytes(out))

    raise ValueError("暂不支持的 SurfaceFormat %d（多半是 DXT 压缩）" % fmt)


def convert(in_path, out_path):
    with open(in_path, "rb") as handle:
        content = handle.read()

    names, _shared, fmt, width, height, _mips, size, pixels = parse_texture(content)

    if "Texture2DReader" not in " ".join(names):
        raise ValueError("不是 Texture2D 载荷：读取器 = %r" % (names,))

    image = to_rgba(fmt, width, height, pixels)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    image.save(out_path)

    return width, height, fmt, size, names


def main():
    parser = argparse.ArgumentParser(description="已解压的 XNB 载荷 -> PNG")
    parser.add_argument("input", nargs="?")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--batch", nargs=2, metavar=("RAWDIR", "OUTDIR"),
                        help="批量转换目录下的所有 .bin")
    args = parser.parse_args()

    if args.batch:
        raw_dir, out_dir = args.batch
        done = failed = 0

        for name in sorted(os.listdir(raw_dir)):
            if not name.endswith(".bin"):
                continue

            try:
                width, height, fmt, size, _names = convert(
                    os.path.join(raw_dir, name),
                    os.path.join(out_dir, name[:-4] + ".png"))
                print("  %-28s %4dx%-5d fmt=%d bytes=%d" % (name[:-4], width, height, fmt, size))
                done += 1
            except Exception as error:  # noqa: BLE001
                print("  %-28s 失败：%r" % (name[:-4], error))
                failed += 1

        print("转换完成：%d 张，失败 %d 张 -> %s" % (done, failed, out_dir))
        return 0 if done else 1

    if not args.input or not args.output:
        parser.error("需要 <in.bin> <out.png>，或用 --batch")

    width, height, fmt, size, names = convert(args.input, args.output)
    print("%dx%d fmt=%d bytes=%d readers=%s -> %s"
          % (width, height, fmt, size, names, args.output))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
