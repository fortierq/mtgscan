from io import BytesIO
from urllib.parse import urlparse
import base64
from pathlib import Path

import numpy as np
import requests
from PIL import Image


def is_url(text: str) -> bool:
    parsed = urlparse(str(text))
    return len(parsed.scheme) > 1


def load_url_or_file_or_base64(image: str) -> Image.Image:
    """Load an image

    Parameters
    ----------
    image : str
        Url or path or base64 encoded image

    Returns
    -------
    Numpy array representing the image
    """
    if is_url(image):
        response = requests.get(image)
        response.raise_for_status()
        image = BytesIO(response.content)
    elif not Path(image).exists():
        image = BytesIO(base64.b64decode(image))
    return np.asarray(Image.open(image))
