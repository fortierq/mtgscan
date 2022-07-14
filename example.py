# basic usage of mtgscan
# env variables AZURE_VISION_ENDPOINT and AZURE_VISION_KEY must be set

from mtgscan.text import MagicRecognition
from mtgscan.ocr.azure import Azure

azure = Azure()
rec = MagicRecognition(file_all_cards="all_cards.txt", file_keywords="Keywords.json")
box_texts = azure.image_to_box_texts("https://user-images.githubusercontent.com/49362475/105632710-fa07a180-5e54-11eb-91bb-c4710ef8168f.jpeg")
deck = rec.box_texts_to_deck(box_texts)
for c, k in deck:
    print(c, k)
