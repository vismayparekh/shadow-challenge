import os

import numpy as np
import cv2
from PIL import Image


def load_rgba(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGBA")
    return np.array(img, dtype=np.uint8)


def save_rgba(path: str, rgba: np.ndarray) -> None:
    Image.fromarray(rgba, mode="RGBA").save(path)


def paste_rgba(dst_rgba: np.ndarray, src_rgba: np.ndarray, x: int, y: int) -> np.ndarray:
    """Paste src onto dst at (x,y) using alpha blending."""
    h, w = src_rgba.shape[:2]
    H, W = dst_rgba.shape[:2]

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)

    if x0 >= x1 or y0 >= y1:
        return dst_rgba

    sx0 = x0 - x
    sy0 = y0 - y
    sx1 = sx0 + (x1 - x0)
    sy1 = sy0 + (y1 - y0)

    dst = dst_rgba[y0:y1, x0:x1].astype(np.float32) / 255.0
    src = src_rgba[sy0:sy1, sx0:sx1].astype(np.float32) / 255.0

    src_a = src[..., 3:4]
    dst_a = dst[..., 3:4]

    out_rgb = src[..., :3] * src_a + dst[..., :3] * (1.0 - src_a)
    out_a = src_a + dst_a * (1.0 - src_a)

    out = np.concatenate([out_rgb, out_a], axis=2)
    dst_rgba[y0:y1, x0:x1] = (np.clip(out, 0, 1) * 255.0).astype(np.uint8)
    return dst_rgba


def apply_shadow_to_bg(bg_rgba: np.ndarray, shadow_alpha: np.ndarray) -> np.ndarray:
    """Darken background where shadow exists."""
    out = bg_rgba.astype(np.float32) / 255.0
    a = np.clip(shadow_alpha, 0.0, 1.0)[..., None]
    out[..., 0:3] = out[..., 0:3] * (1.0 - a)
    return (np.clip(out, 0, 1) * 255.0).astype(np.uint8)
