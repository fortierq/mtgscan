import base64
from dataclasses import dataclass, field
from io import BytesIO
import logging

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mtgscan.utils


@dataclass
class BoxText:
    box: tuple  # (x, y, ...) with (x, y) the bottom-left vertex
    text: str  # text, presumably a card name
    n: int = 1  # number of occurences of the card

    def __iter__(self):
        yield from (self.box, self.text, self.n)


@dataclass
class BoxTextList:
    box_texts: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.box_texts)

    def __iter__(self):
        yield from self.box_texts

    def __getitem__(self, i) -> BoxText:
        return self.box_texts[i]

    def add(self, box, text, n=1) -> None:
        self.box_texts.append(BoxText(box, text, n))

    def sort(self) -> None:
        """Sort boxes by lexicographic order"""
        self.box_texts.sort(key=lambda box_text: box_text.box)

    def save(self, file):
        """Save box_texts to `file`"""
        logging.info(f"Save box_texts to {file}")
        with open(file, "w") as f:
            for box, text, _ in self.box_texts:
                f.write(' '.join(map(str, box)))
                f.write("\n")
                f.write(text)
                f.write("\n")

    def load(self, file):
        """Load box_texts from `file`"""
        logging.info(f"Load box_texts from {file}")
        self.box_texts = []
        with open(file, "r") as f:
            while True:
                box = f.readline().rstrip('\n')
                if box == "":
                    return self.box_texts
                text = f.readline().rstrip('\n')
                self.add(tuple(map(int, box.split(" "))), text, 1)

    def get_image_base64(self, image_in):
        buffer = BytesIO()
        self._get_image(image_in).savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')

    def save_image(self, image_in, image_out):
        """Add boxes to `image_in` and save it in `image_out`

        Parameters
        ----------
        image_in : str
            Path to original image
        image_out : str
            Path to the image to be saved
        """
        logging.info(f"Save box_texts image to {image_out}")
        self._get_image(image_in).savefig(image_out)

    def _get_image(self, image_in):
        img = mtgscan.utils.load_url_or_file_or_base64(image_in)
        fig, ax = plt.subplots(figsize=(img.shape[1] // 64, img.shape[0] // 64))
        ax.imshow(img, aspect='equal')
        for box, text, n in self.box_texts:
            P = (box[0], box[1])
            Q = (box[2], box[3])
            R = (box[4], box[5])
            S = (box[6], box[7])
            x = [P[0], Q[0], Q[0], R[0], R[0], S[0], S[0], P[0]]
            y = [P[1], Q[1], Q[1], R[1], R[1], S[1], S[1], P[1]]
            line = Line2D(x, y, linewidth=3.5, color='red')
            ax.add_line(line)
            if n != 1:
                text = f"{n}x {text}"
            ax.text(P[0], P[1], text, bbox=dict(facecolor='blue', alpha=0.5), fontsize=13, color='white')
        ax.axis('off')
        fig.tight_layout()
        return fig
