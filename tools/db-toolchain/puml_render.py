# -*- coding: utf-8 -*-
import zlib, urllib.request, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def encode6bit(b):
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    if b == 0:
        return "-"
    if b == 1:
        return "_"
    return "?"


def append3bytes(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return encode6bit(c1 & 0x3F) + encode6bit(c2 & 0x3F) + encode6bit(c3 & 0x3F) + encode6bit(c4 & 0x3F)


def encode_puml(text):
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    res = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        if len(chunk) == 3:
            res.append(append3bytes(chunk[0], chunk[1], chunk[2]))
        elif len(chunk) == 2:
            res.append(append3bytes(chunk[0], chunk[1], 0))
        else:
            res.append(append3bytes(chunk[0], 0, 0))
    return "".join(res)


src, out = sys.argv[1], sys.argv[2]
puml = open(src, encoding="utf-8").read()
url = "https://www.plantuml.com/plantuml/png/" + encode_puml(puml)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = r.read()
open(out, "wb").write(data)
from PIL import Image
im = Image.open(out)
print("saved", out, im.size, len(data))
