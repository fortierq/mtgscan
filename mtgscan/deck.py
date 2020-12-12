import logging

class Pile:
    def __init__(self):
        self.cards = dict()

    def add_card(self, card):
        if card in self.cards:
            self.cards[card] += 1
        else:
            self.cards[card] = 1

    def add_cards(self, cards):
        for c in cards:
            self.add_card(c)

    def diff(self, other):
        res = 0
        for card in self.cards:
            n, p = self.cards[card], 0
            if card in other.cards:
                p = other.cards[card]
            d = n - p
            if d > 0:
                logging.info(f"Diff {card}: {p} instead of {n}")
                res += d
        for card in other.cards:
            n, p = other.cards[card], 0
            if card in self.cards:
                p = self.cards[card]
            d = n - p
            if d > 0:
                logging.info(f"Diff {card}: {n} instead of {p}")
                res += d
        return res

    def __str__(self):
        s = ""
        for card in self.cards:
            s += f"{self.cards[card]} {card}\n"
        return s

    def __len__(self):
        return sum(self.cards[c] for c in self.cards)

class Deck:
    def __init__(self):
        self.maindeck = Pile()
        self.sideboard = Pile()

    def __str__(self):
        if len(self.sideboard) == 0:
            return str(self.maindeck)
        return str(self.maindeck) + "\n" + str(self.sideboard)

    def __len__(self):
        return len(self.maindeck) + len(self.sideboard)

    def add_card(self, card, in_sideboard):
        if in_sideboard:
            self.sideboard.add_card(card)
        else:
            self.maindeck.add_card(card)

    def add_cards(self, cards, in_sideboard):
        for card in cards:
            self.add_card(card, in_sideboard)

    def save(self, file):
        logging.info(f"Saving {file}")
        with open(file, "w") as f:
            f.write(str(self))

    def load(self, file):
        logging.info(f"Loading {file}")
        with open(file, "r") as f:
            in_sideboard = False
            for line in f:
                if line == "\n":
                    in_sideboard = True
                else:
                    try:
                        i = line.find(' ')
                        n = int(line[:i])
                        card = line[i+1:].rstrip()
                        self.add_cards([card]*n, in_sideboard)
                    except (ValueError, IndexError):
                        logging.warning(f"Can't read {line}")

    def diff(self, other):
        return self.maindeck.diff(other.maindeck) + self.sideboard.diff(other.sideboard)
