from io import BytesIO
from urllib.parse import urlparse
import base64

import numpy as np
import requests
from PIL import Image


def is_url(text: str) -> bool:
    parsed = urlparse(str(text))
    return len(parsed.scheme) > 1


def load_url_or_base64(image: str) -> Image.Image:
    """Load an image as numpy array from an url or base64 string"""
    if is_url(image):
        response = requests.get(image)
        response.raise_for_status()
        image = BytesIO(response.content)
    else:
        image = BytesIO(base64.b64decode(image))
    return np.asarray(Image.open(image))
