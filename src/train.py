"""Обучение CRNN (CNN + BiLSTM + CTC) на Cyrillic Handwriting Dataset.

Ожидаемая структура папки data/:
    train.tsv, test.tsv   - строки вида "имя_файла.png<TAB>текст"
    train/, test/         - сами картинки

Запуск (из корня проекта):
    python src/train.py --epochs 1 --fraction 0.02     # быстрая проверка
    python src/train.py --epochs 30 --fraction 0.25    # эксперимент для таблицы
    python src/train.py --epochs 30 --fraction 1.0     # полное обучение
"""
import argparse
import csv
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

IMG_H = 32      # высота, к которой приводятся все картинки
MIN_W = 32      # минимальная ширина
MAX_W = 400     # максимальная ширина (длинные подписи сжимаются)


# ---------- данные ----------

def read_tsv(tsv_path, img_dir):
    """Читает файл с подписями, пропускает пустые строки и отсутствующие картинки."""
    items = []
    with open(tsv_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            parts = line.split("\t", 1)
            if len(parts) < 2:
                parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            name, text = parts[0], parts[1].strip()
            path = img_dir / name
            if text and path.exists():
                items.append((str(path), text))
    return items


class HandwritingDataset(Dataset):
    def __init__(self, items, char2idx):
        self.items = items
        self.char2idx = char2idx

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, text = self.items[i]
        img = Image.open(path).convert("L")
        w, h = img.size
        new_w = min(max(round(w * IMG_H / h), MIN_W), MAX_W)
        img = img.resize((new_w, IMG_H), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(img, dtype=np.float32) / 255.0)
        x = (x - 0.5) / 0.5            # белый фон -> 1.0
        target = [self.char2idx[c] for c in text if c in self.char2idx]
        return x.unsqueeze(0), torch.tensor(target, dtype=torch.long), text


def collate(batch):
    imgs, targets, texts = zip(*batch)
    max_w = max(im.shape[2] for im in imgs)
    out = torch.ones(len(imgs), 1, IMG_H, max_w)   # дополняем белым
    for k, im in enumerate(imgs):
        out[k, :, :, : im.shape[2]] = im
    in_lens = torch.tensor([max(im.shape[2] // 4, 1) for im in imgs], dtype=torch.long)
    t_lens = torch.tensor([len(t) for t in targets], dtype=torch.long)
    return out, torch.cat(targets), t_lens, in_lens, list(texts)


# ---------- модель ----------

class CRNN(nn.Module):
    """CNN выделяет признаки, BiLSTM читает их как последовательность, CTC даёт символы."""

    def __init__(self, n_classes):
        super().__init__()

        def block(i, o):
            return [nn.Conv2d(i, o, 3, padding=1, bias=False),
                    nn.BatchNorm2d(o), nn.ReLU(inplace=True)]

        self.cnn = nn.Sequential(
            *block(1, 64), nn.MaxPool2d(2, 2),                        # H 16, W/2
            *block(64, 128), nn.MaxPool2d(2, 2),                      # H 8,  W/4
            *block(128, 256), *block(256, 256), nn.MaxPool2d((2, 1), (2, 1)),  # H 4
            *block(256, 512), nn.MaxPool2d((2, 1), (2, 1)),           # H 2
        )
        self.rnn = nn.LSTM(512, 256, num_layers=2, bidirectional=True, dropout=0.2)
        self.fc = nn.Linear(512, n_classes)

    def forward(self, x):
        f = self.cnn(x)            # B, 512, 2, W/4
        f = f.mean(2)              # B, 512, T
        f = f.permute(2, 0, 1)     # T, B, 512
        f, _ = self.rnn(f)
        return self.fc(f)          # T, B, классы


# ---------- метрики ----------

def greedy_decode(logits, idx2char):
    best = logits.argmax(2).transpose(0, 1).cpu().tolist()
    result = []
    for seq in best:
        out, prev = [], 0
        for k in seq:
            if k != prev and k != 0:
                out.append(idx2char[k])
            prev = k
        result.append("".join(out))
    return result


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


@torch.no_grad()
def evaluate(model, loader, idx2char, device):
    """Возвращает (точность по символам %, точность по словам %)."""
    model.eval()
    ce = cn = we = wn = 0
    for imgs, _, _, _, texts in loader:
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            logits = model(imgs.to(device))
        for pred, ref in zip(greedy_decode(logits.float(), idx2char), texts):
            ce += edit_distance(pred, ref)
            cn += len(ref)
            pw, rw = pred.split(), ref.split()
            we += edit_distance(pw, rw)
            wn += len(rw)
    char_acc = max(0.0, 1 - ce / max(cn, 1)) * 100
    word_acc = max(0.0, 1 - we / max(wn, 1)) * 100
    return char_acc, word_acc


# ---------- обучение ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--fraction", type=float, default=1.0, help="доля обучающих данных (0-1)")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="models/crnn.pt")
    args = ap.parse_args()

    random.seed(0)
    torch.manual_seed(0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    print("Устройство:", device)

    data = Path(args.data)
    all_train = read_tsv(data / "train.tsv", data / "train")
    test_items = read_tsv(data / "test.tsv", data / "test")
    print(f"Загружено: train {len(all_train)}, test {len(test_items)}")

    # алфавит строим по всем обучающим подписям; 0 зарезервирован под CTC blank
    chars = sorted({c for _, t in all_train for c in t})
    char2idx = {c: i + 1 for i, c in enumerate(chars)}
    idx2char = {i + 1: c for i, c in enumerate(chars)}
    print("Символов в алфавите:", len(chars))

    # маленькая валидация из train (одна и та же для всех экспериментов)
    random.shuffle(all_train)
    n_val = max(200, int(0.02 * len(all_train)))
    val_items = all_train[:n_val]
    train_items = all_train[n_val:]
    train_items = train_items[: max(1, int(len(train_items) * args.fraction))]
    print(f"Обучение на {len(train_items)} фрагментах (доля {args.fraction})")

    def make_loader(items, shuffle):
        return DataLoader(
            HandwritingDataset(items, char2idx), batch_size=args.batch, shuffle=shuffle,
            num_workers=args.workers, collate_fn=collate, pin_memory=use_amp,
            persistent_workers=args.workers > 0)

    train_loader = make_loader(train_items, True)
    val_loader = make_loader(val_items, False)
    test_loader = make_loader(test_items, False)

    model = CRNN(len(chars) + 1).to(device)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=args.lr, steps_per_epoch=len(train_loader), epochs=args.epochs)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    best_val = -1.0
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        total, steps = 0.0, 0
        for imgs, targets, t_lens, in_lens, _ in train_loader:
            imgs = imgs.to(device, non_blocking=True)
            with torch.autocast(device.type, enabled=use_amp):
                logits = model(imgs)
            log_probs = logits.float().log_softmax(2)
            loss = ctc(log_probs, targets, in_lens, t_lens)

            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            total += loss.item()
            steps += 1

        v_char, v_word = evaluate(model, val_loader, idx2char, device)
        print(f"Эпоха {epoch}/{args.epochs} | loss {total / max(steps, 1):.3f} | "
              f"валидация: символы {v_char:.1f}%, слова {v_word:.1f}% | "
              f"{(time.time() - start) / 60:.1f} мин")
        if v_char > best_val:
            best_val = v_char
            torch.save({"model": model.state_dict(), "chars": chars,
                        "img_h": IMG_H, "max_w": MAX_W}, out_path)

    # финальная проверка лучшей модели на тестовой выборке
    ckpt = torch.load(out_path, map_location=device)
    model.load_state_dict(ckpt["model"])
    t_char, t_word = evaluate(model, test_loader, idx2char, device)
    minutes = (time.time() - start) / 60
    print(f"\nТЕСТ: точность по символам {t_char:.2f}%, по словам {t_word:.2f}%")

    # запись строки для таблицы в отчёт
    res = Path("results.csv")
    is_new = not res.exists()
    with open(res, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["fraction", "n_train", "epochs", "char_acc", "word_acc", "minutes"])
        w.writerow([args.fraction, len(train_items), args.epochs,
                    f"{t_char:.2f}", f"{t_word:.2f}", f"{minutes:.1f}"])
    print("Результат дописан в results.csv, модель сохранена в", out_path)


if __name__ == "__main__":
    main()
