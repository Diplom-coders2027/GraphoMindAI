import cv2
import numpy as np

from PIL import Image, ImageOps


def prepare_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    return image


def remove_noise(image: Image.Image) -> Image.Image:
    image_array = np.array(image.convert("L"))

    denoised_array = cv2.fastNlMeansDenoising(
        image_array,
        None,
        h=5,
        templateWindowSize=7,
        searchWindowSize=21
    )

    return Image.fromarray(denoised_array)