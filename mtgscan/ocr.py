import os
import requests
import time

class AzureRecognition:

    def __init__(self):
        self.subscription_key = os.environ['AZURE_VISION_KEY']
        self.text_recognition_url = os.environ['AZURE_VISION_ENDPOINT'] + "/vision/v3.1/read/analyze"
        
    def img_to_text(self, url_image):
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        data = {'url': url_image}
        response = requests.post(self.text_recognition_url, headers=headers, json=data)
        response.raise_for_status()
        analysis = {}
        poll = True
        while poll:
            response_final = requests.get(response.headers["Operation-Location"], headers=headers)
            analysis = response_final.json()
            time.sleep(1)
            if ("analyzeResult" in analysis):
                poll = False
            if ("status" in analysis and analysis['status'] == 'failed'):
                poll = False
        box_texts = []
        for line in analysis["analyzeResult"]["readResults"][0]["lines"]:
            box_texts.append((line["boundingBox"], line["text"]))
        return box_texts