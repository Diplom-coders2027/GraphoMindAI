"""Нарезка школьных тетрадей на фрагменты текста для train.py.

Вход (из скачанного датасета):
    data_notebooks/annotations_train.json, annotations_test.json
    data_notebooks/images/images/*.jpg

Выход (та же структура, что у Cyrillic Handwriting):
    data_notebooks_crops/train.tsv, test.tsv
    data_notebooks_crops/train/*.png, test/*.png

Запуск из корня проекта:
    python src/prepare_notebooks.py
    python src/prepare_notebooks.py --train-pages 300 --test-pages 50
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image

CATEGORY_IDS = {0}   # 0 = pupil_text (слова ученика); добавьте 1, 2, чтобы взять и комментарии
MAX_TEXT_LEN = 40    # как в Cyrillic: фрагменты до 40 символов
MIN_SIDE = 8         # слишком маленькие вырезки пропускаем


def crop_split(ann_path, images_dir, out_dir, split, max_pages):
    with open(ann_path, encoding="utf-8") as f:
        data = json.load(f)
    files = {im["id"]: im["file_name"] for im in data["images"]}

    # сгруппировать разметку по страницам, чтобы открывать каждую страницу один раз
    by_image = defaultdict(list)
    for a in data["annotations"]:
        if a["category_id"] not in CATEGORY_IDS:
            continue
        text = (a.get("attributes", {}).get("translation") or "").strip()
        text = text.replace("\t", " ").replace("\n", " ")
        if not text or len(text) > MAX_TEXT_LEN:
            continue
        by_image[a["image_id"]].append((a["segmentation"], text))

    out_images = out_dir / split
    out_images.mkdir(parents=True, exist_ok=True)

    rows = []
    page_ids = sorted(by_image)[:max_pages]
    for n, image_id in enumerate(page_ids, 1):
        page = Image.open(images_dir / files[image_id]).convert("L")
        for k, (seg, text) in enumerate(by_image[image_id]):
            pts = [v for part in seg for v in part]      # все точки многоугольника
            xs, ys = pts[0::2], pts[1::2]
            left = max(0, int(min(xs)))
            top = max(0, int(min(ys)))
            right = min(page.width, int(max(xs)) + 1)
            bottom = min(page.height, int(max(ys)) + 1)
            if right - left < MIN_SIDE or bottom - top < MIN_SIDE:
                continue
            name = f"{image_id}_{k}.png"
            page.crop((left, top, right, bottom)).save(out_images / name)
            rows.append(f"{name}\t{text}")
        if n % 25 == 0:
            print(f"  {split}: страниц {n}/{len(page_ids)}, фрагментов {len(rows)}")

    (out_dir / f"{split}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"{split}: страниц {len(page_ids)}, фрагментов {len(rows)}")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data_notebooks")
    ap.add_argument("--out", default="data_notebooks_crops")
    ap.add_argument("--train-pages", type=int, default=300)
    ap.add_argument("--test-pages", type=int, default=50)
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    images_dir = src / "images" / "images"
    crop_split(src / "annotations_train.json", images_dir, out, "train", args.train_pages)
    crop_split(src / "annotations_test.json", images_dir, out, "test", args.test_pages)
    print("Готово. Теперь:")
    print(f"python src/train.py --data {out} --epochs 10 --out models/crnn_notebooks.pt")


if __name__ == "__main__":
    main()
