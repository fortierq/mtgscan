import json
import logging
import re
from symspellpy import SymSpell, Verbosity, editdistance
import mtgscan.deck

class MagicRecognition:

    def __init__(self, file_all_cards):
        f = open(file_all_cards, "r")
        all_cards_json = json.load(f)
        self.all_cards = dict()
        for c in all_cards_json["data"].keys():
            card = self.preprocess(c)
            i = card.find("//")
            if i != -1: card = card[:i]
            self.all_cards[card] = c
        f.close()
        logging.info(f"Loaded {file_all_cards}: {len(self.all_cards)} cards")

        self.sym_spell = SymSpell(max_dictionary_edit_distance=5)
        self.sym_spell._distance_algorithm = editdistance.DistanceAlgorithm.LEVENSHTEIN
        for c in self.all_cards: 
            self.sym_spell.create_dictionary_entry(c, 1)
        self.edit_dist = editdistance.EditDistance(editdistance.DistanceAlgorithm.LEVENSHTEIN)

    def preprocess(self, text):
        rm = " @*()?"
        for c in rm:
            text = text.replace(c, "")
        text = re.sub('[0-9]+', '', text)
        return text.lower()

    def preprocess_texts(self, box_texts):
        for i in range(len(box_texts)):
            box_texts[i][1] = self.preprocess(box_texts[i][1])

    def ocr_to_deck(self, box_texts):
        box_texts.sort()
        self.preprocess_texts(box_texts)
        boxes, cards = [], []
        for box, text in box_texts:
            card = self.search(text)
            if card != None:
                boxes.append(box)
                cards.append(self.all_cards[card])

        deck = mtgscan.deck.Deck()
        sb = max(60, len(cards) - 15)
        deck.add_cards(cards[:sb], in_sideboard=False)
        deck.add_cards(cards[sb:], in_sideboard=True)
        return deck

    def search(self, text):
        if len(text) < 3: 
            return None
        if len(text) > 25: 
            logging.info(f"Too long: {text}")
            return None
        if text in self.all_cards:
            return text
        i = text.find("..")
        if i != -1:
            dist = int(0.3 * i)
            card = None
            for c in self.all_cards:
                d = self.edit_dist.compare(text[:i], c[:i], dist)
                if d != -1 and d < dist:
                    card = c
                    dist = d
            if card == None:
                logging.info(f"Not prefix: {text}")
            else:
                logging.info(f"Found prefix: {text} {dist/i} {card}")
                return card
        else:
            sug = self.sym_spell.lookup(text,Verbosity.CLOSEST,
            max_edit_distance=min(5, int(0.25*len(text))))
            if sug != []:
                card = sug[0].term
                ratio = sug[0].distance/len(text)
                if len(text) < len(card) + 3: 
                    logging.info(f"Corrected: {text} {ratio} {card}")
                    return card
                else: 
                    logging.info(f"Not corrected: {text} {ratio} {card}")
            else: 
                logging.info(f"Not found: {text}")
        return None