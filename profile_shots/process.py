"""
Final v5: robust background removal + gentle lighting for 3D character reference shots.

Masking (tuned for dark hair backlit by a bright window + adjacent dark objects):
  - isnet-general-use SOLID mask (no alpha matting -> no translucent ragged hair).
  - GrabCut (seeded by isnet) used ONLY to peel background objects touching the
    lower face; never applied in the top hair band (grabcut chops backlit hair).
  - Median-smooth the mask boundary to remove isnet's jagged crown pixels.
  - Remove dark, low-saturation pixels in the far corners (kills the picture-frame /
    phone the subject is holding, which shadow-connects to the jaw).
  - Largest connected component; morphological close; 1.2px feather.

Lighting corrected from FOREGROUND pixels only.

Pose relabelling (source files were mis-ordered):
  left.jpeg -> front | front.jpeg -> left | right.jpeg -> right
"""
import numpy as np
from PIL import Image, ImageOps
import cv2
from rembg import remove, new_session

SRC = {"front": "left.jpeg", "left": "front.jpeg", "right": "right.jpeg"}
session = new_session("isnet-general-use")


def isnet_solid(im):
    return np.array(remove(im, session=session).convert("RGBA"))[..., 3]


def grabcut_mask(rgb, seed):
    h, w = rgb.shape[:2]
    gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    gc[seed > 30] = cv2.GC_PR_FGD
    gc[seed > 200] = cv2.GC_FGD
    gc[seed < 10] = cv2.GC_BGD
    cv2.grabCut(rgb, gc, None, np.zeros((1, 65)), np.zeros((1, 65)),
                5, cv2.GC_INIT_WITH_MASK)
    return np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)


def finalize(rgb, a_solid, b_grab):
    h, w = a_solid.shape
    top = int(h * 0.40)
    m = (a_solid > 128).astype(np.uint8)
    g = (b_grab > 128).astype(np.uint8)
    m[top:] = (m[top:] & g[top:])                       # peel bg only below hairline

    # remove dark low-sat pixels near the two lower corners (frame / held phone)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    dark = (hsv[..., 2] < 70) & (hsv[..., 1] < 90)
    corner = np.zeros((h, w), bool)
    corner[int(h * 0.55):, :int(w * 0.18)] = True        # bottom-left
    corner[int(h * 0.55):, int(w * 0.82):] = True        # bottom-right
    m[dark & corner] = 0

    m = cv2.medianBlur(m * 255, 5)                        # smooth jagged crown
    m = (m > 127).astype(np.uint8)
    n, lbl, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        m = (lbl == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    m = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))  # kill halo
    soft = cv2.GaussianBlur((m * 255).astype(np.float32), (0, 0), 1.2)
    return np.clip(soft, 0, 255).astype(np.uint8)


def improve_lighting(rgb, mask):
    img = rgb.astype(np.float32)
    fg = mask > 32
    if fg.sum() < 100:
        fg = np.ones(mask.shape, bool)
    means = img[fg].reshape(-1, 3).mean(0)
    gray = means.mean()
    img = np.clip(img * np.clip(gray / (means + 1e-6), 0.9, 1.12), 0, 255)
    lab = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2LAB)
    L, A, B = cv2.split(lab)
    L = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8)).apply(L)
    out = cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2RGB).astype(np.float32)
    gamma = 0.90 if (L[fg].mean() / 255.0) < 0.55 else 0.95
    out = np.clip(np.power(out / 255.0, gamma) * 255.0, 0, 255)
    hsv = cv2.cvtColor(out.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.05, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.uint8)


for pose, path in SRC.items():
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    rgb = np.array(im)
    a = isnet_solid(im)
    b = grabcut_mask(rgb, a)
    alpha = finalize(rgb, a, b)
    better = improve_lighting(rgb, alpha)
    cut = Image.fromarray(np.dstack([better, alpha]), "RGBA")
    cut.save(f"out/{pose}_cutout.png")
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    white.alpha_composite(cut)
    white.convert("RGB").save(f"out/{pose}_white.png", quality=95)
    print(f"{pose}: fg={(alpha>10).mean():.2f} done")

print("ALL DONE")
