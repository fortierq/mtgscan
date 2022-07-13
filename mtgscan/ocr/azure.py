import logging
import os
import time

import requests
from mtgscan.box_text import BoxTextList
from mtgscan.utils import is_url
from .ocr import OCR


class Azure(OCR):

    def __init__(self):
        try:
            self.subscription_key = os.environ['AZURE_VISION_KEY']
            self.text_recognition_url = os.environ['AZURE_VISION_ENDPOINT'] + "/vision/v3.1/read/analyze"
        except IndexError as e:
            print(str(e))
            print(
                "Azure credentials should be stored in environment variables AZURE_VISION_KEY and AZURE_VISION_ENDPOINT"
            )

    def __str__(self):
        return "Azure"

    def image_to_box_texts(self, image: str, is_base64=False) -> BoxTextList:
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        json, data = None, None
        if is_url(image):
            json = {'url': image}
        else:
            headers['Content-Type'] = 'application/octet-stream'
            data = image
            if not is_base64:
                with open(image, "rb") as f:
                    data = f.read()
        logging.info(f"Send {image} to Azure")
        response = requests.post(self.text_recognition_url, headers=headers, json=json, data=data)
        response.raise_for_status()
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
