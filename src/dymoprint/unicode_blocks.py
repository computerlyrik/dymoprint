from PIL.Image import Image
from PIL.ImageOps import pad

UH = "▀"
LH = "▄"
FB = "█"
NB = "\xa0"

assert UH == "\N{UPPER HALF BLOCK}"
assert LH == "\N{LOWER HALF BLOCK}"
assert FB == "\N{FULL BLOCK}"
assert NB == "\N{NO-BREAK SPACE}"


dict_unicode = {
    (0, 0): FB,
    (1, 0): LH,
    (0, 1): UH,
    (1, 1): NB,
}

dict_unicode_inverted = {
    (0, 0): NB,
    (255, 0): UH,
    (0, 255): LH,
    (255, 255): FB,
}


def image_to_unicode(im: Image, invert: bool = False) -> str:
    char_for = dict_unicode_inverted if invert else dict_unicode
    width = im.width
    height = im.height + (im.height % 2)
    padded_im = pad(image=im, size=(width, height))
    a = padded_im.load()
    output_rows = []
    for r in range(0, height, 2):
        char_list = [char_for[(a[c, r], a[c, r + 1])] for c in range(width)]
        row = "".join(char_list)
        output_rows.append(row)
    output_str = "\n".join(output_rows)
    return output_str
