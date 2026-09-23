# -*- coding: utf-8 -*-
"""白/黑底图片抠图：从四角 flood fill 背景色连通区域 -> 透明。
用法: python cutout.py <src> <dst>"""
from PIL import Image
from collections import deque
import sys

FEATHER = 8


def detect_bg(rgb):
    r, g, b = rgb
    if r > 200 and g > 200 and b > 200:
        return "white"
    if r < 80 and g < 80 and b < 80:
        return "black"
    return "white"


def make_close(bg, tol):
    if bg == "white":
        def close(rgb):
            return (abs(rgb[0] - 255) <= tol and abs(rgb[1] - 255) <= tol
                    and abs(rgb[2] - 255) <= tol)
    else:
        def close(rgb):
            return rgb[0] <= tol and rgb[1] <= tol and rgb[2] <= tol
    return close


def main():
    src, dst = sys.argv[1], sys.argv[2]
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    px = img.load()
    bg_kind = detect_bg(px[0, 0][:3])
    tol = 42 if bg_kind == "black" else 48
    close = make_close(bg_kind, tol)

    visited = bytearray(w * h)
    bg = bytearray(w * h)  # 1 = 背景, 2 = 过渡

    def idx(x, y):
        return y * w + x

    starts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    dq = deque()
    for sx, sy in starts:
        if not visited[idx(sx, sy)]:
            visited[idx(sx, sy)] = 1
            dq.append((sx, sy))

    while dq:
        x, y = dq.popleft()
        r, g, b, a = px[x, y]
        if not close((r, g, b)):
            continue
        bg[idx(x, y)] = 1
        for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[idx(nx, ny)]:
                visited[idx(nx, ny)] = 1
                dq.append((nx, ny))

    # 羽化过渡
    for _ in range(FEATHER):
        edge = []
        for y in range(h):
            for x in range(w):
                if bg[idx(x, y)]:
                    continue
                for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                    if 0 <= nx < w and 0 <= ny < h and bg[idx(nx, ny)]:
                        edge.append((x, y))
                        break
        for x, y in edge:
            bg[idx(x, y)] = 2

    removed = 0
    for y in range(h):
        for x in range(w):
            v = bg[idx(x, y)]
            if v == 1:
                px[x, y] = (255, 255, 255, 0)
                removed += 1
            elif v == 2:
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, a // 2)
    img.save(dst)
    total = w * h
    print(f"bg={bg_kind} size={w}x{h} removed={removed} ({removed/total*100:.1f}%) -> {dst}")


if __name__ == "__main__":
    main()
