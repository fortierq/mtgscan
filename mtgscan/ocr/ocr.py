from mtgscan.box_text import BoxTextList


class OCR:
    def image_to_box_texts(self, image: str) -> BoxTextList:
        """Apply OCR on an image containing Magic cards

        Parameters
        ----------
        image : str
            URL or path to an image

        Returns
        -------
        BoxTextList
            Texts and boxes recognized by the OCR
        """
        raise NotImplementedError()
