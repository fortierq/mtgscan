import json
import logging
import re
from pathlib import Path

import requests
from symspellpy import SymSpell, Verbosity, editdistance

import mtgscan.deck


def load_json(url):
    print(f"Loading {url}")
    r = requests.get(url)
    return r.json()


DIR_DATA = Path("data")
FILE_ALL_CARDS = DIR_DATA / "all_cards.txt"
URL_ALL_CARDS = "https://mtgjson.com/api/v5/VintageAtomic.json"
FILE_KEYWORDS = DIR_DATA / "Keywords.json"
URL_KEYWORDS = "https://mtgjson.com/api/v5/Keywords.json"


class MagicRecognition:

    def __init__(self, max_ratio_diff=0.3, max_ratio_diff_keyword=0.2):
        self.max_ratio_diff = max_ratio_diff
        self.max_ratio_diff_keyword = max_ratio_diff_keyword

        Path.mkdir(DIR_DATA, parents=True, exist_ok=True)

        if not Path(FILE_ALL_CARDS).is_file():
            all_cards_json = load_json(URL_ALL_CARDS)

            with FILE_ALL_CARDS.open("a") as f:
                for card in all_cards_json["data"].keys():
                    i = card.find(" //")
                    if i != -1:
                        card = card[:i]
                    f.write(card + "$1\n")

        self.sym_all_cards = SymSpell(max_dictionary_edit_distance=6)
        self.sym_all_cards._distance_algorithm = editdistance.DistanceAlgorithm.LEVENSHTEIN
        self.sym_all_cards.load_dictionary(FILE_ALL_CARDS, 0, 1, separator="$")
        self.all_cards = self.sym_all_cards._words
        print(f"Loaded {FILE_ALL_CARDS}: {len(self.all_cards)} cards")
        self.edit_dist = editdistance.EditDistance(
            editdistance.DistanceAlgorithm.LEVENSHTEIN)

        if not Path(FILE_KEYWORDS).is_file():
            keywords = load_json(URL_KEYWORDS)
            json.dump(keywords, FILE_KEYWORDS.open("w"))

        def concat_lists(LL):
            res = []
            for L in LL:
                res.extend(L)
            return res
        keywords_json = json.load(FILE_KEYWORDS.open())
        keywords = concat_lists(keywords_json["data"].values())
        keywords.extend(["Display", "Land", "Search", "Profile"])
        self.sym_keywords = SymSpell(max_dictionary_edit_distance=3)
        for k in keywords:
            self.sym_keywords.create_dictionary_entry(k, 1)

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
                for i in [0, 1]:
                    if text[i] in '×xX' and text[1 - i].isnumeric():
                        multipliers[i].append((box, int(text[1 - i])))

            sug = self.sym_keywords.lookup(text, Verbosity.CLOSEST,
                                           max_edit_distance=min(3, int(self.max_ratio_diff_keyword*len(text))))
            if sug != []:
                logging.info(
                    f"Keyword rejected: {text} {sug[0].distance/len(text)} {sug[0].term}")
            else:
                card = self.search(self.preprocess(text))
                if card is not None:
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

        for m in multipliers[0]:  # maindeck
            m_box = m[0]

            def comp(box1, box2):
                if box1[0] > m_box[0] or box1[1] > m_box[1]:
                    return False
                return dist(m_box, box1) < dist(m_box, box2)
            multiplier_to_card(m, comp)

        for m in multipliers[1]:  # sideboard
            m_box = m[0]

            def comp(box1, box2):
                return dist(m_box, box1) < dist(m_box, box2)
            multiplier_to_card(m, comp)

        maindeck, sideboard = mtgscan.deck.Pile(), mtgscan.deck.Pile()
        n_cards = sum(c[1] for c in cards)
        n_added = 0
        last_main_card = max(60, n_cards - 15)
        for card, n in cards:
            def add_cards(deck, p):
                if card in deck.cards:
                    deck.cards[card] += p
                elif p > 0:
                    deck.cards[card] = p
            n_added_main = max(min(n, last_main_card - n_added), 0)
            add_cards(maindeck, n_added_main)
            add_cards(sideboard, n - n_added_main)
            n_added += n
        deck = mtgscan.deck.Deck()
        deck.maindeck = maindeck
        deck.sideboard = sideboard
        return deck

    def search(self, text):
        if len(text) < 3:
            return None
        if len(text) > 30:  # assume card text
            logging.info(f"Too long: {text}")
            return None
        if text in self.all_cards:
            return text
        i = text.find("..")  # search for truncated card name
        if i != -1:
            dist = int(self.max_ratio_diff * i)
            card = None
            for c in self.all_cards:
                d = self.edit_dist.compare(text[:i], c[:i], dist)
                if d != -1 and d < dist:
                    card = c
                    dist = d
            if card is None:
                logging.info(f"Not prefix: {text}")
            else:
                logging.info(f"Found prefix: {text} {dist/i} {card}")
                return card
        else:
            text = text.replace('.', '').rstrip(' ')
            sug = self.sym_all_cards.lookup(text, Verbosity.CLOSEST,
                                            max_edit_distance=min(6, int(self.max_ratio_diff * len(text))))
            if sug != []:
                card = sug[0].term
                ratio = sug[0].distance/len(text)
                if len(text) < len(card) + 7:
                    logging.info(f"Corrected: {text} {ratio} {card}")
                    return card
                else:
                    logging.info(
                        f"Not corrected (too long): {text} {ratio} {card}")
            else:
                logging.info(f"Not found: {text}")
        return None
