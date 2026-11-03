from PIL import Image
from preprocessing import prepare_image


with Image.open("test_page.jpg") as image:
    processed_image = prepare_image(image)

    processed_image.save("test_page_processed.png")

    print("Изображение успешно обработано!")
    print("Размер:", processed_image.size)
    print("Режим:", processed_image.mode)