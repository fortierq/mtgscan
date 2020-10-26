
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

class Deck:
    def __init__(self):
        self.maindeck = Pile()
        self.sideboard = Pile()
    
    def add_cards(self, cards, in_sideboard = False):
        if in_sideboard:
            self.sideboard.add_cards(cards)
        else:
            self.maindeck.add_cards(cards)

    def __str__(self):
        return str(self.maindeck) + "\n" + str(self.sideboard)

