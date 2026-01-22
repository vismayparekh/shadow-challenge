# Realistic Shadow Generator

This project composites a cutout foreground subject onto a background image and generates a **believable cast shadow** (silhouette-based — not a drop shadow). It outputs:

- `composite.png` (final render)
- `shadow_only.png` (debug)
- `mask_debug.png` (debug)

Supports:
- Directional light control (angle 0–360, elevation 0–90)
- Contact shadow (dark + sharp near contact)
- Soft falloff (blur + opacity decay with distance)
- (Bonus) Depth map bending/warping (optional)

---

## Project Structure

```
shadow-challenge/
  assets/                       # Provided background images
  shadow-solution/
    main.py                     # CLI entry (runs pipeline)
    shadow.py                   # Shadow math / warp / falloff
    utils.py                    # Image IO + blending helpers
    foreground.png              # Your cutout PNG (transparent background)
    output/                     # Generated outputs (created on run)
    ts-viewer/                  # Optional interactive UI (TypeScript)
```

---

## Requirements

- Python 3.10+ recommended
- macOS / Windows / Linux

Python libs:
- numpy
- opencv-python
- pillow

---

## Setup (Python)

From `shadow-solution/`:

```bash
cd shadow-solution
python3 -m venv .venv
source .venv/bin/activate
pip install numpy opencv-python pillow
```

---

## Foreground Preparation (Important)

Your `foreground.png` must be a **cutout PNG with transparency** (alpha channel).

**Mac quick method:**
Finder → right click your photo → **Quick Actions → Remove Background**  
Rename result to `foreground.png` and put it in `shadow-solution/`.

---

## Run (CLI)

From `shadow-solution/`:

```bash
python3 main.py \
  --fg foreground.png \
  --bg "../assets/B_Child Room.JPG" \
  --angle 60 \
  --elev 30 \
  --x 220 --y 160 \
  --scale 1.0 \
  --out output
```

Outputs will be saved to:

```
shadow-solution/output/
  composite.png
  shadow_only.png
  mask_debug.png
```

Open the final image:

```bash
open output/composite.png
```

---

## Parameters

- `--angle` (0–360): light direction (shadow is cast opposite)
- `--elev` (0–90): light elevation (low elev = long shadow)
- `--x --y`: foreground placement (top-left)
- `--scale`: scale foreground before compositing
- `--depth` (optional): grayscale depth map (0–255). If provided, shadow will bend/warp slightly.

Example with depth map:

```bash
python3 main.py \
  --fg foreground.png \
  --bg "../assets/B_Child Room.JPG" \
  --depth "../assets/depth_map.png" \
  --angle 120 --elev 20 \
  --x 200 --y 140 \
  --out output
```

---

## Debug Images

- `mask_debug.png`  
  Shows the alpha mask used for shadow.  
  ✅ Should look like the subject silhouette only.  
  ❌ If you see a big rectangle at the bottom, the cutout is wrong (background not fully removed).

- `shadow_only.png`  
  The shadow alpha output for validation.

---

## Optional: TypeScript Viewer (UI)

A simple Vite-based viewer can display outputs and (if configured with backend) regenerate images via sliders.

### Start viewer
```bash
cd ts-viewer
npm install
npm run dev
```

Open the shown URL (usually `http://localhost:5173`).

> If you implemented a Node/Express backend, the sliders can call Python to regenerate outputs automatically.

---

## Notes / Tips

- Best results happen when the subject’s **feet/contact point** are visible.
- If the subject is sitting / floating visually, contact shadows may look less realistic.
- Choose a background with a visible “floor plane” for stronger realism.

---

## Deliverables

Generated in `shadow-solution/output/`:

- `composite.png`
- `shadow_only.png`
- `mask_debug.png`

Source:
- `main.py`, `shadow.py`, `utils.py`
- (optional) `ts-viewer/` UI
