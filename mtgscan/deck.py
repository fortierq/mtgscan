
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
        else:
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
        with open(file, "w") as f:
            f.write(str(self))

    def load(self, file):
        with open(file, "r") as f:
            in_sideboard = False
            for line in f:
                if line == "\n": in_sideboard = True
                self.add_card(line, in_sideboard)