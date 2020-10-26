
import json
import logging
from symspellpy import SymSpell, Verbosity
import deck

class TextRecognition:

    def __init__(self, file_all_cards, verbose = False):
        f = open(file_all_cards, "r")
        all_cards_json = json.load(f)
        self.all_cards = dict()
        for c in all_cards_json:
            card = TextRecognition.preprocess(c['name'])
            i = card.find("//")
            if i != -1: card = card[:i]
            self.all_cards[card] = c['name']
        f.close()

        self.sym_spell = SymSpell(max_dictionary_edit_distance=5)
        for c in self.all_cards: 
            self.sym_spell.create_dictionary_entry(c, 1)

        self.verbose = verbose

    @staticmethod
    def preprocess(card):
        rm = " @*()?"
        card = card[:15]
        for c in rm:
            card = card.replace(c, "")
        return card.lower()

    def log(self, msg):
        if self.verbose: 
            logging.info(msg)

    def texts_to_cards(self, texts):
        cards = []
        for text in texts:
            if len(text) < 3: continue
            if text in self.all_cards:
                card = self.all_cards[text]
                cards.append(card)
            else:
                sug = self.sym_spell.lookup(text,Verbosity.CLOSEST,max_edit_distance=5)
                if sug != []:
                    card = self.all_cards[sug[0].term]
                    ratio = sug[0].distance/(len(text))
                    if ratio < 0.25 or card in cards: cards.append(card)
                    else: self.log(f"Not found: {text} {ratio} {card}")
                else: self.log(f"Not found: {text}")
        return cards

    def cards_to_deck(self, cards, has_sideboard = True):
        maindeck, sideboard = deck.Deck(), deck.Deck()
        if has_sideboard:
            maindeck.add_cards(cards[:-15])
            sideboard.add_cards(cards[-15:])
            return maindeck, sideboard
        else:
            maindeck.add_cards(cards)
            return maindeck
    
