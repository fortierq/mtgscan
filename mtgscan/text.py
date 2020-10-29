import json
import logging
import re
import os
from symspellpy import SymSpell, Verbosity, editdistance
import mtgscan.deck

class MagicRecognition:

    def __init__(self, file_all_cards_json):
        file_all_cards_txt = os.path.splitext(file_all_cards_json)[0]+".txt"
        if not os.path.isfile(file_all_cards_txt):
            logging.info(f"Save {file_all_cards_txt}")
            with open(file_all_cards_json, "r") as f, open(file_all_cards_txt, "w") as g:
                all_cards_json = json.load(f)
                for card in all_cards_json["data"].keys():
                    i = card.find(" //")
                    if i != -1: 
                        card = card[:i]
                    g.write(card + "$1\n")
    
        self.sym_spell = SymSpell(max_dictionary_edit_distance=6)
        self.sym_spell._distance_algorithm = editdistance.DistanceAlgorithm.LEVENSHTEIN
        self.sym_spell.load_dictionary(file_all_cards_txt, 0, 1, separator="$")
        self.all_cards = self.sym_spell._words
        logging.info(f"Load {file_all_cards_txt}: {len(self.all_cards)} cards")
        self.edit_dist = editdistance.EditDistance(editdistance.DistanceAlgorithm.LEVENSHTEIN)

    def preprocess(self, text):
        return re.sub("[^a-zA-Z',. ]", '', text).rstrip(' ')

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
                cards.append(card)

        deck = mtgscan.deck.Deck()
        sb = max(60, len(cards) - 15)
        deck.add_cards(cards[:sb], in_sideboard=False)
        deck.add_cards(cards[sb:], in_sideboard=True)
        return deck

    def search(self, text):
        if len(text) < 3: 
            return None
        if len(text) > 30: 
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
            text = text.replace('.', '').rstrip(' ')
            sug = self.sym_spell.lookup(text,Verbosity.CLOSEST,
            max_edit_distance=min(6, int(0.3*len(text))))
            if sug != []:
                card = sug[0].term
                ratio = sug[0].distance/len(text)
                if len(text) < len(card) + 5: 
                    logging.info(f"Corrected: {text} {ratio} {card}")
                    return card
                else: 
                    logging.info(f"Not corrected: {text} {ratio} {card}")
            else: 
                logging.info(f"Not found: {text}")
        return None