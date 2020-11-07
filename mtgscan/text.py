import logging
import os
import re

import requests
from symspellpy import SymSpell, Verbosity, editdistance

import mtgscan.deck

class MagicRecognition:

    def __init__(self):
        file_all_cards = "all_cards.txt"
        if not os.path.isfile(file_all_cards):
            file_all_cards_json = "https://mtgjson.com/api/v5/VintageAtomic.json"
            print(f"Loading {file_all_cards_json}")
            r = requests.get(file_all_cards_json)
            with open(file_all_cards, "w") as g:
                all_cards_json = r.json()
                for card in all_cards_json["data"].keys():
                    i = card.find(" //")
                    if i != -1: 
                        card = card[:i]
                    g.write(card + "$1\n")
    
        self.sym_spell = SymSpell(max_dictionary_edit_distance=6)
        self.sym_spell._distance_algorithm = editdistance.DistanceAlgorithm.LEVENSHTEIN
        self.sym_spell.load_dictionary(file_all_cards, 0, 1, separator="$")
        self.all_cards = self.sym_spell._words
        print(f"Loaded {file_all_cards}: {len(self.all_cards)} cards")
        self.edit_dist = editdistance.EditDistance(editdistance.DistanceAlgorithm.LEVENSHTEIN)

    def preprocess(self, text):
        return re.sub("[^a-zA-Z',. ]", '', text).rstrip(' ')

    def preprocess_texts(self, box_texts):
        for i in range(len(box_texts)):
            box_texts[i][1] = self.preprocess(box_texts[i][1])

    def ocr_to_deck(self, box_texts):
        multipliers = [[], []]
        box_texts.sort()
        boxes, cards = [], []
        for box, text in box_texts:
            if len(text) == 2:
                try:
                    for i in [0, 1]:
                        if text[i] in '×xX':  
                            multipliers[i].append((box, int(text[1-i])))
                except: 
                    continue
            card = self.search(self.preprocess(text))
            if card != None:
                boxes.append(box)
                cards.append([card, 1])
        def multiplier_to_card(mult, comp):
            i_min = 0
            for i in range(1, len(cards)):
                if comp(boxes[i], boxes[i_min]):
                    i_min = i
            cards[i_min][1] = m[1]
            logging.info(f"{cards[i_min][0]} assigned to x{m[1]}")
        def dist(p, q):     
                return (p[0] - q[0])**2 + (p[1] - q[1])**2
        for m in multipliers[0]: # maindeck
            m_box = m[0]
            def comp(box1, box2):
                if box1[0] > m_box[0] or box1[1] > m_box[1]:
                    return False
                return dist(m_box, box1) < dist(m_box, box2)
            multiplier_to_card(m, comp)
        for m in multipliers[1]: # sideboard
            m_box = m[0]
            def comp(box1, box2):
                return dist(m_box, box1) < dist(m_box, box2)
            multiplier_to_card(m, comp)
        maindeck, sideboard = mtgscan.deck.Pile(), mtgscan.deck.Pile()
        n_cards = sum(c[1] for c in cards)
        n_added = 0
        current = maindeck
        for card, n in cards:
            n_added += n
            if n_added >= max(60, n_cards - 15):
                current = sideboard
            if card in current.cards: current.cards[card] += n
            else: current.cards[card] = n
        deck = mtgscan.deck.Deck()
        deck.maindeck = maindeck
        deck.sideboard = sideboard 
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
