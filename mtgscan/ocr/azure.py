import logging
import os
import time
from urllib.parse import urlparse

import requests
from mtgscan.box_text import BoxTextList

from .ocr import OCR


class Azure(OCR):
    def __init__(self,
                 azure_vision_key=os.environ['AZURE_VISION_KEY'],
                 azure_vision_endpoint=os.environ['AZURE_VISION_ENDPOINT']):
        try:
            self.subscription_key = azure_vision_key
            self.text_recognition_url = azure_vision_endpoint + "/vision/v3.1/read/analyze"
        except IndexError as e:
            print(str(e))
            print(
                "Azure credentials should be stored in environment variables AZURE_VISION_KEY and AZURE_VISION_ENDPOINT"
            )

    def __str__(self):
        return "Azure"

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
        response = requests.post(self.text_recognition_url, headers=headers, json=json, data=data)
        response.raise_for_status()
        analysis = {}
        poll = True
        while poll:
            response_final = requests.get(response.headers["Operation-Location"], headers=headers)
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
