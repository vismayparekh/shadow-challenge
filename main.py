import argparse
import os

import numpy as np
from PIL import Image

from utils import load_rgba, save_rgba, paste_rgba, apply_shadow_to_bg
from shadow import find_contact_y_and_x, affine_shadow_warp, depth_warp, build_realistic_shadow


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fg", required=True, help="Foreground PNG with transparency (cutout subject)")
    p.add_argument("--bg", required=True, help="Background image")
    p.add_argument("--depth", default=None, help="Optional depth map (grayscale 0-255)")
    p.add_argument("--angle", type=float, default=45.0, help="Light angle (0-360). Shadow goes opposite direction.")
    p.add_argument("--elev", type=float, default=35.0, help="Light elevation (0-90). 90=short shadow.")
    p.add_argument("--x", type=int, default=200, help="Foreground X position (top-left)")
    p.add_argument("--y", type=int, default=150, help="Foreground Y position (top-left)")
    p.add_argument("--scale", type=float, default=1.0, help="Foreground scale")
    p.add_argument("--out", default=".", help="Output directory")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)

    bg = load_rgba(args.bg)
    H, W = bg.shape[:2]

    fg = load_rgba(args.fg)
    if args.scale != 1.0:
        new_w = max(1, int(fg.shape[1] * args.scale))
        new_h = max(1, int(fg.shape[0] * args.scale))
        fg = np.array(Image.fromarray(fg).resize((new_w, new_h), resample=Image.LANCZOS), dtype=np.uint8)

    # Build a full-canvas FG layer (so mask aligns with background)
    fg_layer = np.zeros((H, W, 4), dtype=np.uint8)
    fg_layer = paste_rgba(fg_layer, fg, args.x, args.y)

    mask = (fg_layer[..., 3].astype(np.float32) / 255.0)
    contact_y, contact_x = find_contact_y_and_x(mask)

    # Base shadow shape from warped silhouette
    shadow_base, shadow_dir = affine_shadow_warp(mask, args.angle, args.elev, contact_y)

    # Bonus: depth warp
    if args.depth:
        depth_img = Image.open(args.depth).convert("L")
        depth_gray = np.array(depth_img, dtype=np.uint8)
        shadow_base = depth_warp(shadow_base, depth_gray, shadow_dir)

    # Realistic falloff + contact shadow
    shadow_alpha = build_realistic_shadow(shadow_base, contact_y, contact_x, shadow_dir)

    # Save debug: mask
    mask_debug = (np.clip(mask, 0, 1) * 255).astype(np.uint8)
    mask_debug_rgba = np.dstack([mask_debug, mask_debug, mask_debug, np.full_like(mask_debug, 255)])
    save_rgba(os.path.join(args.out, "mask_debug.png"), mask_debug_rgba)

    # Save debug: shadow only
    shadow_u8 = (np.clip(shadow_alpha, 0, 1) * 255).astype(np.uint8)
    shadow_only = np.zeros((H, W, 4), dtype=np.uint8)
    shadow_only[..., 3] = shadow_u8  # black with alpha
    save_rgba(os.path.join(args.out, "shadow_only.png"), shadow_only)

    # Composite
    bg_shadowed = apply_shadow_to_bg(bg, shadow_alpha)
    composite = bg_shadowed.copy()
    composite = paste_rgba(composite, fg_layer, 0, 0)
    save_rgba(os.path.join(args.out, "composite.png"), composite)

    print("Done ✅")
    print("Wrote:")
    print(" -", os.path.join(args.out, "mask_debug.png"))
    print(" -", os.path.join(args.out, "shadow_only.png"))
    print(" -", os.path.join(args.out, "composite.png"))


if __name__ == "__main__":
    main()
