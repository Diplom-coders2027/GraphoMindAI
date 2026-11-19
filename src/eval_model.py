"""Проверка сохранённой модели на тестовой выборке.

Запуск из корня проекта:
    python src/eval_model.py --model models/crnn_notebooks.pt --data data_notebooks_crops
"""
import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from train import CRNN, HandwritingDataset, collate, evaluate, read_tsv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model, map_location=device)
    chars = ckpt["chars"]
    char2idx = {c: i + 1 for i, c in enumerate(chars)}
    idx2char = {i + 1: c for i, c in enumerate(chars)}

    model = CRNN(len(chars) + 1).to(device)
    model.load_state_dict(ckpt["model"])

    data = Path(args.data)
    items = read_tsv(data / "test.tsv", data / "test")
    loader = DataLoader(
        HandwritingDataset(items, char2idx), batch_size=args.batch,
        collate_fn=collate, num_workers=0)

    char_acc, word_acc = evaluate(model, loader, idx2char, device)
    print(f"Тест ({len(items)} фрагментов): символы {char_acc:.2f}%, слова {word_acc:.2f}%")


if __name__ == "__main__":
    main()
