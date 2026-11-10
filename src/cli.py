import sys

from PIL import Image

from recognizer import recognize


def main():
    if len(sys.argv) < 2:
        print("Использование: python src/cli.py путь_к_фото.jpg")
        sys.exit(1)

    path = sys.argv[1]
    try:
        image = Image.open(path)
    except (FileNotFoundError, Image.UnidentifiedImageError):
        print(f"Не удалось открыть изображение: {path}")
        sys.exit(1)

    print(recognize(image))


if __name__ == "__main__":
    main()