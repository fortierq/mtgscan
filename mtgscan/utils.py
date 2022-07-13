from io import BytesIO
from urllib.parse import urlparse

import numpy as np
import requests
from PIL import Image


def is_url(text: str) -> bool:
    parsed = urlparse(str(text))
    return len(parsed.scheme) > 1


def load_url_or_file(image: str) -> Image.Image:
    if is_url(image):
        response = requests.get(image)
        response.raise_for_status()
        image = BytesIO(response.content)
    return np.asarray(Image.open(image))
