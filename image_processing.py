from functools import reduce
from io import BytesIO
from PIL import Image, ImageFile
from ransom_note import FragmentRecord
import pytesseract
import requests

PADDING_TOP_DEFAULT: int = 5
PADDING_BOTTOM_DEFAULT: int = 3
PADDING_LEFT_DEFAULT: int = 2
PADDING_RIGHT_DEFAULT: int = 2

# downloads an image from the scryfall url
# may not work for links from other websites
def download_scryfall_img(url: str) -> ImageFile:
    data = requests.get(url).content
    return Image.open(BytesIO(data))

# finds a word in an image and returns a crop of just that word
# throws an exception if it can't find anything
def find_word_in_image(word: str, img: ImageFile,
                       padding_top=PADDING_TOP_DEFAULT,
                       padding_bottom=PADDING_BOTTOM_DEFAULT,
                       padding_left=PADDING_LEFT_DEFAULT,
                       padding_right=PADDING_RIGHT_DEFAULT) -> ImageFile:
    # get boxes for all of the letters
    boxes = pytesseract.image_to_boxes(img, "eng")
    box_tuples = [line.split() for line in boxes.splitlines()]
    h = img.height

    # find position of word in boxes
    try:
        start_pos = "".join(map(lambda b: b[0], box_tuples)).lower().find(word)
        end_pos = start_pos + len(word) - 1
        left = int(box_tuples[start_pos][1]) - padding_left
        top = h - int(box_tuples[start_pos][4]) - padding_top
        right = int(box_tuples[end_pos][3]) + padding_right
        bottom = h - int(box_tuples[end_pos][2]) + padding_bottom
        return img.crop((left, top, right, bottom))
    except Exception as e:
        raise Exception("Error finding word in image :{}".format(word), e)
    
def add_images_with_wrapping(img: ImageFile,
                             images: list[any],
                             width: int,
                             starting_x: int,
                             starting_y: int,
                             line_height: int,
                             word_spacing: int) -> ImageFile:
    x_pos, y_pos = starting_x, starting_y
    for i in images:
        # wrap if word would go past end of line
        if x_pos + i.width > width:
            y_pos += line_height
            x_pos = starting_x
        img.paste(i, (x_pos, y_pos))
        x_pos += i.width + word_spacing

    return img

# test downloading
if __name__ == '__main__':
    #img: ImageFile = download_scryfall_img("https://cards.scryfall.io/normal/front/d/5/d5bd85da-9aba-46ea-9c10-617bec99a2f5.jpg?1599709788")
    with open("src/2xm-284-ratchet-bomb.jpg", 'rb') as file:
        img: ImageFile = Image.open(file)
        cropped_img = find_word_in_image("rat", img, 4)
        cropped_img.show()