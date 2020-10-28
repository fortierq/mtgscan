import os
import requests
import time
import logging

class OCR:
    def save_box_texts(self, file):
        logging.info(f"Save box_texts to {file}")
        with open(file, "w") as f:
            for box, text in self.box_texts:
                f.write(' '.join(map(str, box)))
                f.write("\n")
                f.write(text)
                f.write("\n")

    def load_box_texts(self, file):
        logging.info(f"Load box_texts to {file}")
        self.box_texts = []
        with open(file, "r") as f:
            while True:
                box = f.readline().rstrip('\n')
                if box == "":
                    return self.box_texts
                text = f.readline().rstrip('\n')
                self.box_texts.append([list(map(int, box.split(" "))), text])
    
    def save_box_texts_img(self, file):
        logging.info(f"Save box_texts image to {file}")
        

class AzureOCR(OCR):
    def __init__(self):
        self.subscription_key = os.environ['AZURE_VISION_KEY']
        self.text_recognition_url = os.environ['AZURE_VISION_ENDPOINT'] + "/vision/v3.1/read/analyze"
        self.box_texts = []

    def img_to_box_texts(self, url_image):
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        data = {'url': url_image}
        logging.info(f"Send image {url_image} to Azure")
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
        self.box_texts = []
        for line in analysis["analyzeResult"]["readResults"][0]["lines"]:
            self.box_texts.append([line["boundingBox"], line["text"]])
        return self.box_texts