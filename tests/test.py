from datetime import datetime
import logging
from pathlib import Path
import sys

DIR_DATA = Path(__file__).parents[1]
sys.path.insert(0, str(DIR_DATA))
import mtgscan
from mtgscan.box_text import BoxTextList
import mtgscan.deck
from mtgscan.ocr.azure import Azure
import mtgscan.text

FILE_ALL_CARDS = str(DIR_DATA / "all_cards.txt")
FILE_KEYWORDS = str(DIR_DATA / "Keywords.json")

FORMAT = "[%(asctime)s %(filename)s:%(lineno)s:%(funcName)s()] %(message)s"
DIR_SAMPLES = Path(__file__).parent / "samples"
rec = mtgscan.text.MagicRecognition(FILE_ALL_CARDS, FILE_KEYWORDS, max_ratio_diff=0.25)
ocr_all = [Azure()]
errors = {str(ocr): [] for ocr in ocr_all}

for sample in DIR_SAMPLES.iterdir():
    print(f"- Testing {sample}")
    image = None
    for f in sample.iterdir():
        if f.name.endswith("jpg") or f.name.endswith("png"):
            image = f.name
    if image is None:
        print("No image found")
        continue

    for ocr in ocr_all:
        print(f"-- OCR {ocr}")
        ocr_path = sample / str(ocr)
        ocr_path.mkdir(exist_ok=True)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging.INFO,
                            format=FORMAT,
                            datefmt='%I:%M:%S',
                            filename=sample / 'test.log',
                            filemode='w')
        try:
            with open(ocr_path / "errors.txt", "r") as f:
                errors_last = int(f.readlines()[-1].split(' ')[-1])
        except (FileNotFoundError, IndexError):
            errors_last = float("inf")
        box_texts = BoxTextList()
        if not (ocr_path / "box_texts.txt").is_file():
            box_texts = ocr.image_to_box_texts(sample / image)
            box_texts.save(ocr_path / "box_texts.txt")
        else:
            box_texts.load(ocr_path / "box_texts.txt")
        box_texts.save_image(sample / image, ocr_path / f"ocr{Path(image).suffix}")

        box_cards = rec.box_texts_to_cards(box_texts)
        rec._assign_stacked(box_texts, box_cards)
        box_cards.save_image(sample / image, ocr_path / f"cards{Path(image).suffix}")

        deck_ocr = rec.box_texts_to_deck(box_texts)
        deck_ocr.save(ocr_path / "deck.txt")
        print(f"Number of cards found: {len(deck_ocr)}")
        deck = mtgscan.deck.Deck.load(sample / "deck.txt")
        diff = deck.diff(deck_ocr)
        errors[str(ocr)].append(diff / len(deck))
        print(f"Errors: {diff} (last: {errors_last})")
        with open(ocr_path / "errors.txt", "a") as f:
            f.write(f"({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) {diff}\n")

for ocr in ocr_all:
    err = errors[str(ocr)]
    print(f"{ocr} Error rate: {sum(err) / len(err):.2f}")
