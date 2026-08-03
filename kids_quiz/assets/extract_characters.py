#!/usr/bin/env python3
"""Cut JJ (bunny) + Mikey (turtle) out of the FlipaClip screenshot into transparent PNG sprites.

Method: flood the light-gray background inward from the border (so interior whites survive,
because the black outlines block the flood), then keep the 2 largest opaque blobs (drops the
"I love Tik?" caption + FlipaClip watermark), split left/right into JJ and Mikey.
"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "/Users/deepakkumarrai/Downloads/images.jpeg"
OUT = "."

img = Image.open(SRC).convert("RGB")
arr = np.array(img)
H, W = arr.shape[:2]

# 0) paint out the baked-in "love Tik?" caption + FlipaClip watermark BEFORE cutout (inpaint).
#    Boxes are fractions of the image so they track if the source is re-sized.
ip = np.zeros((H, W), np.uint8)
for fx0, fy0, fx1, fy1 in [(0.34, 0.23, 0.74, 0.30),   # caption band
                           (0.05, 0.87, 0.36, 0.95)]:  # watermark corner
    ip[int(fy0*H):int(fy1*H), int(fx0*W):int(fx1*W)] = 255
arr = cv2.inpaint(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR), ip, 4, cv2.INPAINT_TELEA)
arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
bg = arr[2, 2].astype(int)

# 1) "gray-ish like the background" mask — keep it TIGHT so the near-white face is NOT flooded
diff = np.abs(arr.astype(int) - bg).max(axis=2)
sat = arr.max(axis=2).astype(int) - arr.min(axis=2).astype(int)   # low sat = grayish
grayish = ((diff < 18) & (sat < 20)).astype(np.uint8)

# 2) keep only gray connected to the border = exterior background
n, lab = cv2.connectedComponents(grayish, connectivity=4)
border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
border.discard(0)
bg_mask = np.isin(lab, list(border))

alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
# clean: close tiny holes, drop specks
alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

# 3) keep the single largest opaque blob = the two merged characters (drops caption + watermark)
n2, lab2, stats, cent = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), connectivity=8)
big = max(range(1, n2), key=lambda i: stats[i, cv2.CC_STAT_AREA])
M = (lab2 == big).astype(np.uint8)
print(f"merged blob area {int(stats[big, cv2.CC_STAT_AREA])}, bbox w={stats[big,cv2.CC_STAT_WIDTH]}")

# 3a) one seed firmly inside each character (JJ = left, Mikey = right), snapped to opaque
ys_all, xs_all = np.where(M > 0)
def snap(tx, ty):
    i = np.argmin((xs_all - tx) ** 2 + (ys_all - ty) ** 2)
    return int(xs_all[i]), int(ys_all[i])
jj_seed = snap(0.26 * W, 0.58 * H)
mk_seed = snap(0.80 * W, 0.64 * H)
print(f"JJ seed {jj_seed} · Mikey seed {mk_seed}")

# 3b) geodesic multi-source BFS INSIDE the mask -> nearest seed *through the shape*
from collections import deque
label = np.zeros((H, W), np.int8)          # 1 = JJ, 2 = Mikey
dq = deque()
for (sx, sy), lb in [(jj_seed, 1), (mk_seed, 2)]:
    label[sy, sx] = lb; dq.append((sx, sy))
Mb = M > 0
while dq:
    x, y = dq.popleft(); lb = label[y, x]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x+dx, y+dy
        if 0 <= nx < W and 0 <= ny < H and Mb[ny, nx] and label[ny, nx] == 0:
            label[ny, nx] = lb; dq.append((nx, ny))
masks = {"jj": label == 1, "mikey": label == 2}
names = ["jj", "mikey"]
from scipy import ndimage
for name in names:
    m = masks[name]
    m = ndimage.binary_fill_holes(m)          # refill any enclosed transparent pockets (e.g. face)
    ys, xs = np.where(m)
    x0, x1, y0, y1 = xs.min(), xs.max()+1, ys.min(), ys.max()+1
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = arr
    rgba[..., 3] = np.where(m, 255, 0)
    crop = Image.fromarray(rgba[y0:y1, x0:x1], "RGBA")
    # soften the alpha edge by 0.6px so it doesn't look jagged on the sky
    a = crop.split()[3].filter(ImageFilter.GaussianBlur(0.6))
    crop.putalpha(a)
    crop.save(f"{name}.png")
    print(f"  {name}.png  {crop.size}")
