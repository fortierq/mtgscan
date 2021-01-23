from datetime import datetime
import logging
from mtgscan.box_text import BoxTextList
from pathlib import Path

import mtgscan
import mtgscan.deck
import mtgscan.ocr
import mtgscan.text

DIR_DATA = Path(__file__).parents[1]
FILE_ALL_CARDS = DIR_DATA / "all_cards.txt"
URL_ALL_CARDS = "https://mtgjson.com/api/v5/VintageAtomic.json"
FILE_KEYWORDS = DIR_DATA / "Keywords.json"
URL_KEYWORDS = "https://mtgjson.com/api/v5/Keywords.json"

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s:%(funcName)s()] %(message)s"
DIR_SAMPLES = Path(__file__).parent / "samples"
rec = mtgscan.text.MagicRecognition(FILE_ALL_CARDS, FILE_KEYWORDS, max_ratio_diff=0.25)
ocr_all = [mtgscan.ocr.Azure()]


for sample in DIR_SAMPLES.iterdir():
    print(f"- Testing {sample}")
    image = None
    for f in sample.iterdir():
        if f.name.startswith("image"):
            image = f.name
    if image is None:
        print("No image found")
        continue

    for ocr in ocr_all:
        print(f"-- OCR {ocr}")
        ocr_path = sample/str(ocr)
        ocr_path.mkdir(exist_ok=True)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging.INFO, format=FORMAT,
                            datefmt='%I:%M:%S', filename=sample/'test.log', filemode='w')
        try:
            with open(ocr_path/"errors.txt", "r") as f:
                errors_last = int(f.readlines()[-1].split(' ')[-1])
        except (FileNotFoundError, IndexError):
            errors_last = float("inf")
        box_texts = BoxTextList()
        if not (ocr_path/"box_texts.txt").is_file():
            box_texts = ocr.image_to_box_texts(sample/image)
            box_texts.save(ocr_path/"box_texts.txt")
        else:
            box_texts.load(ocr_path/"box_texts.txt")
        box_texts.save_image(sample/image, ocr_path/f"ocr{Path(image).suffix}")

        box_cards = rec.box_texts_to_cards(box_texts)
        rec._assign_stacked(box_texts, box_cards)
        box_cards.save_image(sample/image, ocr_path/f"cards{Path(image).suffix}")

        deck_ocr = rec.box_texts_to_deck(box_texts)
        deck_ocr.save(ocr_path/"deck.txt")
        deck = mtgscan.deck.Deck()
        deck.load(sample/"deck.txt")
        print(f"Number of cards found: {len(deck)}")
        diff = deck.diff(deck_ocr)
        print(f"Errors: {diff} (last: {errors_last})")
        with open(ocr_path/"errors.txt", "a") as f:
            f.write(f"({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) {diff}\n")
