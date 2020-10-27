import sys
import os
DIR_FILE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(DIR_FILE, '..')))
import mtgscan
import mtgscan.ocr
import mtgscan.text
import mtgscan.deck
import logging 

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(level=logging.INFO,format=FORMAT)

ocr_azure = mtgscan.ocr.AzureRecognition()
text_rec = mtgscan.text.MagicRecognition("mtgscan/AtomicCards.json")
errors = []

with os.scandir(os.path.join(DIR_FILE, 'samples')) as samples:
    for sample in samples:
        with open(os.path.join(sample, "url_image.txt"), "r") as f_url:
            path_box_texts = os.path.join(sample, "box_texts.txt")
            if not os.path.isfile(path_box_texts):
                box_texts = ocr_azure.img_to_box_texts(f_url.read())
                ocr_azure.save_box_texts(box_texts, path_box_texts)
            else: 
                box_texts = ocr_azure.load_box_texts(path_box_texts)
        deck_ocr = text_rec.ocr_to_deck(box_texts)
        deck_ocr.save(os.path.join(sample, "deck_azure.txt"))
        deck = mtgscan.deck.Deck()
        deck.load(os.path.join(sample, "deck.txt"))
        errors.append(deck.diff(deck_ocr)/len(deck))

logging.info(f"Errors: {errors}")