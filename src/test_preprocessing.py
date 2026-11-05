from PIL import Image
from preprocessing import prepare_image, remove_noise


with Image.open("test_page.jpg") as image:
    prepared_image = prepare_image(image)
    denoised_image = remove_noise(prepared_image)

    denoised_image.save("test_page_denoised.png")

    print("Изображение успешно обработано!")
    print("Размер:", denoised_image.size)
    print("Режим:", denoised_image.mode)