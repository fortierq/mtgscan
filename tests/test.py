import sys
import os
DIR_FILE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(DIR_FILE, '..')))
import mtgscan
import mtgscan.ocr
import mtgscan.text
import mtgscan.deck
import logging 

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s:%(funcName)s()] %(message)s"

ocr_azure = mtgscan.ocr.AzureOCR()
text_rec = mtgscan.text.MagicRecognition("mtgscan/VintageAtomic.json")
errors = []
with os.scandir(os.path.join(DIR_FILE, 'samples')) as samples:
    for sample in samples:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%I:%M:%S',
            filename=os.path.join(sample,'test.log'), filemode='w')
        print(f"Testing {sample}")
        image = os.path.join(sample, "image")
        path_box_texts = os.path.join(sample, "box_texts.txt")
        if not os.path.isfile(path_box_texts):
            ocr_azure.image_to_box_texts(image)
            ocr_azure.save_box_texts(path_box_texts)
        else: 
            ocr_azure.load_box_texts(path_box_texts)
        deck_ocr = text_rec.ocr_to_deck(ocr_azure.box_texts)
        deck_ocr.save(os.path.join(sample, "deck_azure.txt"))
        ocr_azure.save_box_texts_image(image)
        deck = mtgscan.deck.Deck()
        deck.load(os.path.join(sample, "deck.txt"))
        print(f"Erreurs: {deck.diff(deck_ocr)}")
