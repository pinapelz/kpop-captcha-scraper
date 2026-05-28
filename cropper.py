import cv2
import os
from pathlib import Path
from insightface.app import FaceAnalysis

INPUT_DIR = "../captcha-original"
OUTPUT_DIR = "../captcha"

EXTS = {".jpg", ".jpeg", ".png", ".webp"}

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

os.makedirs(OUTPUT_DIR, exist_ok=True)

def resize_and_crop(img, size=100):
    h, w = img.shape[:2]
    scale = max(size / w, size / h)
    nw = int(w * scale)
    nh = int(h * scale)
    img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    x = (nw - size) // 2
    y = (nh - size) // 2
    return img[y:y+size, x:x+size]


def process_image(path: Path):
    img = cv2.imread(str(path))
    if img is None:
        print(f"failed: {path}")
        return
    faces = app.get(img)
    if not faces:
        print(f"no face: {path}")
        return
    for i, face in enumerate(faces):
        x1, y1, x2, y2 = face.bbox.astype(int)
        pad_x = int((x2 - x1) * 0.25)
        pad_y = int((y2 - y1) * 0.35)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(img.shape[1], x2 + pad_x)
        y2 = min(img.shape[0], y2 + pad_y)
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        crop = resize_and_crop(crop, 100)
        rel = path.relative_to(INPUT_DIR)
        out_dir = Path(OUTPUT_DIR) / rel.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        out_name = f"{path.stem}.png"
        out_path = out_dir / out_name

        cv2.imwrite(str(out_path), crop)

        print(f"saved: {out_path}")

for root, _, files in os.walk(INPUT_DIR):
    for file in files:
        path = Path(root) / file
        if path.suffix.lower() in EXTS:
            process_image(path)
