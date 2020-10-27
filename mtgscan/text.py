import json
import logging
from symspellpy import SymSpell, Verbosity
import mtgscan.deck

class TextRecognition:

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

        self.sym_spell = SymSpell(max_dictionary_edit_distance=5)
        for c in self.all_cards: 
            self.sym_spell.create_dictionary_entry(c, 1)

    def preprocess(self, text):
        rm = " @*()?"
        text = text[:15]
        for c in rm:
            text = text.replace(c, "")
        return text.lower()

    def preprocess_texts(self, texts):
        texts_proc = []
        for text in texts:
            if len(text) < 30:
                texts_proc.append(self.preprocess(text))
            else: 
                logging.info(text)
        return texts_proc

    def ocr_to_deck(self, texts, boxes):
        L = list(zip(boxes, texts))
        L.sort()

        boxes, texts = zip(*L)
        texts_proc = self.preprocess_texts(texts)
        cards = self.texts_to_cards(texts_proc)

        deck = mtgscan.deck.Deck()
        sb = max(60, len(cards) - 15)
        deck.add_cards(cards[:sb], in_sideboard=False)
        deck.add_cards(cards[sb:], in_sideboard=True)
        return deck

    def text_to_card(self, text):
        if len(text) < 3: 
            return None
        if text in self.all_cards:
            return self.all_cards[text]
        else:
            sug = self.sym_spell.lookup(text,Verbosity.CLOSEST,max_edit_distance=5)
            if sug != []:
                card = self.all_cards[sug[0].term]
                ratio = sug[0].distance/len(text)
                if ratio < 0.25 or (card in cards and ratio < 0.4): 
                    logging.info(f"Found: {text} {ratio} {card}")
                    return card
                else: 
                    logging.info(f"Not found: {text} {ratio} {card}")
            else: 
                logging.info(f"Not found: {text}")
        return None
        
    def texts_to_cards(self, texts):
        cards = []
        for text in texts:
            cards.append(self.text_to_card(text))
        return cards
    