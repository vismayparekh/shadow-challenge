import math

import numpy as np
import cv2


def find_contact_y_and_x(mask: np.ndarray) -> tuple[int, int]:
    """mask is float 0..1, shape (H,W). Returns (contact_y, contact_x_center)."""
    ys, xs = np.where(mask > 0.05)
    if len(ys) == 0:
        raise ValueError("Foreground mask is empty. Make sure your foreground is a PNG with transparency.")
    contact_y = int(np.max(ys))

    # Use pixels close to the bottom to estimate x-center at contact
    band = 3
    ys2, xs2 = np.where((mask > 0.05) & (np.abs(np.arange(mask.shape[0])[:, None] - contact_y) <= band))
    if len(xs2) > 0:
        contact_x = int(np.mean(xs2))
    else:
        contact_x = int(np.mean(xs))
    return contact_y, contact_x


def affine_shadow_warp(mask: np.ndarray, angle_deg: float, elev_deg: float, contact_y: int) -> np.ndarray:
    """
    Projects the silhouette onto the ground plane using an affine transform:
    - angle controls direction (light direction; shadow goes opposite)
    - elevation controls length (90 = no shadow)
    """
    H, W = mask.shape

    # Shadow direction = opposite of light direction
    theta = math.radians(angle_deg)
    light_dir = (math.cos(theta), math.sin(theta))
    shadow_dir = (-light_dir[0], -light_dir[1])

    elev = math.radians(max(0.1, min(89.9, elev_deg)))
    cot = 1.0 / math.tan(elev)  # bigger when light is low

    a = cot * shadow_dir[0]
    b = cot * shadow_dir[1]

    # Anchor the contact line: points at y=contact_y should not move
    # x' = x - a*y + a*contact_y
    # y' = (1-b)*y + b*contact_y
    M = np.array([
        [1.0, -a, a * float(contact_y)],
        [0.0, (1.0 - b), b * float(contact_y)],
    ], dtype=np.float32)

    warped = cv2.warpAffine(
        mask.astype(np.float32),
        M,
        (W, H),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0.0,
    )

    # Clean small interpolation noise
    warped = np.clip(warped, 0.0, 1.0)
    return warped, shadow_dir


def depth_warp(shadow: np.ndarray, depth_gray: np.ndarray, shadow_dir: tuple[float, float]) -> np.ndarray:
    """
    Bonus: use a depth map as a *displacement* field to slightly bend the shadow.
    This is not perfect physics, but looks more believable on uneven surfaces.
    """
    H, W = shadow.shape
    if depth_gray.shape[:2] != (H, W):
        depth_gray = cv2.resize(depth_gray, (W, H), interpolation=cv2.INTER_LINEAR)

    depth = depth_gray.astype(np.float32) / 255.0  # 0..1
    # center around 0
    disp = (depth - 0.5)

    # stronger bending farther from contact tends to look nicer; approximate with shadow intensity itself
    strength = 25.0  # pixels (tweak if you want more/less bending)
    dx = disp * strength * shadow_dir[0]
    dy = disp * strength * shadow_dir[1]

    grid_x, grid_y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    map_x = grid_x + dx
    map_y = grid_y + dy

    warped = cv2.remap(
        shadow.astype(np.float32),
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0.0,
    )
    return np.clip(warped, 0.0, 1.0)


def build_realistic_shadow(shadow_base: np.ndarray, contact_y: int, contact_x: int, shadow_dir: tuple[float, float]) -> np.ndarray:
    """
    Create:
    - contact shadow (sharp/dark near contact)
    - mid + far shadow (more blur + lower opacity)
    - opacity decay with distance along shadow direction
    """
    H, W = shadow_base.shape

    # Distance along shadow direction from contact point
    vx, vy = shadow_dir
    grid_x, grid_y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    dist = (grid_x - float(contact_x)) * vx + (grid_y - float(contact_y)) * vy
    dist = np.maximum(dist, 0.0)

    # Three zones (pixels) - tweak as needed
    contact_zone = 35.0
    mid_zone = 180.0

    contact_mask = shadow_base * (dist <= contact_zone)
    mid_mask = shadow_base * ((dist > contact_zone) & (dist <= mid_zone))
    far_mask = shadow_base * (dist > mid_zone)

    # Make contact shadow tighter: erode before blur
    kernel = np.ones((3, 3), np.uint8)
    contact_mask_u8 = (contact_mask * 255).astype(np.uint8)
    contact_mask_u8 = cv2.erode(contact_mask_u8, kernel, iterations=1)
    contact_mask = contact_mask_u8.astype(np.float32) / 255.0

    # Blur increases with distance
    contact_blur = cv2.GaussianBlur(contact_mask, (0, 0), sigmaX=2.0)
    mid_blur = cv2.GaussianBlur(mid_mask, (0, 0), sigmaX=10.0)
    far_blur = cv2.GaussianBlur(far_mask, (0, 0), sigmaX=22.0)

    # Opacity decreases with distance
    fade_scale = 260.0
    fade = np.exp(-dist / fade_scale).astype(np.float32)

    shadow_alpha = (
        (0.85 * contact_blur) +
        (0.45 * mid_blur) +
        (0.22 * far_blur)
    ) * fade

    # Clamp to avoid over-dark
    return np.clip(shadow_alpha, 0.0, 0.85)
