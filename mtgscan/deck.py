import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Pile:
    cards: Counter = field(default_factory=Counter)

    def add_card(self, card: str) -> None:
        if card in self.cards:
            self.cards[card] += 1
        else:
            self.cards[card] = 1

    def add_cards(self, cards: Iterable) -> None:
        for c in cards:
            self.add_card(c)

    def diff(self, other) -> int:
        """Return the number of different cards between self and other"""
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

    def __iadd__(self, other):
        self.cards += other.cards
        return self

    def __str__(self):
        return "".join(f"{self.cards[card]} {card}\n" for card in self.cards)

    def __len__(self):
        return sum(self.cards[c] for c in self.cards)

    def __iter__(self):
        yield from self.cards.items()


@dataclass
class Deck:
    maindeck: Pile = field(default_factory=Pile)
    sideboard: Pile = field(default_factory=Pile)

    def __str__(self):
        if len(self.sideboard) == 0:
            return str(self.maindeck)
        return str(self.maindeck) + "\n" + str(self.sideboard)

    def __len__(self):
        return len(self.maindeck) + len(self.sideboard)

    def __iadd__(self, other):
        self.maindeck += other.maindeck
        self.sideboard += other.sideboard
        return self

    def __iter__(self):
        yield from self.maindeck
        yield from self.sideboard

    def add_card(self, card: str, in_sideboard: bool) -> None:
        if in_sideboard:
            self.sideboard.add_card(card)
        else:
            self.maindeck.add_card(card)

    def add_cards(self, cards: Iterable, in_sideboard: bool) -> None:
        for card in cards:
            self.add_card(card, in_sideboard)

    def save(self, file: str) -> None:
        logging.info(f"Saving {file}")
        with open(file, "w") as f:
            f.write(str(self))

    def load(file: str):
        logging.info(f"Loading {file}")
        file = Path(file)
        deck = Deck()
        if not file.exists():
            print(f"Can't load file {file}")
            return deck
        with file.open("r") as f:
            in_sideboard = False
            for line in f:
                if line == "\n":
                    in_sideboard = True
                else:
                    try:
                        i = line.find(' ')
                        n = int(line[:i])
                        card = line[i + 1:].rstrip()
                        deck.add_cards([card] * n, in_sideboard)
                    except (ValueError, IndexError):
                        logging.warning(f"Can't read {line}")
        return deck

    def diff(self, other):
        """Return the number of different cards between self and other"""
        return self.maindeck.diff(other.maindeck) + self.sideboard.diff(other.sideboard)
