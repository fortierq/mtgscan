import logging
import os
import time
from urllib.parse import urlparse

import requests

from mtgscan.box_text import BoxTextList


class OCR:
    def image_to_box_texts(self, image: str) -> BoxTextList:
        """Apply OCR on an image containing Magic cards

        Parameters
        ----------
        image : str
            URL or path to an image

        Returns
        -------
        BoxTextList
            Texts and boxes recognized by the OCR
        """
        raise NotImplementedError()


class Azure(OCR):
    def __init__(self):
        self.subscription_key = os.environ['AZURE_VISION_KEY']
        self.text_recognition_url = os.environ['AZURE_VISION_ENDPOINT'] + \
            "/vision/v3.1/read/analyze"
        super().__init__()

    def __str__(self):
        return "azure"

    def image_to_box_texts(self, image: str) -> BoxTextList:
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        json, data = None, None
        parsed = urlparse(str(image))
        if len(parsed.scheme) > 1:  # if URL
            json = {'url': image}
        else:
            headers['Content-Type'] = 'application/octet-stream'
            with open(image, "rb") as f:
                data = f.read()
        logging.info(f"Send {image} to Azure")
        response = requests.post(
            self.text_recognition_url, headers=headers, json=json, data=data)
        response.raise_for_status()
        analysis = {}
        poll = True
        while poll:
            response_final = requests.get(
                response.headers["Operation-Location"], headers=headers)
            analysis = response_final.json()
            time.sleep(1)
            if "analyzeResult" in analysis:
                poll = False
            if "status" in analysis and analysis['status'] == 'failed':
                poll = False
        box_texts = BoxTextList()
        for line in analysis["analyzeResult"]["readResults"][0]["lines"]:
            box_texts.add(line["boundingBox"], line["text"])
        return box_texts
