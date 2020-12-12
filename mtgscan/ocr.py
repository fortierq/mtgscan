import os
import requests
import time
import logging
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from urllib.parse import urlparse


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

    def save_box_texts_image(self, image_in, image_out):
        if not os.path.isfile(image_out):
            logging.info(f"Save box_texts image to {image_out}")
            img = plt.imread(image_in, image_out)
            fig, ax = plt.subplots(
                figsize=(img.shape[1]//64, img.shape[0]//64))
            ax.imshow(img, aspect='equal')
            for box, text in self.box_texts:
                P = (box[0], box[1])
                Q = (box[2], box[3])
                R = (box[4], box[5])
                S = (box[6], box[7])
                x = [P[0], Q[0], Q[0], R[0], R[0], S[0], S[0], P[0]]
                y = [P[1], Q[1], Q[1], R[1], R[1], S[1], S[1], P[1]]
                line = Line2D(x, y, linewidth=3.5, color='red')
                ax.add_line(line)
                ax.text(P[0], P[1], text, bbox=dict(
                    facecolor='blue', alpha=0.5), fontsize=11, color='white')
            plt.axis('off')
            plt.tight_layout()
            fig.savefig(image_out)


class AzureOCR(OCR):
    def __init__(self):
        self.subscription_key = os.environ['AZURE_VISION_KEY']
        self.text_recognition_url = os.environ['AZURE_VISION_ENDPOINT'] + \
            "/vision/v3.1/read/analyze"
        self.box_texts = []

    def __str__(self):
        return "azure"

    def image_to_box_texts(self, image):
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
        self.box_texts = []
        for line in analysis["analyzeResult"]["readResults"][0]["lines"]:
            self.box_texts.append([line["boundingBox"], line["text"]])
