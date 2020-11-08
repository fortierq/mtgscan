import logging
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parents[1]
DIR_TEST = DIR/'tests'
sys.path.insert(0, str(DIR)) # so that python finds mtgscan

import mtgscan
import mtgscan.deck
import mtgscan.ocr
import mtgscan.text

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s:%(funcName)s()] %(message)s"

ocr_azure = mtgscan.ocr.AzureOCR()
text_rec = mtgscan.text.MagicRecognition()
errors = []

for sample in (DIR_TEST/'samples').iterdir():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%I:%M:%S', filename=sample/'test.log', filemode='w')
    print(f"Testing {sample}")
    image = None
    for f in sample.iterdir():
        if f.name.startswith("image"):
            image = f.name
    if image == None:
        print("No image found")
        continue

    ocr_path = sample/str(ocr_azure)
    ocr_path.mkdir(exist_ok=True)
    try: 
        with open(ocr_path/"errors.txt", "r") as f:
            errors_last = int(f.read())
    except:
        errors_last = float("inf")
    if not (ocr_path/"box_texts.txt").is_file():
        ocr_azure.image_to_box_texts(sample/image)
        ocr_azure.save_box_texts(ocr_path/"box_texts.txt")
    else: 
        ocr_azure.load_box_texts(ocr_path/"box_texts.txt")
    deck_ocr = text_rec.ocr_to_deck(ocr_azure.box_texts)
    deck_ocr.save(ocr_path/"deck.txt")
    ocr_azure.save_box_texts_image(sample/image, ocr_path/image)
    deck = mtgscan.deck.Deck()
    deck.load(sample/"deck.txt")
    print(f"Number of cards found: {len(deck)}")
    diff = deck.diff(deck_ocr)
    print(f"Errors: {diff} (last: {errors_last})")
    with open(ocr_path/"errors.txt", "w") as f:
        f.write(str(diff))